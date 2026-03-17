"""Deterministic CSV export helpers for the FX Daily Protocol v1.

All public functions derive their data from already-persisted ``ForecastRecord``,
``OutcomeRecord``, and ``EvaluationRecord`` instances.  No engine values are
recomputed here.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ugh_quantamental.fx_protocol.models import (
        EvaluationRecord,
        ForecastRecord,
        OutcomeRecord,
    )

# ---------------------------------------------------------------------------
# Canonical column definitions
# ---------------------------------------------------------------------------

FORECAST_FIELDNAMES: tuple[str, ...] = (
    "forecast_id",
    "forecast_batch_id",
    "pair",
    "strategy_kind",
    "as_of_jst",
    "window_end_jst",
    "forecast_direction",
    "expected_close_change_bp",
    "expected_range_low",
    "expected_range_high",
    "primary_question",
    "dominant_state",
    "prob_dormant",
    "prob_setup",
    "prob_fire",
    "prob_expansion",
    "prob_exhaustion",
    "prob_failure",
    "q_dir",
    "q_strength",
    "s_q",
    "temporal_score",
    "grv_raw",
    "grv_lock",
    "alignment",
    "e_star",
    "mismatch_px",
    "mismatch_sem",
    "conviction",
    "urgency",
    "disconfirmer_rule_count",
    "theory_version",
    "engine_version",
    "schema_version",
    "protocol_version",
    "market_data_vendor",
    "market_data_feed_name",
    "market_data_price_type",
    "market_data_resolution",
    "market_data_timezone",
)

OUTCOME_FIELDNAMES: tuple[str, ...] = (
    "outcome_id",
    "pair",
    "window_start_jst",
    "window_end_jst",
    "realized_open",
    "realized_high",
    "realized_low",
    "realized_close",
    "realized_direction",
    "realized_close_change_bp",
    "realized_range_price",
    "event_happened",
    "event_tags",
    "schema_version",
    "protocol_version",
    "market_data_vendor",
    "market_data_feed_name",
    "market_data_price_type",
    "market_data_resolution",
    "market_data_timezone",
)

EVALUATION_FIELDNAMES: tuple[str, ...] = (
    "evaluation_id",
    "forecast_id",
    "outcome_id",
    "pair",
    "strategy_kind",
    "direction_hit",
    "range_hit",
    "close_error_bp",
    "magnitude_error_bp",
    "state_proxy_hit",
    "mismatch_change_bp",
    "realized_state_proxy",
    "actual_state_change",
    "disconfirmers_hit",
    "disconfirmer_explained",
    "evaluated_at_utc",
    "theory_version",
    "engine_version",
    "schema_version",
    "protocol_version",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _blank(v: object) -> object:
    """Return *v* unchanged, or empty string if *v* is ``None``."""
    return "" if v is None else v


def _pipe_join(items: tuple[object, ...]) -> str:
    """Serialize a tuple as a ``|``-joined string; empty tuple → blank."""
    if not items:
        return ""
    return "|".join(str(i) for i in items)


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------


def make_daily_csv_stem(pair: str, as_of_jst: datetime) -> str:
    """Return the ``{PAIR}_{YYYYMMDD}`` stem used in all daily CSV filenames.

    ``as_of_jst`` may be timezone-aware or naive; only the calendar date is used.

    >>> make_daily_csv_stem("USDJPY", datetime(2026, 3, 16, 8, 0, 0))
    'USDJPY_20260316'
    """
    date_str = as_of_jst.strftime("%Y%m%d")
    return f"{pair}_{date_str}"


# ---------------------------------------------------------------------------
# Row-flattening helpers
# ---------------------------------------------------------------------------


def forecast_records_to_rows(
    forecasts: tuple[ForecastRecord, ...],
) -> list[dict[str, object]]:
    """Flatten a tuple of ``ForecastRecord`` objects to CSV-ready row dicts.

    Nested structures are flattened:

    - ``expected_range`` → ``expected_range_low`` / ``expected_range_high``
    - ``state_probabilities`` → ``prob_dormant`` … ``prob_failure``
    - ``market_data_provenance`` → ``market_data_*`` columns
    - ``disconfirmers`` → ``disconfirmer_rule_count``

    Rows are ordered by ``forecast_id`` ascending for deterministic output.
    """
    rows: list[dict[str, object]] = []
    for fc in sorted(forecasts, key=lambda r: r.forecast_id):
        prv = fc.market_data_provenance
        sp = fc.state_probabilities
        er = fc.expected_range
        row: dict[str, object] = {
            "forecast_id": fc.forecast_id,
            "forecast_batch_id": fc.forecast_batch_id,
            "pair": fc.pair.value,
            "strategy_kind": fc.strategy_kind.value,
            "as_of_jst": fc.as_of_jst.isoformat(),
            "window_end_jst": fc.window_end_jst.isoformat(),
            "forecast_direction": fc.forecast_direction.value,
            "expected_close_change_bp": fc.expected_close_change_bp,
            "expected_range_low": er.low_price if er is not None else "",
            "expected_range_high": er.high_price if er is not None else "",
            "primary_question": _blank(fc.primary_question),
            "dominant_state": fc.dominant_state.value if fc.dominant_state is not None else "",
            "prob_dormant": sp.dormant if sp is not None else "",
            "prob_setup": sp.setup if sp is not None else "",
            "prob_fire": sp.fire if sp is not None else "",
            "prob_expansion": sp.expansion if sp is not None else "",
            "prob_exhaustion": sp.exhaustion if sp is not None else "",
            "prob_failure": sp.failure if sp is not None else "",
            "q_dir": fc.q_dir.value if fc.q_dir is not None else "",
            "q_strength": _blank(fc.q_strength),
            "s_q": _blank(fc.s_q),
            "temporal_score": _blank(fc.temporal_score),
            "grv_raw": _blank(fc.grv_raw),
            "grv_lock": _blank(fc.grv_lock),
            "alignment": _blank(fc.alignment),
            "e_star": _blank(fc.e_star),
            "mismatch_px": _blank(fc.mismatch_px),
            "mismatch_sem": _blank(fc.mismatch_sem),
            "conviction": _blank(fc.conviction),
            "urgency": _blank(fc.urgency),
            "disconfirmer_rule_count": len(fc.disconfirmers),
            "theory_version": fc.theory_version,
            "engine_version": fc.engine_version,
            "schema_version": fc.schema_version,
            "protocol_version": fc.protocol_version,
            "market_data_vendor": prv.vendor,
            "market_data_feed_name": prv.feed_name,
            "market_data_price_type": prv.price_type,
            "market_data_resolution": prv.resolution,
            "market_data_timezone": prv.timezone,
        }
        rows.append(row)
    return rows


def outcome_record_to_rows(outcome: OutcomeRecord) -> list[dict[str, object]]:
    """Flatten one ``OutcomeRecord`` to a single-element list of CSV-ready row dicts.

    ``event_tags`` is serialized as a ``|``-joined string of tag values.
    """
    prv = outcome.market_data_provenance
    row: dict[str, object] = {
        "outcome_id": outcome.outcome_id,
        "pair": outcome.pair.value,
        "window_start_jst": outcome.window_start_jst.isoformat(),
        "window_end_jst": outcome.window_end_jst.isoformat(),
        "realized_open": outcome.realized_open,
        "realized_high": outcome.realized_high,
        "realized_low": outcome.realized_low,
        "realized_close": outcome.realized_close,
        "realized_direction": outcome.realized_direction.value,
        "realized_close_change_bp": outcome.realized_close_change_bp,
        "realized_range_price": outcome.realized_range_price,
        "event_happened": outcome.event_happened,
        "event_tags": _pipe_join(tuple(t.value for t in outcome.event_tags)),
        "schema_version": outcome.schema_version,
        "protocol_version": outcome.protocol_version,
        "market_data_vendor": prv.vendor,
        "market_data_feed_name": prv.feed_name,
        "market_data_price_type": prv.price_type,
        "market_data_resolution": prv.resolution,
        "market_data_timezone": prv.timezone,
    }
    return [row]


def evaluation_records_to_rows(
    evaluations: tuple[EvaluationRecord, ...],
) -> list[dict[str, object]]:
    """Flatten a tuple of ``EvaluationRecord`` objects to CSV-ready row dicts.

    ``disconfirmers_hit`` is serialized as a ``|``-joined string of rule IDs.
    Rows are ordered by ``evaluation_id`` ascending for deterministic output.
    """
    rows: list[dict[str, object]] = []
    for ev in sorted(evaluations, key=lambda r: r.evaluation_id):
        row: dict[str, object] = {
            "evaluation_id": ev.evaluation_id,
            "forecast_id": ev.forecast_id,
            "outcome_id": ev.outcome_id,
            "pair": ev.pair.value,
            "strategy_kind": ev.strategy_kind.value,
            "direction_hit": ev.direction_hit,
            "range_hit": _blank(ev.range_hit),
            "close_error_bp": _blank(ev.close_error_bp),
            "magnitude_error_bp": _blank(ev.magnitude_error_bp),
            "state_proxy_hit": _blank(ev.state_proxy_hit),
            "mismatch_change_bp": _blank(ev.mismatch_change_bp),
            "realized_state_proxy": _blank(ev.realized_state_proxy),
            "actual_state_change": _blank(ev.actual_state_change),
            "disconfirmers_hit": _pipe_join(ev.disconfirmers_hit),
            "disconfirmer_explained": _blank(ev.disconfirmer_explained),
            "evaluated_at_utc": ev.evaluated_at_utc.isoformat(),
            "theory_version": ev.theory_version,
            "engine_version": ev.engine_version,
            "schema_version": ev.schema_version,
            "protocol_version": ev.protocol_version,
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# CSV write primitive
# ---------------------------------------------------------------------------


def write_csv_rows(
    path: str,
    rows: list[dict[str, object]],
    fieldnames: tuple[str, ...],
) -> str:
    """Write *rows* to *path* as a CSV file with the given *fieldnames* column order.

    Parent directories are created if they do not exist.  If the file already
    exists it is overwritten (idempotent rerun policy).

    Returns the absolute path of the written file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# High-level export functions
# ---------------------------------------------------------------------------


def export_daily_forecast_csv(
    forecasts: tuple[ForecastRecord, ...],
    as_of_jst: datetime,
    pair: str,
    csv_output_dir: str,
) -> str:
    """Write the daily forecast CSV and return its absolute path.

    File path: ``{csv_output_dir}/forecasts/{pair}_{YYYYMMDD}_forecast.csv``
    """
    stem = make_daily_csv_stem(pair, as_of_jst)
    path = os.path.join(csv_output_dir, "forecasts", f"{stem}_forecast.csv")
    rows = forecast_records_to_rows(forecasts)
    return write_csv_rows(path, rows, FORECAST_FIELDNAMES)


def export_daily_outcome_csv(
    outcome: OutcomeRecord | None,
    as_of_jst: datetime,
    pair: str,
    csv_output_dir: str,
) -> str | None:
    """Write the daily outcome CSV and return its absolute path, or ``None`` if absent.

    File path: ``{csv_output_dir}/outcomes/{pair}_{YYYYMMDD}_outcome.csv``
    """
    if outcome is None:
        return None
    stem = make_daily_csv_stem(pair, as_of_jst)
    path = os.path.join(csv_output_dir, "outcomes", f"{stem}_outcome.csv")
    rows = outcome_record_to_rows(outcome)
    return write_csv_rows(path, rows, OUTCOME_FIELDNAMES)


def export_daily_evaluation_csv(
    evaluations: tuple[EvaluationRecord, ...] | None,
    as_of_jst: datetime,
    pair: str,
    csv_output_dir: str,
) -> str | None:
    """Write the daily evaluation CSV and return its absolute path, or ``None`` if absent.

    File path: ``{csv_output_dir}/evaluations/{pair}_{YYYYMMDD}_evaluation.csv``
    """
    if not evaluations:
        return None
    stem = make_daily_csv_stem(pair, as_of_jst)
    path = os.path.join(csv_output_dir, "evaluations", f"{stem}_evaluation.csv")
    rows = evaluation_records_to_rows(evaluations)
    return write_csv_rows(path, rows, EVALUATION_FIELDNAMES)


# ---------------------------------------------------------------------------
# Layout publication and manifest helpers
# ---------------------------------------------------------------------------


def publish_csv_to_layout(
    csv_output_dir: str,
    date_str: str,
    forecast_batch_id: str,
    forecast_path: str,
    outcome_path: str | None,
    evaluation_path: str | None,
) -> dict[str, str | None]:
    """Copy CSV files into the ``latest/`` and ``history/`` canonical layout.

    Layout written:

    - ``latest/forecast.csv`` — always; overwritten on each run.
    - ``latest/outcome.csv`` — written when *outcome_path* is not ``None``;
      **deleted** from ``latest/`` when ``None`` so stale files are not served.
    - ``latest/evaluation.csv`` — same policy as outcome.
    - ``history/{date_str}/{forecast_batch_id}/forecast.csv`` — immutable archive.
    - ``history/{date_str}/{forecast_batch_id}/outcome.csv`` — when present.
    - ``history/{date_str}/{forecast_batch_id}/evaluation.csv`` — when present.

    The ``history/`` sub-tree uses *forecast_batch_id* as a run-scoped directory.
    Because the batch ID is deterministic for a given ``(pair, as_of_jst,
    protocol_version)`` triple, same-day reruns land in the same history directory
    and overwrite it — this is the intended idempotency behaviour.

    Returns a ``dict`` whose values are paths **relative to** *csv_output_dir*,
    or ``None`` for absent optional files.
    """
    base = os.path.abspath(csv_output_dir)
    latest_dir = os.path.join(base, "latest")
    history_dir = os.path.join(base, "history", date_str, forecast_batch_id)
    os.makedirs(latest_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    # forecast — always present
    shutil.copy2(forecast_path, os.path.join(latest_dir, "forecast.csv"))
    shutil.copy2(forecast_path, os.path.join(history_dir, "forecast.csv"))

    result: dict[str, str | None] = {
        "latest_forecast": "latest/forecast.csv",
        "history_forecast": f"history/{date_str}/{forecast_batch_id}/forecast.csv",
        "latest_outcome": None,
        "history_outcome": None,
        "latest_evaluation": None,
        "history_evaluation": None,
    }

    # outcome — write or delete stale
    latest_outcome = os.path.join(latest_dir, "outcome.csv")
    if outcome_path is not None:
        shutil.copy2(outcome_path, latest_outcome)
        shutil.copy2(outcome_path, os.path.join(history_dir, "outcome.csv"))
        result["latest_outcome"] = "latest/outcome.csv"
        result["history_outcome"] = f"history/{date_str}/{forecast_batch_id}/outcome.csv"
    elif os.path.exists(latest_outcome):
        os.remove(latest_outcome)

    # evaluation — write or delete stale
    latest_evaluation = os.path.join(latest_dir, "evaluation.csv")
    if evaluation_path is not None:
        shutil.copy2(evaluation_path, latest_evaluation)
        shutil.copy2(evaluation_path, os.path.join(history_dir, "evaluation.csv"))
        result["latest_evaluation"] = "latest/evaluation.csv"
        result["history_evaluation"] = f"history/{date_str}/{forecast_batch_id}/evaluation.csv"
    elif os.path.exists(latest_evaluation):
        os.remove(latest_evaluation)

    return result


def write_latest_manifest(csv_output_dir: str, manifest_data: dict[str, object]) -> str:
    """Write *manifest_data* as formatted JSON to ``{csv_output_dir}/latest/manifest.json``.

    The manifest is overwritten on each run (idempotent).  Path values inside
    *manifest_data* should be relative to *csv_output_dir* for portability.

    Returns the absolute path of the written file.
    """
    latest_dir = os.path.join(os.path.abspath(csv_output_dir), "latest")
    os.makedirs(latest_dir, exist_ok=True)
    path = os.path.join(latest_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest_data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path
