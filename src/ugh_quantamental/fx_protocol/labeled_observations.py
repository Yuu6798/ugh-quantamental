"""Labeled-observations builder — derives the annotated observation rows
that feed weekly / monthly review pipelines.

Pure read-only post-processing layer: reads forecast / outcome / evaluation
history plus AI / manual annotations, joins by ``forecast_id``, resolves
effective labels via the AI → auto → manual precedence, and writes
``analytics/labeled_observations.csv``.

Responsibility split (split out of ``analytics_annotations`` in Phase 2):

* This module: labeled-observations build, manual-annotation loading,
  deterministic auto event-tag derivation. Produces the substrate.
* ``analytics_annotations``: AI draft generation, manual template,
  slice / tag scoreboards, orchestrator. Consumes the substrate.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import calendar
import csv
import logging
import os
from datetime import datetime, timedelta

from ugh_quantamental.fx_protocol.csv_utils import write_csv_rows

logger = logging.getLogger(__name__)


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
    # AI annotation fields (primary source for analysis)
    "ai_regime_label",
    "ai_volatility_label",
    "ai_intervention_risk",
    "ai_event_tags",
    "ai_failure_reason",
    "ai_annotation_confidence",
    "ai_annotation_model_version",
    "ai_annotation_prompt_version",
    "ai_evidence_refs",
    "ai_annotation_status",
    # Effective labels (resolved via AI > auto > manual precedence)
    "regime_label",
    "event_tags",
    "manual_event_tags",
    "auto_event_tags",
    "effective_event_tags",
    "event_tag_source",
    "volatility_label",
    "intervention_risk",
    "failure_reason",
    "annotation_source",
    "annotation_status",
)


# ---------------------------------------------------------------------------
# Manual annotation loading
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
# Deterministic auto event-tag derivation
# ---------------------------------------------------------------------------


def _is_last_business_day_of_month(dt: datetime) -> bool:
    """Return True if *dt* is the last Mon-Fri day in its calendar month."""
    year, month = dt.year, dt.month
    last_day = calendar.monthrange(year, month)[1]
    candidate = datetime(year, month, last_day)
    while candidate.isoweekday() > 5:
        candidate -= timedelta(days=1)
    return dt.day == candidate.day


def _derive_auto_event_tags(
    as_of_jst: str,
    outcome_row: dict[str, str] | None,
) -> list[str]:
    """Derive deterministic auto event tags from available data.

    Rules:
    1. Outcome event tags from the evaluation window are included verbatim.
    2. ``month_end`` is added when ``as_of_jst`` falls on the last protocol
       business day (Mon-Fri) of its calendar month.
    3. ``quarter_end`` is added when ``as_of_jst`` falls on the last protocol
       business day of Mar, Jun, Sep, or Dec.

    Returns a sorted, deduplicated list of tag strings.
    """
    tags: set[str] = set()

    # Outcome-derived tags
    if outcome_row:
        raw = outcome_row.get("event_tags", "")
        if raw:
            for t in raw.split("|"):
                t = t.strip()
                if t:
                    tags.add(t)

    # Calendar-derived tags
    try:
        date_str = as_of_jst[:10]  # "YYYY-MM-DD"
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, IndexError):
        return sorted(tags)

    if _is_last_business_day_of_month(dt):
        tags.add("month_end")
        if dt.month in (3, 6, 9, 12):
            tags.add("quarter_end")

    return sorted(tags)


def _build_event_tag_fields(
    manual_tags_raw: str,
    auto_tags: list[str],
) -> tuple[str, str, str, str]:
    """Compute (manual_event_tags, auto_event_tags, effective_event_tags, event_tag_source).

    ``effective_event_tags`` is the deduplicated union of manual and auto tags.
    ``event_tag_source`` is one of: manual, auto, mixed, none.
    """
    manual_list = [t.strip() for t in manual_tags_raw.split("|") if t.strip()] if manual_tags_raw else []
    manual_set = set(manual_list)
    auto_set = set(auto_tags)
    effective = sorted(manual_set | auto_set)

    manual_str = "|".join(sorted(manual_set)) if manual_set else ""
    auto_str = "|".join(auto_tags) if auto_tags else ""
    effective_str = "|".join(effective) if effective else ""

    if manual_set and auto_set:
        source = "mixed" if (auto_set - manual_set) else "manual"
    elif manual_set:
        source = "manual"
    elif auto_set:
        source = "auto"
    else:
        source = "none"

    return manual_str, auto_str, effective_str, source


# ---------------------------------------------------------------------------
# Labeled observations build
# ---------------------------------------------------------------------------


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    """Read all rows from a CSV file."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_labeled_observations(
    csv_output_dir: str,
    generated_at_utc: datetime,
    ai_annotations: dict[str, dict[str, str]] | None = None,
) -> str | None:
    """Build ``labeled_observations.csv`` joining history CSVs with annotations.

    AI annotations are the primary annotation source.  Manual annotations
    are optional compatibility inputs with lowest precedence.

    Parameters
    ----------
    ai_annotations:
        Optional dict keyed by forecast_id containing AI annotation fields.
        When provided, these become the primary source for regime/volatility/
        intervention/event-tag labels.

    Returns the absolute path to the written file, or ``None`` on failure.
    """
    try:
        base = os.path.abspath(csv_output_dir)
        history_dir = os.path.join(base, "history")
        if not os.path.isdir(history_dir):
            return None

        manual_annotations = load_manual_annotations(csv_output_dir)
        rows = _collect_labeled_observation_rows(
            history_dir, manual_annotations, ai_annotations or {},
        )

        if not rows:
            return None

        out_dir = os.path.join(base, "analytics")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "labeled_observations.csv")
        write_csv_rows(path, rows, LABELED_OBSERVATION_FIELDNAMES, extrasaction="ignore")
        return os.path.abspath(path)
    except Exception:
        logger.warning("labeled_observations generation failed (non-fatal).", exc_info=True)
        return None


def _collect_labeled_observation_rows(
    history_dir: str,
    manual_annotations: dict[str, dict[str, str]],
    ai_annotations: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    """Scan history/ and build labeled observation rows.

    Uses AI-first annotation precedence:
      1. AI annotation labels (primary)
      2. Deterministic auto-derived labels
      3. Manual compatibility labels (lowest priority)

    Evaluations live in the *next* day's batch (they evaluate the previous
    day's forecasts against that day's outcome).  To join correctly we first
    build a global ``forecast_id → evaluation`` index across all batches,
    then iterate over forecasts and look up evaluations from that index.
    """
    from ugh_quantamental.fx_protocol.annotation_sources import (
        SOURCE_AI,
        SOURCE_AI_PLUS_AUTO,
        SOURCE_AUTO_ONLY,
        SOURCE_MANUAL_COMPAT,
        SOURCE_NONE,
        resolve_effective_event_tags,
        resolve_effective_label,
    )

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

                # Skip forecasts without a matched evaluation to avoid
                # counting unevaluated rows as misses in weekly metrics.
                if not ev:
                    continue

                outcome_row = global_outcome_by_forecast.get(forecast_id)

                # AI annotation lookup (primary source)
                ai = ai_annotations.get(forecast_id, {})

                # Manual annotation lookup (compatibility)
                manual = manual_annotations.get(as_of_jst, {})

                # Auto-derived event tags
                auto_tags = _derive_auto_event_tags(as_of_jst, outcome_row)

                # AI event tags
                ai_tags_raw = ai.get("ai_event_tags", "")
                ai_tag_list = [t.strip() for t in ai_tags_raw.split("|") if t.strip()] if ai_tags_raw else []

                # Manual event tags
                manual_tags_raw = manual.get("event_tags", "")
                manual_tag_list = [t.strip() for t in manual_tags_raw.split("|") if t.strip()] if manual_tags_raw else []

                # Resolve effective event tags (AI > auto > manual)
                effective_et, et_source = resolve_effective_event_tags(
                    ai_tags=ai_tag_list, auto_tags=auto_tags, manual_tags=manual_tag_list,
                )

                # Resolve effective labels (AI > auto > manual)
                eff_regime, regime_src = resolve_effective_label(
                    ai_value=ai.get("ai_regime_label", ""),
                    auto_value="",
                    manual_value=manual.get("regime_label", ""),
                )
                eff_vol, _ = resolve_effective_label(
                    ai_value=ai.get("ai_volatility_label", ""),
                    auto_value="",
                    manual_value=manual.get("volatility_label", ""),
                )
                eff_ir, _ = resolve_effective_label(
                    ai_value=ai.get("ai_intervention_risk", ""),
                    auto_value="",
                    manual_value=manual.get("intervention_risk", ""),
                )

                # Determine overall annotation_source from all effective fields.
                # Any AI-populated field makes the row AI-annotated.
                has_ai = bool(
                    ai.get("ai_regime_label", "")
                    or ai.get("ai_volatility_label", "")
                    or ai.get("ai_intervention_risk", "")
                    or ai.get("ai_event_tags", "")
                    or ai.get("ai_failure_reason", "")
                )
                has_auto = bool(auto_tags)
                if has_ai and has_auto:
                    annotation_source = SOURCE_AI_PLUS_AUTO
                elif has_ai:
                    annotation_source = SOURCE_AI
                elif has_auto:
                    annotation_source = SOURCE_AUTO_ONLY
                elif manual.get("annotation_status", ""):
                    annotation_source = SOURCE_MANUAL_COMPAT
                else:
                    annotation_source = SOURCE_NONE

                manual_et = "|".join(sorted(manual_tag_list)) if manual_tag_list else ""
                auto_et = "|".join(auto_tags) if auto_tags else ""

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
                    # AI annotation fields
                    "ai_regime_label": ai.get("ai_regime_label", ""),
                    "ai_volatility_label": ai.get("ai_volatility_label", ""),
                    "ai_intervention_risk": ai.get("ai_intervention_risk", ""),
                    "ai_event_tags": ai.get("ai_event_tags", ""),
                    "ai_failure_reason": ai.get("ai_failure_reason", ""),
                    "ai_annotation_confidence": ai.get("ai_annotation_confidence", ""),
                    "ai_annotation_model_version": ai.get("ai_annotation_model_version", ""),
                    "ai_annotation_prompt_version": ai.get("ai_annotation_prompt_version", ""),
                    "ai_evidence_refs": ai.get("ai_evidence_refs", ""),
                    "ai_annotation_status": ai.get("ai_annotation_status", ""),
                    # Effective labels (resolved via AI > auto > manual)
                    "regime_label": eff_regime,
                    "event_tags": effective_et,
                    "manual_event_tags": manual_et,
                    "auto_event_tags": auto_et,
                    "effective_event_tags": effective_et,
                    "event_tag_source": et_source,
                    "volatility_label": eff_vol,
                    "intervention_risk": eff_ir,
                    "failure_reason": ai.get("ai_failure_reason", ""),
                    "annotation_source": annotation_source,
                    # AI-annotated rows are treated as "confirmed" for
                    # downstream scoreboards that gate on annotation_status.
                    "annotation_status": (
                        "confirmed"
                        if has_ai
                        else manual.get("annotation_status", "")
                    ),
                }
                rows.append(row)

    return rows


__all__ = [
    "LABELED_OBSERVATION_FIELDNAMES",
    "build_labeled_observations",
    "load_manual_annotations",
]
