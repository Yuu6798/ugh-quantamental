#!/usr/bin/env python3
"""Replay the persisted ``input_snapshot.json`` series under alternative magnitude
paths and signal scales (2026-09 monthly review, ``docs/engine_review_2026_09_findings.md``).

Read-only, deterministic, no network calls.  Every day is rebuilt from the
persisted snapshot through the unmodified ``compute_snapshot_statistics`` ->
``build_ugh_request_from_snapshot`` -> projection path, the same way
``analyze_estar_lag.py`` does; every persisted UGH forecast in the window
(direction and ``expected_close_change_bp``) is reproduced bit-for-bit under
its own ``engine_version``'s expansion ceiling, and the script fails if any
is missing or differs.

Two axes, each independent of the other:

``magnitude`` -- the e_star -> expected_close_change_bp path only.  Direction
inputs are untouched, so the direction/FLAT decision changes only where the
conviction factor is replaced (modes ``B`` / ``D``):

* ``A`` v2.6: ``e_star * trailing_mean_abs_close_change_bp *
  (0.5 + 0.5 * conviction)``, then the v2.5 volatility-expansion multiplier
  with its v2.6 ceiling (``REPLAY_EXPANSION_MAX = 1.8``, pinned so a later
  default change cannot fold A onto C).
* ``B`` conviction decoupled: the factor is the constant 0.75 (the midpoint
  of its ``[0.5, 1.0]`` range); expansion kept.
* ``C`` expansion off: conviction factor kept, multiplier forced to ``1.0``
  (what ``volatility_expansion_max=1.0`` produces).
* ``D`` both.

``scale`` -- the hard-coded ``x100`` in ``derive_signal_features`` /
``derive_question_features`` replaced by ``k``, implemented by scaling the raw
``momentum_5d`` and ``spot_vs_sma20`` statistics by ``k/100`` and rebuilding
the whole request.  This moves every consumer of those statistics (direction
threshold, q_strength, momentum_evidence, technical/fundamental score), so read
it as "the engine measures SMA spreads in units where saturation happens at
100/k %", not as an isolation of one score.

Usage
-----
python scripts/replay_magnitude_counterfactual.py \\
    --fxdata-dir <fx-daily-data checkout>/csv --out-dir <out> \\
    [--start 2026-04-01] [--end 2026-09-30] [--scales 100 50 33 25] \\
    [--expected-validated 164]
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import statistics
import sys
from dataclasses import dataclass
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_estar_lag import (  # noqa: E402
    _replay_projection,
    _variant_config,
    business_days,
    find_snapshot_path,
    load_market_snapshot,
)

VARIANTS = ("ugh_v2_alpha", "ugh_v2_beta", "ugh_v2_gamma", "ugh_v2_delta")
MAGNITUDE_MODES = ("A", "B", "C", "D")
DECOUPLED_CONVICTION_FACTOR = 0.75
#: Mode A is the v2.6 counterfactual and stays pinned to the v2.6 expansion
#: ceiling whatever ``ProjectionConfig`` defaults to later.  Once a
#: production version lowers the default, mode A keeps answering "what would
#: v2.6 have forecast", which is what the monthly rollback check compares
#: against -- it must not silently collapse onto mode C.
REPLAY_EXPANSION_MAX = 1.8
#: ``volatility_expansion_max`` in force for each persisted ``engine_version``;
#: the unablated validation replays a persisted row under its own version's
#: ceiling.  Add an entry when a version changes the ceiling.
EXPANSION_MAX_BY_ENGINE_VERSION = {"v2.6": 1.8, "v2.7": 1.0}


@dataclass(frozen=True)
class Row:
    axis: str
    setting: str
    variant: str
    day: str
    direction: str
    expected_bp: float
    realized_bp: float
    conviction: float
    e_star: float
    technical_score: float
    fundamental_score: float

    @property
    def close_error_bp(self) -> float:
        return abs(self.realized_bp - self.expected_bp)

    @property
    def random_walk_error_bp(self) -> float:
        return abs(self.realized_bp)


def _load_realized(fxdata_dir: str) -> dict[str, float]:
    realized: dict[str, float] = {}
    for path in glob.glob(os.path.join(fxdata_dir, "history", "*", "*", "outcome.csv")):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                realized[row["window_start_jst"][:10]] = float(row["realized_close_change_bp"])
    return realized


def _load_persisted(fxdata_dir: str) -> dict[tuple[str, str], tuple[str, float, str]]:
    persisted: dict[tuple[str, str], tuple[str, float, str]] = {}
    for path in glob.glob(os.path.join(fxdata_dir, "history", "*", "*", "forecast.csv")):
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                persisted[(row["as_of_jst"][:10], row["strategy_kind"])] = (
                    row["forecast_direction"],
                    float(row["expected_close_change_bp"]),
                    row["engine_version"],
                )
    return persisted


def _forecast_bp(req, res, cfg, trailing: float, *, conviction_factor: float, expansion: bool):
    from ugh_quantamental.fx_protocol.forecasting import (
        _direction_from_bp_with_epsilon,
        _volatility_expansion_multiplier,
    )

    pre_expansion = res.e_star * trailing * conviction_factor
    direction, bp = _direction_from_bp_with_epsilon(pre_expansion, trailing, cfg)
    if expansion and direction.value != "flat":
        bp *= _volatility_expansion_multiplier(
            catalyst_strength=req.state.event_features.catalyst_strength,
            urgency=res.urgency,
            fire_probability=req.projection.signal_features.fire_probability,
            config=cfg,
        )
    return direction.value, bp


def run(
    fxdata_dir: str, start: date, end: date, scales: list[int]
) -> tuple[list[Row], int, list[str], list[str], list[str]]:
    from ugh_quantamental.fx_protocol.market_ugh_builder import (
        build_ugh_request_from_snapshot,
        compute_snapshot_statistics,
    )

    realized = _load_realized(fxdata_dir)
    persisted = _load_persisted(fxdata_dir)
    configs = {
        v: _variant_config(v).model_copy(update={"volatility_expansion_max": REPLAY_EXPANSION_MAX})
        for v in VARIANTS
    }
    rows: list[Row] = []
    checked = 0
    # A persisted forecast whose window has no outcome yet (the newest day,
    # evaluated by the next run) is pending, not missing; it is reported but
    # cannot be replayed.  A replayed day, on the other hand, must have a
    # persisted forecast for every variant or the validation is incomplete.
    persisted_days = {day_str for (day_str, _kind) in persisted}
    # engine_version is stamped on every row of a batch, baselines included, so
    # a batch is identified as modelled from all its rows -- a modelled batch
    # that lost every variant row must fail, not pass as a legacy day.
    versions_by_day: dict[str, set[str]] = {}
    for (day_str, _kind), ref in persisted.items():
        versions_by_day.setdefault(day_str, set()).add(ref[2])
    modelled_versions = set(EXPANSION_MAX_BY_ENGINE_VERSION)
    unvalidated: set[str] = set()
    # A business day with no persisted batch at all is invisible to every
    # per-day guard above (nothing to inspect), so it is reported, and the
    # caller can pin the validated count with --expected-validated.
    no_batch_days: list[str] = []
    pending_days = sorted(
        {
            day_str
            for (day_str, variant), ref in persisted.items()
            if variant in VARIANTS
            and start.isoformat() <= day_str <= end.isoformat()
            and day_str not in realized
        }
    )
    for day in business_days(start, end):
        day_str = day.isoformat()
        path = find_snapshot_path(fxdata_dir, day)
        if day_str not in persisted_days:
            no_batch_days.append(day_str)
        if path is None:
            # No snapshot: fine for a day with no persisted batch (holiday) or
            # a pending / unmodelled day, but a modelled persisted forecast with
            # an outcome and no snapshot is a gap in the archive, not a skip.
            if versions_by_day.get(day_str, set()) & modelled_versions and day_str in realized:
                raise RuntimeError(
                    f"{day_str}: a persisted batch of a modelled engine_version has an outcome "
                    "but no input_snapshot.json; the modelled day cannot be replayed"
                )
            continue
        if day_str not in realized:
            continue
        snapshot = load_market_snapshot(path)
        base_stats = compute_snapshot_statistics(snapshot)
        # Production names this trailing_mean_abs_close_change_bp on BaselineContext.
        trailing = float(base_stats["trailing_mean_abs_change_bp"])
        realized_bp = realized[day_str]

        # Decide how this day is validated before replaying it.  A day whose
        # batch carries any variant row of a modelled engine_version must carry
        # all of them, so a checkout that lost one variant row fails instead of
        # quietly lowering the validated count.
        if day_str not in persisted_days:
            raise RuntimeError(
                f"no persisted forecast batch on {day_str}: the checkout is missing forecast "
                "rows for a day it replays"
            )
        day_refs = {v: persisted[(day_str, v)] for v in VARIANTS if (day_str, v) in persisted}
        validate_day = bool(versions_by_day[day_str] & modelled_versions)
        if validate_day:
            covered = {v for v, ref in day_refs.items() if ref[2] in modelled_versions}
            if covered != set(VARIANTS):
                missing = sorted(set(VARIANTS) - covered)
                raise RuntimeError(
                    f"{day_str}: persisted batch has a modelled engine_version but lacks "
                    f"{missing}; refusing to validate a partial day"
                )
        if not validate_day:
            # Pre-variant batch (single ``ugh`` row) or a version whose ceiling
            # this script does not model: replayed, not validated.
            unvalidated.add(day_str)

        # --- magnitude axis (unablated inputs) ---
        req = build_ugh_request_from_snapshot(snapshot, snapshot_ref=path, stats=base_stats)
        for variant in VARIANTS:
            cfg = configs[variant]
            res = _replay_projection(req, cfg, None)
            sf = req.projection.signal_features
            for mode in MAGNITUDE_MODES:
                factor = (
                    DECOUPLED_CONVICTION_FACTOR
                    if mode in ("B", "D")
                    else 0.5 + 0.5 * res.conviction
                )
                direction, bp = _forecast_bp(
                    req, res, cfg, trailing, conviction_factor=factor, expansion=mode in ("A", "B")
                )
                if mode == "A" and validate_day:
                    # Validate under the ceiling the persisted version ran with,
                    # independently of the pinned mode-A counterfactual.
                    ref = day_refs[variant]
                    ref_cfg = cfg.model_copy(
                        update={"volatility_expansion_max": EXPANSION_MAX_BY_ENGINE_VERSION[ref[2]]}
                    )
                    ref_direction, ref_bp = _forecast_bp(
                        req,
                        res,
                        ref_cfg,
                        trailing,
                        conviction_factor=0.5 + 0.5 * res.conviction,
                        expansion=True,
                    )
                    checked += 1
                    if ref[0] != ref_direction or abs(ref[1] - ref_bp) > 1e-6:
                        raise RuntimeError(
                            f"replay drifted from the persisted forecast on {day_str} "
                            f"{variant}: {ref[:2]} vs ({ref_direction}, {ref_bp})"
                        )
                rows.append(
                    Row(
                        "magnitude",
                        mode,
                        variant,
                        day_str,
                        direction,
                        bp,
                        realized_bp,
                        res.conviction,
                        res.e_star,
                        sf.technical_score,
                        sf.fundamental_score,
                    )
                )

        # --- scale axis (current magnitude path) ---
        for k in scales:
            stats = dict(base_stats)
            stats["momentum_5d"] = base_stats["momentum_5d"] * (k / 100.0)
            stats["spot_vs_sma20"] = base_stats["spot_vs_sma20"] * (k / 100.0)
            req_k = build_ugh_request_from_snapshot(snapshot, snapshot_ref=path, stats=stats)
            for variant in VARIANTS:
                cfg = configs[variant]
                res = _replay_projection(req_k, cfg, None)
                sf = req_k.projection.signal_features
                direction, bp = _forecast_bp(
                    req_k,
                    res,
                    cfg,
                    trailing,
                    conviction_factor=0.5 + 0.5 * res.conviction,
                    expansion=True,
                )
                rows.append(
                    Row(
                        "scale",
                        str(k),
                        variant,
                        day_str,
                        direction,
                        bp,
                        realized_bp,
                        res.conviction,
                        res.e_star,
                        sf.technical_score,
                        sf.fundamental_score,
                    )
                )
    if checked == 0:
        raise RuntimeError(
            f"no persisted forecast with a known engine_version ceiling was replayed in "
            f"{start}..{end}; refusing to emit counterfactual outputs without a validation baseline"
        )
    return rows, checked, pending_days, sorted(unvalidated), no_batch_days


def summarize(rows: list[Row]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    keys = sorted({(r.axis, r.setting, r.variant) for r in rows})
    for axis, setting, variant in keys:
        sel = [r for r in rows if (r.axis, r.setting, r.variant) == (axis, setting, variant)]
        non_flat = [r for r in sel if r.direction != "flat"]
        hits = sum(
            1
            for r in non_flat
            if (r.direction == "up") == (r.realized_bp > 0) and r.realized_bp != 0
        )
        high = [r for r in non_flat if r.conviction >= 0.9]
        high_hits = sum(1 for r in high if (r.direction == "up") == (r.realized_bp > 0))
        out.append(
            {
                "axis": axis,
                "setting": setting,
                "variant": variant,
                "n": len(sel),
                "flat_count": len(sel) - len(non_flat),
                "direction_hit_excl_flat": f"{hits}/{len(non_flat)}",
                "mean_close_error_bp": round(statistics.mean(r.close_error_bp for r in sel), 2),
                "median_close_error_bp": round(statistics.median(r.close_error_bp for r in sel), 2),
                "mean_error_delta_vs_random_walk_bp": round(
                    statistics.mean(r.close_error_bp - r.random_walk_error_bp for r in sel), 2
                ),
                "mean_abs_expected_bp_non_flat": round(
                    statistics.mean(abs(r.expected_bp) for r in non_flat), 2
                )
                if non_flat
                else None,
                "high_conviction_hits": f"{high_hits}/{len(high)}",
                "technical_saturated_days": sum(1 for r in sel if abs(r.technical_score) >= 0.999),
                "fundamental_saturated_days": sum(
                    1 for r in sel if abs(r.fundamental_score) >= 0.999
                ),
            }
        )
    return out


def _write_csv(path: str, rows: list[dict[str, object]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: str, title: str, rows: list[dict[str, object]]) -> None:
    cols = list(rows[0])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# {title}\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for row in rows:
            fh.write(
                "| " + " | ".join("" if row[c] is None else str(row[c]) for c in cols) + " |\n"
            )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fxdata-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--start", default="2026-04-01")
    parser.add_argument("--end", default="2026-09-30")
    parser.add_argument("--scales", nargs="+", type=int, default=[100, 50, 33, 25])
    parser.add_argument(
        "--expected-validated",
        type=int,
        default=None,
        help=(
            "Exact number of persisted forecasts the replay must validate; the run fails on "
            "any other count. An archive that lost a whole day (forecast.csv and snapshot) "
            "leaves nothing for the per-day guards to inspect, so pin the count when the "
            "output is used as promotion evidence (2026-04-01..2026-09-30: 164)."
        ),
    )
    args = parser.parse_args(argv)

    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    rows, checked, pending_days, unvalidated, no_batch_days = run(
        args.fxdata_dir, start, end, args.scales
    )
    if args.expected_validated is not None and checked != args.expected_validated:
        raise SystemExit(
            f"[ERROR] validated {checked} persisted forecasts, expected "
            f"{args.expected_validated}; business days with no persisted batch: "
            f"{', '.join(no_batch_days) or 'none'}"
        )
    os.makedirs(args.out_dir, exist_ok=True)

    daily = [
        {
            "axis": r.axis,
            "setting": r.setting,
            "variant": r.variant,
            "date": r.day,
            "direction": r.direction,
            "expected_bp": r.expected_bp,
            "realized_bp": r.realized_bp,
            "close_error_bp": r.close_error_bp,
            "conviction": r.conviction,
            "e_star": r.e_star,
            "technical_score": r.technical_score,
            "fundamental_score": r.fundamental_score,
        }
        for r in rows
    ]
    _write_csv(os.path.join(args.out_dir, "daily_rows.csv"), daily)

    windows = {
        "all": rows,
        "pre_aug": [r for r in rows if r.day < "2026-08-01"],
        "aug_sep": [r for r in rows if r.day >= "2026-08-01"],
    }
    for name, sel in windows.items():
        if not sel:
            continue
        summary = summarize(sel)
        _write_csv(os.path.join(args.out_dir, f"summary_{name}.csv"), summary)
        _write_markdown(
            os.path.join(args.out_dir, f"summary_{name}.md"),
            f"Magnitude / scale counterfactual summary ({name}: {start}..{end})",
            summary,
        )
    print(f"[OK] {len(rows)} rows; replay validated against {checked} persisted forecasts")
    if no_batch_days:
        print(
            f"  business days with no persisted batch (holiday or lost day, not replayed): "
            f"{', '.join(no_batch_days)}"
        )
    if pending_days:
        print(f"  pending (no outcome yet, not replayed): {', '.join(pending_days)}")
    if unvalidated:
        print(
            f"  replayed but not validated ({len(unvalidated)} days without a persisted variant "
            f"row of a modelled engine_version): {unvalidated[0]}..{unvalidated[-1]}"
        )
    print(f"  outputs: {args.out_dir}")


if __name__ == "__main__":
    main()
