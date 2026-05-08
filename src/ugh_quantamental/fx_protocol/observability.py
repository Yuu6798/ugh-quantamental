"""Observability artifact generators for the FX Daily Protocol.

All public functions derive their data from already-persisted records,
market snapshots, and manifest data.  No engine values are recomputed here.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ugh_quantamental.fx_protocol.csv_utils import (
    append_csv_row,
    write_csv_rows as write_csv_artifact,
)
from ugh_quantamental.fx_protocol.models import is_ugh_kind

# Explicit ``__all__`` so ``append_csv_row`` and ``write_csv_artifact`` (re-exports
# from :mod:`csv_utils`) are recognized as part of this module's public API and
# survive ``from observability import *``. Includes every previously-public name
# so star-imports remain backwards compatible.
__all__ = [
    "PROVIDER_HEALTH_FIELDNAMES",
    "SCOREBOARD_FIELDNAMES",
    "append_csv_row",
    "build_daily_report_md",
    "build_input_snapshot",
    "build_provider_health_row",
    "build_run_summary",
    "build_scoreboard_rows",
    "collect_all_evaluations_from_history",
    "publish_observability_to_layout",
    "write_csv_artifact",
    "write_json_artifact",
    "write_md_artifact",
]

if TYPE_CHECKING:
    from ugh_quantamental.fx_protocol.data_models import FxProtocolMarketSnapshot
    from ugh_quantamental.fx_protocol.models import (
        EvaluationRecord,
        ForecastRecord,
        OutcomeRecord,
    )

# ---------------------------------------------------------------------------
# Scoreboard column definitions
# ---------------------------------------------------------------------------

SCOREBOARD_FIELDNAMES: tuple[str, ...] = (
    "strategy_kind",
    "observation_count",
    "direction_hit_count",
    "direction_hit_rate",
    "range_hit_count",
    "range_hit_rate",
    "state_proxy_hit_count",
    "state_proxy_hit_rate",
    "mean_close_error_bp",
    "median_close_error_bp",
    "mean_magnitude_error_bp",
    "last_updated_utc",
)

PROVIDER_HEALTH_FIELDNAMES: tuple[str, ...] = (
    "as_of_jst",
    "generated_at_utc",
    "provider_name",
    "newest_completed_window_end_jst",
    "snapshot_lag_business_days",
    "used_fallback_adjustment",
    "run_status",
    "notes",
)

# ---------------------------------------------------------------------------
# 1. input_snapshot.json
# ---------------------------------------------------------------------------


def build_input_snapshot(
    snapshot: "FxProtocolMarketSnapshot",
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build the ``input_snapshot.json`` data from a market snapshot.

    Captures the state of market data inputs used for a forecast run.
    No engine values are recomputed.
    """
    windows = snapshot.completed_windows
    prv = snapshot.market_data_provenance
    newest_end = windows[-1].window_end_jst if windows else None

    return {
        "as_of_jst": snapshot.as_of_jst.isoformat(),
        "pair": snapshot.pair.value,
        "current_spot": snapshot.current_spot,
        "provider_name": prv.vendor,
        "market_data_provenance": {
            "vendor": prv.vendor,
            "feed_name": prv.feed_name,
            "price_type": prv.price_type,
            "resolution": prv.resolution,
            "timezone": prv.timezone,
            "retrieved_at_utc": prv.retrieved_at_utc.isoformat(),
        },
        "completed_windows": [
            {
                "window_start_jst": w.window_start_jst.isoformat(),
                "window_end_jst": w.window_end_jst.isoformat(),
                "open_price": w.open_price,
                "high_price": w.high_price,
                "low_price": w.low_price,
                "close_price": w.close_price,
            }
            for w in windows
        ],
        "completed_window_count": len(windows),
        "newest_completed_window_end_jst": newest_end.isoformat() if newest_end else None,
        "generated_at_utc": generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ---------------------------------------------------------------------------
# 2. run_summary.json
# ---------------------------------------------------------------------------


def build_run_summary(
    *,
    as_of_jst: datetime,
    provider_name: str,
    forecast_batch_id: str | None,
    outcome_id: str | None,
    forecast_created: bool,
    outcome_recorded: bool,
    evaluation_count: int,
    forecast_csv_path: str | None,
    outcome_csv_path: str | None,
    evaluation_csv_path: str | None,
    manifest_path: str | None,
    snapshot_lag_business_days: int,
    used_fallback_adjustment: bool,
    run_status: str,
    theory_version: str,
    engine_version: str,
    schema_version: str,
    protocol_version: str,
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build the ``run_summary.json`` data from automation run results.

    Pure data reshaping — no new logic.
    """
    return {
        "as_of_jst": as_of_jst.isoformat(),
        "provider_name": provider_name,
        "versions": {
            "theory_version": theory_version,
            "engine_version": engine_version,
            "schema_version": schema_version,
            "protocol_version": protocol_version,
        },
        "forecast_batch_id": forecast_batch_id,
        "outcome_id": outcome_id,
        "forecast_created": forecast_created,
        "outcome_recorded": outcome_recorded,
        "evaluation_count": evaluation_count,
        "csv_paths": {
            "forecast_csv_path": forecast_csv_path,
            "outcome_csv_path": outcome_csv_path,
            "evaluation_csv_path": evaluation_csv_path,
        },
        "manifest_path": manifest_path,
        "snapshot_lag_business_days": snapshot_lag_business_days,
        "used_fallback_adjustment": used_fallback_adjustment,
        "run_status": run_status,
        "generated_at_utc": generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ---------------------------------------------------------------------------
# 3. daily_report.md
# ---------------------------------------------------------------------------


def _format_direction(direction: str) -> str:
    """Format direction with arrow symbol."""
    arrows = {"up": "UP", "down": "DOWN", "flat": "FLAT"}
    return arrows.get(direction, direction)


def build_daily_report_md(
    *,
    as_of_jst: datetime,
    forecast_batch_id: str | None,
    forecasts: tuple["ForecastRecord", ...],
    outcome: "OutcomeRecord | None",
    evaluations: tuple["EvaluationRecord", ...],
    manifest_data: dict[str, Any] | None,
    generated_at_utc: datetime,
) -> str:
    """Build the ``daily_report.md`` content from forecast/outcome/evaluation data.

    Reconstructed entirely from existing records — no new prediction logic.
    """
    lines: list[str] = []
    date_str = as_of_jst.strftime("%Y-%m-%d")

    # --- Header ---
    lines.append(f"# FX Daily Report — {date_str}")
    lines.append("")
    lines.append(f"Generated: {generated_at_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("")

    # --- Section 1: Run summary ---
    lines.append("## Run Summary")
    lines.append("")
    lines.append(f"- **as_of_jst**: {as_of_jst.isoformat()}")
    lines.append(f"- **forecast_batch_id**: {forecast_batch_id or 'N/A'}")
    lines.append(f"- **forecast count**: {len(forecasts)}")
    lines.append(f"- **outcome recorded**: {'Yes' if outcome else 'No'}")
    lines.append(f"- **evaluation count**: {len(evaluations)}")
    if manifest_data:
        lines.append(f"- **protocol_version**: {manifest_data.get('protocol_version', 'N/A')}")
    lines.append("")

    # --- Section 2: Today's forecasts ---
    lines.append("## Today's Forecasts")
    lines.append("")
    if forecasts:
        lines.append(
            "| Strategy | Direction | Expected Change (bp) | Dominant State |"
        )
        lines.append("|---|---|---|---|")
        for fc in sorted(forecasts, key=lambda r: r.strategy_kind.value):
            state = fc.dominant_state.value if fc.dominant_state else "-"
            lines.append(
                f"| {fc.strategy_kind.value} "
                f"| {_format_direction(fc.forecast_direction.value)} "
                f"| {fc.expected_close_change_bp:+.1f} "
                f"| {state} |"
            )
        lines.append("")
    else:
        lines.append("No forecasts generated in this run.")
        lines.append("")

    # --- Section 3: Previous window outcome ---
    lines.append("## Previous Window Outcome")
    lines.append("")
    if outcome:
        lines.append(
            f"- **Window**: {outcome.window_start_jst.isoformat()} "
            f"→ {outcome.window_end_jst.isoformat()}"
        )
        lines.append(f"- **Direction**: {_format_direction(outcome.realized_direction.value)}")
        lines.append(f"- **Close change**: {outcome.realized_close_change_bp:+.1f} bp")
        lines.append(
            f"- **OHLC**: O={outcome.realized_open:.2f} H={outcome.realized_high:.2f} "
            f"L={outcome.realized_low:.2f} C={outcome.realized_close:.2f}"
        )
        lines.append(f"- **Range**: {outcome.realized_range_price:.2f}")
        if outcome.event_happened:
            tags = ", ".join(t.value for t in outcome.event_tags)
            lines.append(f"- **Events**: {tags}")
        lines.append("")
    else:
        lines.append("No outcome recorded for the previous window.")
        lines.append("")

    # --- Section 4: Evaluation comparison ---
    lines.append("## Evaluation Comparison")
    lines.append("")
    if evaluations:
        lines.append(
            "| Strategy | Dir Hit | Range Hit | Close Err (bp) "
            "| Magnitude Err (bp) | Disconfirmer |"
        )
        lines.append("|---|---|---|---|---|---|")
        for ev in sorted(evaluations, key=lambda r: r.strategy_kind.value):
            range_hit = str(ev.range_hit) if ev.range_hit is not None else "-"
            close_err = f"{ev.close_error_bp:.1f}" if ev.close_error_bp is not None else "-"
            mag_err = (
                f"{ev.magnitude_error_bp:.1f}" if ev.magnitude_error_bp is not None else "-"
            )
            disconf = "Yes" if ev.disconfirmer_explained else "No"
            lines.append(
                f"| {ev.strategy_kind.value} "
                f"| {ev.direction_hit} "
                f"| {range_hit} "
                f"| {close_err} "
                f"| {mag_err} "
                f"| {disconf} |"
            )
        lines.append("")
    else:
        lines.append("No evaluations available.")
        lines.append("")

    # --- Section 5: Mechanical observation notes ---
    lines.append("## Observation Notes")
    lines.append("")
    if evaluations:
        # Pool UGH-class evaluations (legacy + v2 variants); the daily
        # observation note picks the first available one for direction /
        # range / close diagnostics. With v2's 4 variants this favors the
        # canonical batch-order entry (alpha first under the v2 active set).
        ugh_evals = [e for e in evaluations if is_ugh_kind(e.strategy_kind)]
        if ugh_evals:
            ev = ugh_evals[0]
            lines.append(f"- UGH direction hit: **{ev.direction_hit}**")
            if ev.range_hit is not None:
                lines.append(f"- UGH range hit: **{ev.range_hit}**")
            if ev.close_error_bp is not None:
                lines.append(f"- UGH close error: **{ev.close_error_bp:.1f} bp**")
            if ev.disconfirmer_explained:
                hit_rules = ", ".join(ev.disconfirmers_hit) if ev.disconfirmers_hit else "none"
                lines.append(f"- Disconfirmer explained miss (rules: {hit_rules})")
        baseline_hits = [
            e for e in evaluations if e.direction_hit and not is_ugh_kind(e.strategy_kind)
        ]
        lines.append(
            f"- Baseline direction hits: {len(baseline_hits)}/3"
        )
    else:
        lines.append("No observations to report.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. scoreboard.csv
# ---------------------------------------------------------------------------


def build_scoreboard_rows(
    evaluations: tuple["EvaluationRecord", ...],
    generated_at_utc: datetime,
) -> list[dict[str, Any]]:
    """Build scoreboard rows from a collection of evaluation records.

    Aggregates cumulative metrics per strategy from all available evaluations.
    Pure re-aggregation — no new logic.
    """
    from collections import defaultdict

    strategy_evals: dict[str, list["EvaluationRecord"]] = defaultdict(list)
    for ev in evaluations:
        strategy_evals[ev.strategy_kind.value].append(ev)

    rows: list[dict[str, Any]] = []
    ts = generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    for strategy in sorted(strategy_evals.keys()):
        evs = strategy_evals[strategy]
        n = len(evs)
        dir_hits = sum(1 for e in evs if e.direction_hit)

        range_evaluable = [e for e in evs if e.range_hit is not None]
        range_hits = sum(1 for e in range_evaluable if e.range_hit)

        state_evaluable = [e for e in evs if e.state_proxy_hit is not None]
        state_hits = sum(1 for e in state_evaluable if e.state_proxy_hit)

        close_errors = [e.close_error_bp for e in evs if e.close_error_bp is not None]
        mag_errors = [e.magnitude_error_bp for e in evs if e.magnitude_error_bp is not None]

        mean_close = sum(close_errors) / len(close_errors) if close_errors else None
        median_close = _median(close_errors) if close_errors else None
        mean_mag = sum(mag_errors) / len(mag_errors) if mag_errors else None

        rows.append({
            "strategy_kind": strategy,
            "observation_count": n,
            "direction_hit_count": dir_hits,
            "direction_hit_rate": round(dir_hits / n, 4) if n > 0 else "",
            "range_hit_count": range_hits if range_evaluable else "",
            "range_hit_rate": (
                round(range_hits / len(range_evaluable), 4) if range_evaluable else ""
            ),
            "state_proxy_hit_count": state_hits if state_evaluable else "",
            "state_proxy_hit_rate": (
                round(state_hits / len(state_evaluable), 4) if state_evaluable else ""
            ),
            "mean_close_error_bp": round(mean_close, 2) if mean_close is not None else "",
            "median_close_error_bp": round(median_close, 2) if median_close is not None else "",
            "mean_magnitude_error_bp": round(mean_mag, 2) if mean_mag is not None else "",
            "last_updated_utc": ts,
        })

    return rows


def _median(values: list[float]) -> float:
    """Return the median of a non-empty list of floats."""
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2.0
    return s[mid]


# ---------------------------------------------------------------------------
# 5. provider_health.csv
# ---------------------------------------------------------------------------


def build_provider_health_row(
    *,
    as_of_jst: datetime,
    generated_at_utc: datetime,
    provider_name: str,
    newest_completed_window_end_jst: datetime | None,
    snapshot_lag_business_days: int,
    used_fallback_adjustment: bool,
    run_status: str,
    notes: str,
) -> dict[str, Any]:
    """Build a single provider_health.csv row from run metadata.

    Pure data reshaping — no new logic.
    """
    return {
        "as_of_jst": as_of_jst.isoformat(),
        "generated_at_utc": generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider_name": provider_name,
        "newest_completed_window_end_jst": (
            newest_completed_window_end_jst.isoformat()
            if newest_completed_window_end_jst
            else ""
        ),
        "snapshot_lag_business_days": snapshot_lag_business_days,
        "used_fallback_adjustment": used_fallback_adjustment,
        "run_status": run_status,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# File write helpers
# ---------------------------------------------------------------------------


def write_json_artifact(path: str, data: dict[str, Any]) -> str:
    """Write *data* as formatted JSON to *path*.  Returns absolute path."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return os.path.abspath(path)


def write_md_artifact(path: str, content: str) -> str:
    """Write markdown *content* to *path*.  Returns absolute path."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Layout publication for observability artifacts
# ---------------------------------------------------------------------------


def publish_observability_to_layout(
    csv_output_dir: str,
    date_str: str,
    forecast_batch_id: str,
    *,
    input_snapshot_path: str | None = None,
    run_summary_path: str | None = None,
    daily_report_path: str | None = None,
    scoreboard_path: str | None = None,
    provider_health_path: str | None = None,
) -> dict[str, str | None]:
    """Copy observability artifacts into ``latest/`` and ``history/`` layout.

    Follows the same pattern as ``publish_csv_to_layout``: latest/ is always
    overwritten, history/ is immutable per run.  Stale latest/ files for
    artifacts that are ``None`` are **deleted** to prevent serving outdated data.

    Returns a dict of relative paths (or ``None`` for absent artifacts).
    """
    base = os.path.abspath(csv_output_dir)
    latest_dir = os.path.join(base, "latest")
    history_dir = os.path.join(base, "history", date_str, forecast_batch_id)
    os.makedirs(latest_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    result: dict[str, str | None] = {}

    _artifacts: list[tuple[str, str | None, str]] = [
        ("input_snapshot", input_snapshot_path, "input_snapshot.json"),
        ("run_summary", run_summary_path, "run_summary.json"),
        ("daily_report", daily_report_path, "daily_report.md"),
        ("scoreboard", scoreboard_path, "scoreboard.csv"),
        ("provider_health", provider_health_path, "provider_health.csv"),
    ]

    for key, src_path, filename in _artifacts:
        latest_file = os.path.join(latest_dir, filename)
        if src_path is not None:
            shutil.copy2(src_path, latest_file)
            shutil.copy2(src_path, os.path.join(history_dir, filename))
            result[f"latest_{key}"] = f"latest/{filename}"
            result[f"history_{key}"] = (
                f"history/{date_str}/{forecast_batch_id}/{filename}"
            )
        else:
            if os.path.exists(latest_file):
                os.remove(latest_file)
            result[f"latest_{key}"] = None
            result[f"history_{key}"] = None

    return result


def collect_all_evaluations_from_history(
    csv_output_dir: str,
) -> tuple["EvaluationRecord", ...]:
    """Scan history/ directories for evaluation.csv files and parse them back.

    Returns a tuple of ``EvaluationRecord`` objects reconstructed from CSV rows.
    Used by scoreboard generation to aggregate cumulative metrics.

    This function reads CSVs only — no DB dependency.
    """
    base = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(base, "history")
    if not os.path.isdir(history_dir):
        return ()

    records: list["EvaluationRecord"] = []

    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            eval_csv = os.path.join(date_path, batch_dir, "evaluation.csv")
            if not os.path.isfile(eval_csv):
                continue
            with open(eval_csv, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    records.append(_parse_evaluation_row(row))

    return tuple(records)


def _parse_evaluation_row(row: dict[str, str]) -> "EvaluationRecord":
    """Parse a single evaluation CSV row back into an ``EvaluationRecord``."""
    from ugh_quantamental.fx_protocol.models import (
        CurrencyPair,
        EvaluationRecord,
        StrategyKind,
    )

    def _opt_bool(v: str) -> bool | None:
        if v == "":
            return None
        return v.lower() in ("true", "1", "yes")

    def _opt_float(v: str) -> float | None:
        if v == "":
            return None
        return float(v)

    def _opt_str(v: str) -> str | None:
        return v if v != "" else None

    hit_str = row.get("disconfirmers_hit", "")
    disconfirmers_hit = tuple(hit_str.split("|")) if hit_str else ()

    return EvaluationRecord(
        evaluation_id=row["evaluation_id"],
        forecast_id=row["forecast_id"],
        outcome_id=row["outcome_id"],
        pair=CurrencyPair(row["pair"]),
        strategy_kind=StrategyKind(row["strategy_kind"]),
        direction_hit=row["direction_hit"].lower() in ("true", "1", "yes"),
        range_hit=_opt_bool(row.get("range_hit", "")),
        close_error_bp=_opt_float(row.get("close_error_bp", "")),
        magnitude_error_bp=_opt_float(row.get("magnitude_error_bp", "")),
        state_proxy_hit=_opt_bool(row.get("state_proxy_hit", "")),
        mismatch_change_bp=_opt_float(row.get("mismatch_change_bp", "")),
        realized_state_proxy=_opt_str(row.get("realized_state_proxy", "")),
        actual_state_change=_opt_bool(row.get("actual_state_change", "")),
        disconfirmers_hit=disconfirmers_hit,
        disconfirmer_explained=_opt_bool(row.get("disconfirmer_explained", "")),
        evaluated_at_utc=datetime.fromisoformat(row["evaluated_at_utc"]),
        theory_version=row.get("theory_version", "v1"),
        engine_version=row.get("engine_version", "v1"),
        schema_version=row.get("schema_version", "v1"),
        protocol_version=row.get("protocol_version", "v1"),
    )
