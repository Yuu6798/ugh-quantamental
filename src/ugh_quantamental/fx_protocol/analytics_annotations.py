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

from ugh_quantamental.fx_protocol.csv_utils import write_csv_rows
from ugh_quantamental.fx_protocol.labeled_observations import (
    LABELED_OBSERVATION_FIELDNAMES,
    _build_event_tag_fields,
    _derive_auto_event_tags,
    _is_last_business_day_of_month,
    build_labeled_observations,
    collect_evaluated_forecast_rows,
    load_manual_annotations,
)
from ugh_quantamental.fx_protocol.metrics_utils import collect_floats, count_bool_rows

logger = logging.getLogger(__name__)

# Star-import contract: every previously-public top-level name in this module,
# including the labeled-observations symbols re-imported above for backwards
# compatibility (callers in __init__, automation, analytics_rebuild, and tests
# import these from analytics_annotations). Private re-exports
# (_build_event_tag_fields, _derive_auto_event_tags,
# _is_last_business_day_of_month) are listed because the test suite imports
# them by name from this module.
__all__ = [
    "AI_ANNOTATION_FIELDNAMES",
    "LABELED_OBSERVATION_FIELDNAMES",
    "MANUAL_ANNOTATION_FIELDNAMES",
    "SLICE_SCOREBOARD_FIELDNAMES",
    "TAG_SCOREBOARD_FIELDNAMES",
    "_build_event_tag_fields",
    "_derive_auto_event_tags",
    "_is_last_business_day_of_month",
    "build_labeled_observations",
    "build_slice_scoreboard",
    "build_tag_scoreboard",
    "generate_ai_annotations",
    "generate_manual_annotation_template",
    "load_manual_annotations",
    "run_annotation_analytics",
]


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
        write_csv_rows(path, rows, AI_ANNOTATION_FIELDNAMES, extrasaction="ignore")
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

    Heuristics (purely supplementary, never authoritative). Regime and
    volatility are derived ONLY from realized OHLC / market statistics — never
    from forecast-accuracy fields (``direction_hit`` / ``close_error_bp``),
    which would make the labels circular (see
    engine_review_2026_06_planning.md §5.1). Output uses the shared vocabulary
    (trending/choppy, low/normal/high) — no "mixed"/"unknown" third bucket.

    - regime_label: close-change sign consistency over recent outcomes
    - volatility_label: recent intraday range vs trailing baseline
    - event_tags: collected from recent outcome event_tags
    - intervention_risk: magnitude of recent realized moves (a market fact)
    """
    from ugh_quantamental.fx_protocol.annotation_fallback import (
        REGIME_CHOPPY,
        VOL_NORMAL,
        classify_regime,
        classify_volatility,
        intraday_range_bp,
    )

    base = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(base, "history")

    regime_label = REGIME_CHOPPY
    event_tags = ""
    volatility_label = VOL_NORMAL
    intervention_risk = "low"
    notes = "auto-generated draft (OHLC-derived)"

    # Scan recent outcomes for market-derived signals (oldest → newest).
    outcome_rows = _collect_recent_outcome_rows(history_dir, limit=5)
    ohlc_series = sorted(
        outcome_rows, key=lambda r: r.get("window_end_jst", "")
    )

    close_changes: list[float] = []
    ranges_bp: list[float] = []
    for r in ohlc_series:
        try:
            change = float(r.get("realized_close_change_bp", ""))
            close_changes.append(change)
        except (ValueError, TypeError):
            pass
        try:
            o = float(r.get("realized_open", ""))
            h = float(r.get("realized_high", ""))
            low = float(r.get("realized_low", ""))
            ranges_bp.append(intraday_range_bp(h, low, o))
        except (ValueError, TypeError):
            pass

    if close_changes:
        regime_label = classify_regime(close_changes)
    if ranges_bp:
        latest_range = ranges_bp[-1]
        prior = ranges_bp[:-1]
        baseline = sum(prior) / len(prior) if prior else 0.0
        volatility_label = classify_volatility(latest_range, baseline)

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
    write_csv_rows(path, [sample_row], MANUAL_ANNOTATION_FIELDNAMES, extrasaction="ignore")
    return os.path.abspath(path)


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
        write_csv_rows(path, sb_rows, SLICE_SCOREBOARD_FIELDNAMES, extrasaction="ignore")
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
        dir_hits = count_bool_rows(rows, "direction_hit")
        range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
        range_hits = count_bool_rows(range_evaluable, "range_hit")
        state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
        state_hits = count_bool_rows(state_evaluable, "state_proxy_hit")
        close_errors = collect_floats(rows, "close_error_bp")
        mag_errors = collect_floats(rows, "magnitude_error_bp")

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
        write_csv_rows(path, tag_rows, TAG_SCOREBOARD_FIELDNAMES, extrasaction="ignore")
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
        dir_hits = count_bool_rows(rows, "direction_hit")
        range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
        range_hits = count_bool_rows(range_evaluable, "range_hit")
        state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
        state_hits = count_bool_rows(state_evaluable, "state_proxy_hit")
        close_errors = collect_floats(rows, "close_error_bp")
        mag_errors = collect_floats(rows, "magnitude_error_bp")

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

    # Step C: Labeled observations (must run before scoreboards).
    #
    # The daily live path must wire AI + deterministic OHLC fallback labels
    # into the labeled observations, mirroring the weekly rebuild path.
    # Historically Step C called build_labeled_observations WITHOUT any
    # annotation source, which is why live weekly reports were 28/28
    # unannotated (FX-ANNOT-LIVE root cause): suggestions never reached the
    # effective labels. Both passes are deterministic and API-key-free.
    try:
        ai_annotations, fallback_annotations = _build_daily_annotations(
            csv_output_dir, generated_at_utc
        )
        result["labeled_observations_path"] = build_labeled_observations(
            csv_output_dir,
            generated_at_utc,
            ai_annotations=ai_annotations,
            fallback_annotations=fallback_annotations,
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


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    """Read all rows from a CSV file."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _build_daily_annotations(
    csv_output_dir: str,
    generated_at_utc: datetime,
) -> tuple[dict[str, dict[str, str]] | None, dict[str, dict[str, str]] | None]:
    """Build forecast_id-keyed AI + OHLC fallback annotations for the daily path.

    Returns ``(ai_annotations, fallback_annotations)``, either of which may be
    ``None`` when no evaluated history is available. Both passes are
    deterministic and require no API key. Failures are swallowed so the daily
    run is never broken by the annotation layer.
    """
    history_dir = os.path.join(os.path.abspath(csv_output_dir), "history")
    if not os.path.isdir(history_dir):
        return None, None

    ai_annotations: dict[str, dict[str, str]] | None = None
    fallback_annotations: dict[str, dict[str, str]] | None = None
    try:
        from ugh_quantamental.fx_protocol.ai_annotations import (
            ai_batch_to_lookup,
            run_ai_annotation_pass,
        )
        from ugh_quantamental.fx_protocol.annotation_fallback import (
            build_ohlc_fallback_annotations,
        )

        obs = collect_evaluated_forecast_rows(history_dir)
        if obs:
            fallback_annotations = build_ohlc_fallback_annotations(obs)
            batch = run_ai_annotation_pass(obs, generated_at_utc=generated_at_utc)
            if batch:
                ai_annotations = ai_batch_to_lookup(batch)
    except Exception:
        logger.warning("Daily AI/fallback annotation pass failed (non-fatal).", exc_info=True)

    return ai_annotations, fallback_annotations
