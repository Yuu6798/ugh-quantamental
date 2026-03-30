"""FX Annotation & Analytics layer for the FX Daily Protocol.

Adds AI draft annotations, manual annotation support, and slice-based
analytics on top of the existing forecast/outcome/evaluation pipeline.

This module is a pure post-processing layer:
- No engine logic is changed.
- No existing CSV/manifest contracts are modified.
- All outputs are derived from existing history CSVs and annotation files.
- Failures in this layer never break the daily run.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import csv
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone
from statistics import median
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

AI_ANNOTATION_FIELDNAMES: tuple[str, ...] = (
    "as_of_jst",
    "ai_regime_label",
    "ai_event_tags",
    "ai_volatility_label",
    "ai_intervention_risk",
    "ai_notes",
    "generated_at_utc",
)

MANUAL_ANNOTATION_FIELDNAMES: tuple[str, ...] = (
    "as_of_jst",
    "regime_label",
    "event_tags",
    "volatility_label",
    "intervention_risk",
    "notes",
    "annotation_status",
)

LABELED_OBSERVATION_FIELDNAMES: tuple[str, ...] = (
    "as_of_jst",
    "forecast_batch_id",
    "outcome_id",
    "strategy_kind",
    "forecast_direction",
    "expected_close_change_bp",
    "realized_direction",
    "realized_close_change_bp",
    "direction_hit",
    "range_hit",
    "state_proxy_hit",
    "close_error_bp",
    "magnitude_error_bp",
    "regime_label",
    "event_tags",
    "volatility_label",
    "intervention_risk",
    "annotation_status",
)

SLICE_SCOREBOARD_FIELDNAMES: tuple[str, ...] = (
    "strategy_kind",
    "regime_label",
    "volatility_label",
    "intervention_risk",
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

TAG_SCOREBOARD_FIELDNAMES: tuple[str, ...] = (
    "strategy_kind",
    "event_tag",
    "observation_count",
    "direction_hit_rate",
    "range_hit_rate",
    "state_proxy_hit_rate",
    "mean_close_error_bp",
    "mean_magnitude_error_bp",
    "last_updated_utc",
)


# ---------------------------------------------------------------------------
# 1. AI draft annotation generation
# ---------------------------------------------------------------------------


def generate_ai_annotations(
    csv_output_dir: str,
    as_of_jst: datetime,
    generated_at_utc: datetime,
) -> str | None:
    """Generate AI draft annotation suggestions from history data.

    Reads the most recent forecast and evaluation CSVs to produce a simple
    heuristic-based draft.  This is a *supplement* — never used as ground truth.

    Returns the absolute path to the written file, or ``None`` on failure.
    """
    try:
        row = _build_ai_annotation_row(csv_output_dir, as_of_jst, generated_at_utc)
        out_dir = os.path.join(os.path.abspath(csv_output_dir), "annotations")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "ai_annotation_suggestions.csv")
        rows = _load_existing_ai_annotations(path)
        # Replace or append for this as_of_jst
        as_of_str = as_of_jst.isoformat()
        rows = [r for r in rows if r.get("as_of_jst") != as_of_str]
        rows.append(row)
        rows.sort(key=lambda r: r.get("as_of_jst", ""))
        _write_csv(path, rows, AI_ANNOTATION_FIELDNAMES)
        return os.path.abspath(path)
    except Exception:
        logger.warning("AI annotation generation failed (non-fatal).", exc_info=True)
        return None


def _build_ai_annotation_row(
    csv_output_dir: str,
    as_of_jst: datetime,
    generated_at_utc: datetime,
) -> dict[str, str]:
    """Build a single AI annotation row using heuristic rules on history data.

    Heuristics (purely supplementary, never authoritative):
    - regime_label: derived from recent evaluation direction hit rates
    - event_tags: collected from recent outcome event_tags
    - volatility_label: derived from recent close_error_bp magnitudes
    - intervention_risk: simple heuristic based on magnitude of recent moves
    """
    base = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(base, "history")

    regime_label = "unknown"
    event_tags = ""
    volatility_label = "normal"
    intervention_risk = "low"
    notes = "auto-generated draft"

    # Scan recent evaluations and outcomes for heuristic signals
    eval_rows = _collect_recent_eval_rows(history_dir, limit=5)
    outcome_rows = _collect_recent_outcome_rows(history_dir, limit=5)

    if eval_rows:
        ugh_evals = [r for r in eval_rows if r.get("strategy_kind") == "ugh"]
        if ugh_evals:
            hit_count = sum(
                1 for r in ugh_evals
                if r.get("direction_hit", "").lower() in ("true", "1", "yes")
            )
            hit_rate = hit_count / len(ugh_evals)
            if hit_rate >= 0.8:
                regime_label = "trending"
            elif hit_rate <= 0.2:
                regime_label = "choppy"
            else:
                regime_label = "mixed"

        close_errors = []
        for r in eval_rows:
            try:
                v = float(r.get("close_error_bp", ""))
                close_errors.append(v)
            except (ValueError, TypeError):
                pass
        if close_errors:
            avg_err = sum(close_errors) / len(close_errors)
            if avg_err > 50:
                volatility_label = "high"
            elif avg_err > 20:
                volatility_label = "normal"
            else:
                volatility_label = "low"

    if outcome_rows:
        all_tags: list[str] = []
        for r in outcome_rows:
            tags_str = r.get("event_tags", "")
            if tags_str:
                all_tags.extend(tags_str.split("|"))
        if all_tags:
            event_tags = "|".join(sorted(set(all_tags)))

        # Intervention risk heuristic: large recent moves
        recent_changes: list[float] = []
        for r in outcome_rows:
            try:
                v = abs(float(r.get("realized_close_change_bp", "")))
                recent_changes.append(v)
            except (ValueError, TypeError):
                pass
        if recent_changes:
            max_change = max(recent_changes)
            if max_change > 100:
                intervention_risk = "high"
            elif max_change > 50:
                intervention_risk = "medium"
            else:
                intervention_risk = "low"

    return {
        "as_of_jst": as_of_jst.isoformat(),
        "ai_regime_label": regime_label,
        "ai_event_tags": event_tags,
        "ai_volatility_label": volatility_label,
        "ai_intervention_risk": intervention_risk,
        "ai_notes": notes,
        "generated_at_utc": generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _collect_recent_eval_rows(
    history_dir: str, limit: int = 5
) -> list[dict[str, str]]:
    """Collect the most recent evaluation CSV rows from history."""
    if not os.path.isdir(history_dir):
        return []
    rows: list[dict[str, str]] = []
    for date_dir in sorted(os.listdir(history_dir), reverse=True):
        if len(rows) >= limit * 4:  # 4 strategies per date
            break
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            eval_csv = os.path.join(date_path, batch_dir, "evaluation.csv")
            if not os.path.isfile(eval_csv):
                continue
            with open(eval_csv, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows.extend(reader)
    return rows[:limit * 4]


def _collect_recent_outcome_rows(
    history_dir: str, limit: int = 5
) -> list[dict[str, str]]:
    """Collect the most recent outcome CSV rows from history."""
    if not os.path.isdir(history_dir):
        return []
    rows: list[dict[str, str]] = []
    for date_dir in sorted(os.listdir(history_dir), reverse=True):
        if len(rows) >= limit:
            break
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            outcome_csv = os.path.join(date_path, batch_dir, "outcome.csv")
            if not os.path.isfile(outcome_csv):
                continue
            with open(outcome_csv, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows.extend(reader)
    return rows[:limit]


def _load_existing_ai_annotations(path: str) -> list[dict[str, str]]:
    """Load existing AI annotation rows, or return empty list."""
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# 2. Manual annotation template generation
# ---------------------------------------------------------------------------


def generate_manual_annotation_template(csv_output_dir: str) -> str:
    """Generate ``manual_annotations.template.csv`` with column headers and a sample row.

    Returns the absolute path to the written file.
    """
    out_dir = os.path.join(os.path.abspath(csv_output_dir), "annotations")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "manual_annotations.template.csv")

    sample_row: dict[str, str] = {
        "as_of_jst": "2026-01-05T08:00:00+09:00",
        "regime_label": "trending",
        "event_tags": "fomc|cpi_us",
        "volatility_label": "high",
        "intervention_risk": "low",
        "notes": "Example: copy from ai_annotation_suggestions.csv and edit",
        "annotation_status": "pending",
    }
    _write_csv(path, [sample_row], MANUAL_ANNOTATION_FIELDNAMES)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# 3. Manual annotation loading
# ---------------------------------------------------------------------------


def load_manual_annotations(csv_output_dir: str) -> dict[str, dict[str, str]]:
    """Load ``manual_annotations.csv`` keyed by ``as_of_jst``.

    Returns an empty dict if the file does not exist.
    """
    path = os.path.join(
        os.path.abspath(csv_output_dir), "annotations", "manual_annotations.csv"
    )
    if not os.path.isfile(path):
        return {}
    result: dict[str, dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            key = row.get("as_of_jst", "")
            if key:
                result[key] = dict(row)
    return result


# ---------------------------------------------------------------------------
# 4. Labeled observations generation
# ---------------------------------------------------------------------------


def build_labeled_observations(
    csv_output_dir: str,
    generated_at_utc: datetime,
) -> str | None:
    """Build ``labeled_observations.csv`` by joining history CSVs with manual annotations.

    Scans all history/ directories for forecast, outcome, and evaluation CSVs,
    joins them by as_of_jst/date, and left-joins manual annotations.

    AI suggestion columns are intentionally excluded from this main analysis CSV.

    Returns the absolute path to the written file, or ``None`` on failure.
    """
    try:
        base = os.path.abspath(csv_output_dir)
        history_dir = os.path.join(base, "history")
        if not os.path.isdir(history_dir):
            return None

        annotations = load_manual_annotations(csv_output_dir)
        rows = _collect_labeled_observation_rows(history_dir, annotations)

        if not rows:
            return None

        out_dir = os.path.join(base, "analytics")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "labeled_observations.csv")
        _write_csv(path, rows, LABELED_OBSERVATION_FIELDNAMES)
        return os.path.abspath(path)
    except Exception:
        logger.warning("labeled_observations generation failed (non-fatal).", exc_info=True)
        return None


def _collect_labeled_observation_rows(
    history_dir: str,
    annotations: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    """Scan history/ and build labeled observation rows.

    Evaluations live in the *next* day's batch (they evaluate the previous
    day's forecasts against that day's outcome).  To join correctly we first
    build a global ``forecast_id → evaluation`` index across all batches,
    then iterate over forecasts and look up evaluations from that index.

    Outcome data is similarly indexed by the evaluated forecast_id so that
    realized direction/change are attached to the correct forecast row.
    """
    # Pass 1: build global evaluation and outcome indexes across all batches.
    global_eval_by_forecast: dict[str, dict[str, str]] = {}
    global_outcome_by_forecast: dict[str, dict[str, str]] = {}

    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            batch_path = os.path.join(date_path, batch_dir)
            eval_csv = os.path.join(batch_path, "evaluation.csv")
            outcome_csv = os.path.join(batch_path, "outcome.csv")

            if os.path.isfile(eval_csv):
                evals = _read_csv_rows(eval_csv)
                outcome_row: dict[str, str] | None = None
                if os.path.isfile(outcome_csv):
                    outcome_rows = _read_csv_rows(outcome_csv)
                    if outcome_rows:
                        outcome_row = outcome_rows[0]
                for ev in evals:
                    fid = ev.get("forecast_id", "")
                    if fid:
                        global_eval_by_forecast[fid] = ev
                        if outcome_row is not None:
                            global_outcome_by_forecast[fid] = outcome_row

    # Pass 2: iterate over forecasts and join with global indexes.
    rows: list[dict[str, str]] = []

    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            batch_path = os.path.join(date_path, batch_dir)
            forecast_csv = os.path.join(batch_path, "forecast.csv")

            if not os.path.isfile(forecast_csv):
                continue

            forecasts = _read_csv_rows(forecast_csv)

            for fc in forecasts:
                as_of_jst = fc.get("as_of_jst", "")
                forecast_id = fc.get("forecast_id", "")
                ev = global_eval_by_forecast.get(forecast_id, {})
                outcome_row = global_outcome_by_forecast.get(forecast_id)

                # Lookup annotation by as_of_jst
                ann = annotations.get(as_of_jst, {})

                row: dict[str, str] = {
                    "as_of_jst": as_of_jst,
                    "forecast_batch_id": fc.get("forecast_batch_id", ""),
                    "outcome_id": ev.get("outcome_id", ""),
                    "strategy_kind": fc.get("strategy_kind", ""),
                    "forecast_direction": fc.get("forecast_direction", ""),
                    "expected_close_change_bp": fc.get("expected_close_change_bp", ""),
                    "realized_direction": (
                        outcome_row.get("realized_direction", "")
                        if outcome_row
                        else ""
                    ),
                    "realized_close_change_bp": (
                        outcome_row.get("realized_close_change_bp", "")
                        if outcome_row
                        else ""
                    ),
                    "direction_hit": ev.get("direction_hit", ""),
                    "range_hit": ev.get("range_hit", ""),
                    "state_proxy_hit": ev.get("state_proxy_hit", ""),
                    "close_error_bp": ev.get("close_error_bp", ""),
                    "magnitude_error_bp": ev.get("magnitude_error_bp", ""),
                    "regime_label": ann.get("regime_label", ""),
                    "event_tags": ann.get("event_tags", ""),
                    "volatility_label": ann.get("volatility_label", ""),
                    "intervention_risk": ann.get("intervention_risk", ""),
                    "annotation_status": ann.get("annotation_status", ""),
                }
                rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# 5. Slice scoreboard generation
# ---------------------------------------------------------------------------


def build_slice_scoreboard(
    csv_output_dir: str,
    generated_at_utc: datetime,
) -> str | None:
    """Build ``slice_scoreboard.csv`` from labeled observations.

    Aggregates by ``(strategy_kind, regime_label, volatility_label, intervention_risk)``.

    Scoring priority:
    - Rows with ``annotation_status=confirmed`` are used preferentially.
    - Rows without confirmed annotation are grouped under empty-string labels
      (effectively "unlabeled").

    Returns the absolute path to the written file, or ``None`` on failure.
    """
    try:
        obs_path = os.path.join(
            os.path.abspath(csv_output_dir), "analytics", "labeled_observations.csv"
        )
        if not os.path.isfile(obs_path):
            return None

        obs_rows = _read_csv_rows(obs_path)
        if not obs_rows:
            return None

        sb_rows = _aggregate_slice_scoreboard(obs_rows, generated_at_utc)
        if not sb_rows:
            return None

        path = os.path.join(
            os.path.abspath(csv_output_dir), "analytics", "slice_scoreboard.csv"
        )
        _write_csv(path, sb_rows, SLICE_SCOREBOARD_FIELDNAMES)
        return os.path.abspath(path)
    except Exception:
        logger.warning("slice_scoreboard generation failed (non-fatal).", exc_info=True)
        return None


def _aggregate_slice_scoreboard(
    obs_rows: list[dict[str, str]],
    generated_at_utc: datetime,
) -> list[dict[str, Any]]:
    """Aggregate observations into slice scoreboard rows.

    Confirmed annotations use their labels as-is.  Non-confirmed rows
    (pending, missing, or empty status) have their annotation labels
    replaced with empty strings, effectively bucketing them as "unlabeled".
    """
    GroupKey = tuple[str, str, str, str]
    groups: dict[GroupKey, list[dict[str, str]]] = defaultdict(list)

    for row in obs_rows:
        status = row.get("annotation_status", "").strip().lower()
        if status == "confirmed":
            key: GroupKey = (
                row.get("strategy_kind", ""),
                row.get("regime_label", ""),
                row.get("volatility_label", ""),
                row.get("intervention_risk", ""),
            )
        else:
            # Unlabeled: use strategy_kind only, blank labels
            key = (row.get("strategy_kind", ""), "", "", "")
        groups[key].append(row)

    ts = generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    result: list[dict[str, Any]] = []

    for (sk, rl, vl, ir), rows in sorted(groups.items()):
        n = len(rows)
        dir_hits = _count_bool(rows, "direction_hit")
        range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
        range_hits = _count_bool(range_evaluable, "range_hit")
        state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
        state_hits = _count_bool(state_evaluable, "state_proxy_hit")
        close_errors = _collect_floats(rows, "close_error_bp")
        mag_errors = _collect_floats(rows, "magnitude_error_bp")

        result.append({
            "strategy_kind": sk,
            "regime_label": rl,
            "volatility_label": vl,
            "intervention_risk": ir,
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
            "mean_close_error_bp": (
                round(sum(close_errors) / len(close_errors), 2) if close_errors else ""
            ),
            "median_close_error_bp": (
                round(median(close_errors), 2) if close_errors else ""
            ),
            "mean_magnitude_error_bp": (
                round(sum(mag_errors) / len(mag_errors), 2) if mag_errors else ""
            ),
            "last_updated_utc": ts,
        })

    return result


# ---------------------------------------------------------------------------
# 6. Tag scoreboard generation
# ---------------------------------------------------------------------------


def build_tag_scoreboard(
    csv_output_dir: str,
    generated_at_utc: datetime,
) -> str | None:
    """Build ``tag_scoreboard.csv`` by expanding event_tags and aggregating per tag.

    Only rows with ``annotation_status=confirmed`` are included.
    Each tag in a pipe-delimited ``event_tags`` field generates a separate
    observation in the per-tag aggregation.

    Returns the absolute path to the written file, or ``None`` on failure.
    """
    try:
        obs_path = os.path.join(
            os.path.abspath(csv_output_dir), "analytics", "labeled_observations.csv"
        )
        if not os.path.isfile(obs_path):
            return None

        obs_rows = _read_csv_rows(obs_path)
        if not obs_rows:
            return None

        tag_rows = _aggregate_tag_scoreboard(obs_rows, generated_at_utc)
        if not tag_rows:
            return None

        path = os.path.join(
            os.path.abspath(csv_output_dir), "analytics", "tag_scoreboard.csv"
        )
        _write_csv(path, tag_rows, TAG_SCOREBOARD_FIELDNAMES)
        return os.path.abspath(path)
    except Exception:
        logger.warning("tag_scoreboard generation failed (non-fatal).", exc_info=True)
        return None


def _aggregate_tag_scoreboard(
    obs_rows: list[dict[str, str]],
    generated_at_utc: datetime,
) -> list[dict[str, Any]]:
    """Aggregate observations by (strategy_kind, event_tag)."""
    TagKey = tuple[str, str]
    groups: dict[TagKey, list[dict[str, str]]] = defaultdict(list)

    for row in obs_rows:
        # Only confirmed annotations contribute to per-tag analysis.
        # Pending/unlabeled rows are excluded to prevent draft labels from
        # skewing tag-level metrics.
        if row.get("annotation_status", "").strip().lower() != "confirmed":
            continue
        tags_str = row.get("event_tags", "")
        if not tags_str:
            continue
        tags = [t.strip() for t in tags_str.split("|") if t.strip()]
        sk = row.get("strategy_kind", "")
        for tag in tags:
            groups[(sk, tag)].append(row)

    ts = generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    result: list[dict[str, Any]] = []

    for (sk, tag), rows in sorted(groups.items()):
        n = len(rows)
        dir_hits = _count_bool(rows, "direction_hit")
        range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
        range_hits = _count_bool(range_evaluable, "range_hit")
        state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
        state_hits = _count_bool(state_evaluable, "state_proxy_hit")
        close_errors = _collect_floats(rows, "close_error_bp")
        mag_errors = _collect_floats(rows, "magnitude_error_bp")

        result.append({
            "strategy_kind": sk,
            "event_tag": tag,
            "observation_count": n,
            "direction_hit_rate": round(dir_hits / n, 4) if n > 0 else "",
            "range_hit_rate": (
                round(range_hits / len(range_evaluable), 4) if range_evaluable else ""
            ),
            "state_proxy_hit_rate": (
                round(state_hits / len(state_evaluable), 4) if state_evaluable else ""
            ),
            "mean_close_error_bp": (
                round(sum(close_errors) / len(close_errors), 2) if close_errors else ""
            ),
            "mean_magnitude_error_bp": (
                round(sum(mag_errors) / len(mag_errors), 2) if mag_errors else ""
            ),
            "last_updated_utc": ts,
        })

    return result


# ---------------------------------------------------------------------------
# 7. Orchestrator: run all annotation + analytics steps
# ---------------------------------------------------------------------------


def run_annotation_analytics(
    csv_output_dir: str,
    as_of_jst: datetime,
    generated_at_utc: datetime | None = None,
) -> dict[str, str | None]:
    """Run all annotation and analytics generation steps.

    This is the single entry-point called by automation.py after all existing
    steps have completed.  Each sub-step is independently guarded so that
    failures do not propagate.

    Returns a dict of artifact keys to absolute paths (or ``None`` on failure).
    """
    if generated_at_utc is None:
        generated_at_utc = datetime.now(timezone.utc)

    result: dict[str, str | None] = {
        "ai_annotation_suggestions_path": None,
        "manual_annotation_template_path": None,
        "labeled_observations_path": None,
        "slice_scoreboard_path": None,
        "tag_scoreboard_path": None,
    }

    # Step A: AI draft annotations
    try:
        result["ai_annotation_suggestions_path"] = generate_ai_annotations(
            csv_output_dir, as_of_jst, generated_at_utc
        )
    except Exception:
        logger.warning("AI annotation step failed (non-fatal).", exc_info=True)

    # Step B: Manual annotation template
    try:
        result["manual_annotation_template_path"] = generate_manual_annotation_template(
            csv_output_dir
        )
    except Exception:
        logger.warning("Manual annotation template step failed (non-fatal).", exc_info=True)

    # Step C: Labeled observations (must run before scoreboards)
    try:
        result["labeled_observations_path"] = build_labeled_observations(
            csv_output_dir, generated_at_utc
        )
    except Exception:
        logger.warning("Labeled observations step failed (non-fatal).", exc_info=True)

    # Step D: Slice scoreboard
    try:
        result["slice_scoreboard_path"] = build_slice_scoreboard(
            csv_output_dir, generated_at_utc
        )
    except Exception:
        logger.warning("Slice scoreboard step failed (non-fatal).", exc_info=True)

    # Step E: Tag scoreboard
    try:
        result["tag_scoreboard_path"] = build_tag_scoreboard(
            csv_output_dir, generated_at_utc
        )
    except Exception:
        logger.warning("Tag scoreboard step failed (non-fatal).", exc_info=True)

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _write_csv(
    path: str,
    rows: list[dict[str, Any]],
    fieldnames: tuple[str, ...],
) -> str:
    """Write rows to CSV.  Returns absolute path."""
    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return abs_path


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    """Read all rows from a CSV file."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _count_bool(rows: list[dict[str, str]], field: str) -> int:
    """Count rows where *field* is truthy."""
    return sum(
        1 for r in rows
        if r.get(field, "").lower() in ("true", "1", "yes")
    )


def _collect_floats(rows: list[dict[str, str]], field: str) -> list[float]:
    """Collect non-empty float values from *field*."""
    result: list[float] = []
    for r in rows:
        v = r.get(field, "")
        if v != "":
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                pass
    return result
