#!/usr/bin/env python3
"""Replay the persisted ``input_snapshot.json`` series under alternative magnitude
paths and signal scales (2026-09 monthly review, ``docs/engine_review_2026_09_findings.md``).

Read-only, deterministic, no network calls.  Every day is rebuilt from the
persisted snapshot through the unmodified ``compute_snapshot_statistics`` ->
``build_ugh_request_from_snapshot`` -> projection path, the same way
``analyze_estar_lag.py`` does; the unablated row reproduces the persisted
forecast (direction and ``expected_close_change_bp``) bit-for-bit for every
v2.6 day, and the script fails if it does not.

Two axes, each independent of the other:

``magnitude`` -- the e_star -> expected_close_change_bp path only.  Direction
inputs are untouched, so the direction/FLAT decision changes only where the
conviction factor is replaced (modes ``B`` / ``D``):

* ``A`` current v2.6: ``e_star * trailing_mean_abs_close_change_bp *
  (0.5 + 0.5 * conviction)``, then the v2.5 volatility-expansion multiplier.
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
    [--start 2026-04-01] [--end 2026-09-30] [--scales 100 50 33 25]
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


def run(fxdata_dir: str, start: date, end: date, scales: list[int]) -> tuple[list[Row], int]:
    from ugh_quantamental.fx_protocol.market_ugh_builder import (
        build_ugh_request_from_snapshot,
        compute_snapshot_statistics,
    )

    realized = _load_realized(fxdata_dir)
    persisted = _load_persisted(fxdata_dir)
    configs = {v: _variant_config(v) for v in VARIANTS}
    rows: list[Row] = []
    checked = 0
    for day in business_days(start, end):
        day_str = day.isoformat()
        path = find_snapshot_path(fxdata_dir, day)
        if path is None or day_str not in realized:
            continue
        snapshot = load_market_snapshot(path)
        base_stats = compute_snapshot_statistics(snapshot)
        # Production names this trailing_mean_abs_close_change_bp on BaselineContext.
        trailing = float(base_stats["trailing_mean_abs_change_bp"])
        realized_bp = realized[day_str]

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
                if mode == "A":
                    ref = persisted.get((day_str, variant))
                    if ref is not None and ref[2] == "v2.6":
                        checked += 1
                        if ref[0] != direction or abs(ref[1] - bp) > 1e-6:
                            raise RuntimeError(
                                f"replay drifted from the persisted forecast on {day_str} "
                                f"{variant}: {ref[:2]} vs ({direction}, {bp})"
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
    return rows, checked


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
    args = parser.parse_args(argv)

    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    rows, checked = run(args.fxdata_dir, start, end, args.scales)
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
    print(
        f"[OK] {len(rows)} rows; unablated replay checked against {checked} persisted v2.6 forecasts"
    )
    print(f"  outputs: {args.out_dir}")


if __name__ == "__main__":
    main()
