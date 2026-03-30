"""Weekly Report v2 — annotation-aware weekly analytics for the FX Daily Protocol.

Extends the existing weekly report with confirmed-annotation-based regime,
volatility, intervention, and event-tag slicing.  All data is derived from
persisted CSV history and annotation files — no engine logic is recomputed.

This module is a pure post-processing layer:
- No forecast / outcome / evaluation logic is changed.
- Existing ``run_weekly_report`` (v1) is untouched.
- Importable without SQLAlchemy.
"""

from __future__ import annotations

import csv
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Column definitions for v2 CSV outputs
# ---------------------------------------------------------------------------

WEEKLY_STRATEGY_METRICS_FIELDNAMES: tuple[str, ...] = (
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
)

WEEKLY_SLICE_METRICS_FIELDNAMES: tuple[str, ...] = (
    "slice_dimension",
    "strategy_kind",
    "label",
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
)


# ---------------------------------------------------------------------------
# Pure helpers (no I/O)
# ---------------------------------------------------------------------------


def _resolve_week_window(
    report_date_jst: datetime,
    business_day_count: int = 5,
) -> tuple[str, str]:
    """Return (start_date_str, end_date_str) for the week window.

    Walks backwards from the day *before* *report_date_jst* collecting
    *business_day_count* Mon-Fri dates.  The report date itself is excluded
    to avoid including an incomplete current-day bucket.
    Returns YYYYMMDD strings for the oldest and newest dates.
    """
    if report_date_jst.tzinfo is not None:
        ts = report_date_jst.astimezone(_JST)
    else:
        ts = report_date_jst.replace(tzinfo=_JST)

    dates: list[datetime] = []
    # Start from the day before report_date to exclude the (potentially incomplete) current day.
    candidate = ts.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    while len(dates) < business_day_count:
        if candidate.isoweekday() in range(1, 6):
            dates.append(candidate)
        candidate -= timedelta(days=1)

    dates.reverse()
    return dates[0].strftime("%Y%m%d"), dates[-1].strftime("%Y%m%d")


def _is_in_week(date_str: str, start: str, end: str) -> bool:
    """Check if a YYYYMMDD date string falls within [start, end]."""
    return start <= date_str <= end


def _count_bool(rows: list[dict[str, str]], field: str) -> int:
    return sum(
        1 for r in rows if r.get(field, "").lower() in ("true", "1", "yes")
    )


def _collect_floats(rows: list[dict[str, str]], field: str) -> list[float]:
    result: list[float] = []
    for r in rows:
        v = r.get(field, "")
        if v != "":
            try:
                result.append(float(v))
            except (ValueError, TypeError):
                pass
    return result


def _safe_rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return ""
    return str(round(numerator / denominator, 4))


def _safe_mean(values: list[float]) -> str:
    if not values:
        return ""
    return str(round(sum(values) / len(values), 2))


def _safe_median(values: list[float]) -> str:
    if not values:
        return ""
    return str(round(median(values), 2))


def _compute_metrics_for_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Compute standard metrics from a list of labeled observation rows."""
    n = len(rows)
    dir_hits = _count_bool(rows, "direction_hit")
    range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
    range_hits = _count_bool(range_evaluable, "range_hit")
    state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
    state_hits = _count_bool(state_evaluable, "state_proxy_hit")
    close_errors = _collect_floats(rows, "close_error_bp")
    mag_errors = _collect_floats(rows, "magnitude_error_bp")

    return {
        "observation_count": n,
        "direction_hit_count": dir_hits,
        "direction_hit_rate": _safe_rate(dir_hits, n),
        "range_hit_count": range_hits if range_evaluable else "",
        "range_hit_rate": _safe_rate(range_hits, len(range_evaluable)) if range_evaluable else "",
        "state_proxy_hit_count": state_hits if state_evaluable else "",
        "state_proxy_hit_rate": (
            _safe_rate(state_hits, len(state_evaluable)) if state_evaluable else ""
        ),
        "mean_close_error_bp": _safe_mean(close_errors),
        "median_close_error_bp": _safe_median(close_errors),
        "mean_magnitude_error_bp": _safe_mean(mag_errors),
    }


# ---------------------------------------------------------------------------
# Data loading helpers (CSV I/O only)
# ---------------------------------------------------------------------------


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _load_labeled_observations_for_week(
    csv_output_dir: str,
    week_start: str,
    week_end: str,
) -> list[dict[str, str]]:
    """Load labeled observations filtered to the given week window."""
    obs_path = os.path.join(os.path.abspath(csv_output_dir), "analytics", "labeled_observations.csv")
    all_rows = _read_csv_rows(obs_path)
    result: list[dict[str, str]] = []
    for row in all_rows:
        as_of = row.get("as_of_jst", "")
        # Extract YYYYMMDD from ISO datetime
        date_str = as_of[:10].replace("-", "") if len(as_of) >= 10 else ""
        if date_str and _is_in_week(date_str, week_start, week_end):
            result.append(row)
    return result


def _load_provider_health_rows(csv_output_dir: str) -> list[dict[str, str]]:
    """Load provider_health.csv from latest/ or observability layout."""
    base = os.path.abspath(csv_output_dir)
    # Try latest first, then scan history
    for candidate in [
        os.path.join(base, "latest", "provider_health.csv"),
        os.path.join(base, "provider_health.csv"),
    ]:
        if os.path.isfile(candidate):
            return _read_csv_rows(candidate)

    # Scan history for provider_health.csv files and merge.
    # History files are cumulative snapshots, so deduplicate by as_of_jst
    # to avoid inflating counts.
    history_dir = os.path.join(base, "history")
    if not os.path.isdir(history_dir):
        return []
    seen: dict[str, dict[str, str]] = {}
    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            ph_csv = os.path.join(date_path, batch_dir, "provider_health.csv")
            if os.path.isfile(ph_csv):
                for row in _read_csv_rows(ph_csv):
                    key = row.get("as_of_jst", "")
                    if key:
                        seen[key] = row
    return list(seen.values())


def _filter_provider_health_for_week(
    rows: list[dict[str, str]],
    week_start: str,
    week_end: str,
) -> list[dict[str, str]]:
    """Filter provider health rows to the given week window."""
    result: list[dict[str, str]] = []
    for row in rows:
        as_of = row.get("as_of_jst", "")
        date_str = as_of[:10].replace("-", "").replace("T", "")[:8] if as_of else ""
        if date_str and _is_in_week(date_str, week_start, week_end):
            result.append(row)
    return result


# ---------------------------------------------------------------------------
# Core v2 report building (pure functions operating on loaded data)
# ---------------------------------------------------------------------------


def build_annotation_coverage(
    observations: list[dict[str, str]],
) -> dict[str, Any]:
    """Compute annotation coverage summary from labeled observations."""
    total = len(observations)
    if total == 0:
        return {
            "total_observations": 0,
            "confirmed_annotation_count": 0,
            "pending_annotation_count": 0,
            "unlabeled_count": 0,
            "annotation_coverage_rate": 0.0,
        }

    confirmed = sum(
        1 for r in observations
        if r.get("annotation_status", "").strip().lower() == "confirmed"
    )
    pending = sum(
        1 for r in observations
        if r.get("annotation_status", "").strip().lower() == "pending"
    )
    unlabeled = total - confirmed - pending

    return {
        "total_observations": total,
        "confirmed_annotation_count": confirmed,
        "pending_annotation_count": pending,
        "unlabeled_count": unlabeled,
        "annotation_coverage_rate": round(confirmed / total, 4) if total > 0 else 0.0,
    }


def build_annotation_field_coverage(
    observations: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    """Compute per-field annotation coverage with AI-first source breakdown.

    For each field reports AI, auto, manual, and effective populated counts.
    """
    fields = (
        "regime_label", "event_tags", "volatility_label",
        "intervention_risk", "failure_reason",
    )
    # Map effective field → AI field → auto field fallback
    ai_field_map = {
        "regime_label": "ai_regime_label",
        "event_tags": "ai_event_tags",
        "volatility_label": "ai_volatility_label",
        "intervention_risk": "ai_intervention_risk",
        "failure_reason": "ai_failure_reason",
    }
    effective_field_map = {
        "event_tags": "effective_event_tags",
    }

    total = len(observations)
    result: dict[str, dict[str, Any]] = {}

    _empty: dict[str, Any] = {
        "total_observations": 0,
        "ai_populated_count": 0, "ai_populated_rate": 0.0,
        "auto_populated_count": 0, "auto_populated_rate": 0.0,
        "manual_populated_count": 0, "manual_populated_rate": 0.0,
        "effective_populated_count": 0, "effective_populated_rate": 0.0,
        "missing_count": 0, "missing_rate": 0.0,
    }

    for field in fields:
        if total == 0:
            result[field] = dict(_empty)
            continue

        ai_col = ai_field_map.get(field, "")
        eff_col = effective_field_map.get(field, field)

        ai_pop = sum(1 for r in observations if r.get(ai_col, "").strip()) if ai_col else 0
        auto_pop = sum(
            1 for r in observations
            if r.get("annotation_source", "").strip() in ("auto_only", "ai_plus_auto")
            and r.get(eff_col, "").strip()
        )
        manual_pop = sum(
            1 for r in observations
            if r.get("annotation_source", "").strip() == "manual_compat"
            and r.get(eff_col, "").strip()
        )
        eff_pop = sum(1 for r in observations if r.get(eff_col, "").strip())
        missing = total - eff_pop

        result[field] = {
            "total_observations": total,
            "ai_populated_count": ai_pop,
            "ai_populated_rate": round(ai_pop / total, 4),
            "auto_populated_count": auto_pop,
            "auto_populated_rate": round(auto_pop / total, 4),
            "manual_populated_count": manual_pop,
            "manual_populated_rate": round(manual_pop / total, 4),
            "effective_populated_count": eff_pop,
            "effective_populated_rate": round(eff_pop / total, 4),
            "missing_count": missing,
            "missing_rate": round(missing / total, 4),
        }

    return result


def build_event_tag_source_summary(
    observations: list[dict[str, str]],
) -> dict[str, int]:
    """Count observations by annotation_source."""
    from ugh_quantamental.fx_protocol.annotation_sources import ANNOTATION_SOURCE_VALUES
    counts: dict[str, int] = {s: 0 for s in ANNOTATION_SOURCE_VALUES}
    for row in observations:
        source = row.get("annotation_source", "none").strip()
        if source in counts:
            counts[source] += 1
        else:
            counts["none"] += 1
    return counts


def build_strategy_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute per-strategy metrics from weekly observations."""
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in observations:
        sk = row.get("strategy_kind", "")
        if sk:
            groups[sk].append(row)

    result: list[dict[str, Any]] = []
    for sk in sorted(groups.keys()):
        metrics = _compute_metrics_for_rows(groups[sk])
        metrics["strategy_kind"] = sk
        result.append(metrics)
    return result


def build_slice_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute metrics sliced by (strategy_kind x annotation dimension).

    Slices:
    - strategy_kind x regime_label
    - strategy_kind x volatility_label
    - strategy_kind x intervention_risk
    - strategy_kind x event_tag (expanded)

    When confirmed annotations exist, they are used for labeled slices and
    non-confirmed rows go into an 'unlabeled' bucket.  When no confirmed
    annotations exist at all, all observations are sliced directly by their
    AI-suggested or empty labels so that the weekly report still provides
    useful per-strategy metrics without manual annotation.
    """
    from ugh_quantamental.fx_protocol.annotation_sources import SOURCE_NONE

    result: list[dict[str, Any]] = []

    # AI-first: annotated rows are those with any non-none annotation_source
    # (AI, AI+auto, auto, or manual_compat).  This replaces the old
    # confirmed-manual-only gate.
    annotated = [
        r for r in observations
        if r.get("annotation_source", SOURCE_NONE).strip() != SOURCE_NONE
    ]
    has_annotated = len(annotated) > 0

    # Dimension slices
    dimensions = [
        ("regime_label", "regime_label"),
        ("volatility_label", "volatility_label"),
        ("intervention_risk", "intervention_risk"),
    ]

    if has_annotated:
        unannotated = [
            r for r in observations
            if r.get("annotation_source", SOURCE_NONE).strip() == SOURCE_NONE
        ]

        for dim_name, field in dimensions:
            groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
            for row in annotated:
                sk = row.get("strategy_kind", "")
                label = row.get(field, "") or "unknown"
                groups[(sk, label)].append(row)

            unlabeled_by_sk: dict[str, list[dict[str, str]]] = defaultdict(list)
            for row in unannotated:
                sk = row.get("strategy_kind", "")
                unlabeled_by_sk[sk].append(row)
            for sk, rows in unlabeled_by_sk.items():
                groups[(sk, "unlabeled")].extend(rows)

            for (sk, label), rows in sorted(groups.items()):
                if not rows:
                    continue
                metrics = _compute_metrics_for_rows(rows)
                metrics["slice_dimension"] = dim_name
                metrics["strategy_kind"] = sk
                metrics["label"] = label
                result.append(metrics)
    else:
        for dim_name, _field in dimensions:
            groups_all: dict[str, list[dict[str, str]]] = defaultdict(list)
            for row in observations:
                sk = row.get("strategy_kind", "")
                groups_all[sk].append(row)
            for sk in sorted(groups_all.keys()):
                rows = groups_all[sk]
                metrics = _compute_metrics_for_rows(rows)
                metrics["slice_dimension"] = dim_name
                metrics["strategy_kind"] = sk
                metrics["label"] = "all"
                result.append(metrics)

    # Event-tag slices use effective_event_tags.  When annotations exist
    # (AI, auto, or manual), only annotated rows are used; otherwise all.
    tag_source_rows = annotated if has_annotated else observations
    tag_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in tag_source_rows:
        tags_str = row.get("effective_event_tags", "") or row.get("event_tags", "")
        if not tags_str:
            continue
        sk = row.get("strategy_kind", "")
        for tag in tags_str.split("|"):
            tag = tag.strip()
            if tag:
                tag_groups[(sk, tag)].append(row)

    for (sk, tag), rows in sorted(tag_groups.items()):
        if not rows:
            continue
        metrics = _compute_metrics_for_rows(rows)
        metrics["slice_dimension"] = "event_tag"
        metrics["strategy_kind"] = sk
        metrics["label"] = tag
        result.append(metrics)

    return result


def build_provider_health_summary(
    health_rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Summarize provider health for the week."""
    if not health_rows:
        return {
            "total_runs": 0,
            "providers": {},
            "fallback_adjustment_count": 0,
            "lag_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }

    total = len(health_rows)
    providers: dict[str, int] = defaultdict(int)
    fallback_count = 0
    lag_count = 0
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for row in health_rows:
        provider = row.get("provider_name", "unknown")
        providers[provider] += 1

        fb = row.get("used_fallback_adjustment", "").lower()
        if fb in ("true", "1", "yes"):
            fallback_count += 1

        try:
            lag = int(row.get("snapshot_lag_business_days", "0"))
            if lag > 0:
                lag_count += 1
        except (ValueError, TypeError):
            pass

        status = row.get("run_status", "").lower()
        if status in ("success", "ok"):
            success_count += 1
        elif status in ("failed", "error"):
            failed_count += 1
        elif status in ("skipped", "skip", "idempotent_skip"):
            skipped_count += 1

    return {
        "total_runs": total,
        "providers": dict(sorted(providers.items())),
        "fallback_adjustment_count": fallback_count,
        "lag_count": lag_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_weekly_report_v2(
    csv_output_dir: str,
    report_date_jst: datetime,
    *,
    business_day_count: int = 5,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    """Generate a v2 annotation-aware weekly report from CSV history.

    This function reads from persisted CSV artifacts only — no DB access,
    no forecast re-execution.  The existing ``run_weekly_report`` (v1) is
    not affected.

    Parameters
    ----------
    csv_output_dir:
        Root CSV output directory (containing ``history/``, ``analytics/``, etc.).
    report_date_jst:
        The reference date for the report (JST).
    business_day_count:
        Number of business days to include (default 5).
    generated_at_utc:
        Timestamp for the report generation.  Defaults to ``datetime.now(UTC)``.

    Returns
    -------
    dict[str, Any]
        The full v2 report data structure, suitable for JSON serialization.
    """
    if generated_at_utc is None:
        generated_at_utc = datetime.now(timezone.utc)

    week_start, week_end = _resolve_week_window(report_date_jst, business_day_count)

    # Load data
    observations = _load_labeled_observations_for_week(csv_output_dir, week_start, week_end)
    all_health_rows = _load_provider_health_rows(csv_output_dir)
    week_health_rows = _filter_provider_health_for_week(all_health_rows, week_start, week_end)

    # Build report sections
    coverage = build_annotation_coverage(observations)
    field_coverage = build_annotation_field_coverage(observations)
    strategy_metrics = build_strategy_metrics(observations)
    slice_metrics = build_slice_metrics(observations)
    provider_health = build_provider_health_summary(week_health_rows)

    from ugh_quantamental.fx_protocol.annotation_sources import (
        build_annotation_source_summary,
    )
    source_summary = build_annotation_source_summary(observations)
    et_source_summary = build_event_tag_source_summary(observations)

    obs_count = len(observations)
    # AI-first: annotated_analysis_ready when AI or auto annotations exist
    ai_or_auto_count = (
        source_summary.get("ai_annotated_count", 0)
        + source_summary.get("auto_annotated_count", 0)
    )

    # Collect model/prompt versions from source summary
    model_versions = source_summary.get("model_versions", [])
    prompt_versions = source_summary.get("prompt_versions", [])

    # Collect generated artifact paths placeholder (filled by export layer)
    return {
        "report_version": "v2",
        "generated_at_utc": generated_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "report_date_jst": report_date_jst.isoformat(),
        "week_window": {"start": week_start, "end": week_end},
        "business_day_count": business_day_count,
        "core_analysis_ready": obs_count > 0,
        "annotated_analysis_ready": ai_or_auto_count > 0,
        "annotation_coverage": coverage,
        "annotation_field_coverage": field_coverage,
        "annotation_source_summary": source_summary,
        "event_tag_slice_source_summary": et_source_summary,
        "ai_annotation_model_versions": model_versions,
        "ai_annotation_prompt_versions": prompt_versions,
        "strategy_metrics": strategy_metrics,
        "slice_metrics": slice_metrics,
        "provider_health_summary": provider_health,
        "observation_count": obs_count,
        "generated_artifact_paths": [],
    }
