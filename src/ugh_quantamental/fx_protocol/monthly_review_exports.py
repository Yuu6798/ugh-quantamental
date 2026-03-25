"""Monthly Review v1 — persistent artifact export helpers.

Separates file I/O from pure review computation so that the core
``run_monthly_review`` remains read-only and side-effect-free.

All output is derived from the monthly review dict — no engine recomputation.
Importable without SQLAlchemy.

Output layout:
    {csv_output_dir}/analytics/monthly/{YYYYMM}/monthly_review.json
    {csv_output_dir}/analytics/monthly/{YYYYMM}/monthly_review.md
    {csv_output_dir}/analytics/monthly/{YYYYMM}/monthly_strategy_metrics.csv
    {csv_output_dir}/analytics/monthly/{YYYYMM}/monthly_slice_metrics.csv
    {csv_output_dir}/analytics/monthly/{YYYYMM}/monthly_review_flags.csv
    {csv_output_dir}/analytics/monthly/latest/...  (mirror)
"""

from __future__ import annotations

import csv
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.monthly_review import (
    _resolve_month_window,
    run_monthly_review,
)
from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
    WEEKLY_SLICE_METRICS_FIELDNAMES,
    _is_in_week,
    _load_labeled_observations_for_week,
    _load_provider_health_rows,
    _filter_provider_health_for_week,
    _read_csv_rows,
)

logger = logging.getLogger(__name__)

_JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# CSV column definitions for monthly artifacts
# ---------------------------------------------------------------------------

MONTHLY_STRATEGY_METRICS_FIELDNAMES: tuple[str, ...] = (
    "strategy_kind",
    "forecast_count",
    "direction_hit_count",
    "direction_hit_rate",
    "range_hit_count",
    "range_hit_rate",
    "state_proxy_hit_count",
    "state_proxy_hit_rate",
    "mean_abs_close_error_bp",
    "median_abs_close_error_bp",
    "mean_abs_magnitude_error_bp",
    "median_abs_magnitude_error_bp",
)

MONTHLY_REVIEW_FLAGS_FIELDNAMES: tuple[str, ...] = (
    "flag",
    "reason",
)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


def export_monthly_review_json(
    review: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``monthly_review.json`` and return the absolute path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "monthly_review.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(review, fh, ensure_ascii=False, indent=2, default=str)
        fh.write("\n")
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------


def _fmt_pct(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(value)


def _fmt_bp(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.1f}"
    except (ValueError, TypeError):
        return str(value)


def _fmt_delta(value: Any, unit: str = "") -> str:
    if value is None or value == "":
        return "-"
    try:
        v = float(value)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.2f}{unit}"
    except (ValueError, TypeError):
        return str(value)


def build_monthly_review_md(review: dict[str, Any]) -> str:
    """Build human-readable monthly review markdown."""
    lines: list[str] = []
    pair = review.get("pair", "USDJPY")

    # Header
    lines.append(f"# FX Monthly Review v1 — {pair}")
    lines.append("")
    lines.append(f"Generated: {review.get('review_generated_at_jst', 'N/A')}")
    lines.append(
        f"Window: {review.get('requested_window_count', 0)} business days requested, "
        f"{review.get('included_window_count', 0)} included, "
        f"{review.get('missing_window_count', 0)} missing"
    )
    lines.append("")

    # Monthly Summary
    lines.append("## Monthly Summary")
    lines.append("")
    recommendation = review.get("recommendation_summary", "")
    if recommendation:
        lines.append(f"> {recommendation}")
        lines.append("")

    # Review Flags
    flags = review.get("review_flags", [])
    if flags:
        lines.append("## Review Flags")
        lines.append("")
        for f in flags:
            lines.append(f"- **{f.get('flag', '')}**: {f.get('reason', '')}")
        lines.append("")

    # Strategy Performance
    strats = review.get("monthly_strategy_metrics", [])
    lines.append("## Strategy Performance")
    lines.append("")
    if strats:
        lines.append(
            "| Strategy | N | Dir Hit | Dir Rate | Range Rate "
            "| State Rate | Mean Err | Med Err | Mean Mag | Med Mag |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for s in strats:
            lines.append(
                f"| {s.get('strategy_kind', '')} "
                f"| {s.get('forecast_count', 0)} "
                f"| {s.get('direction_hit_count', 0)} "
                f"| {_fmt_pct(s.get('direction_hit_rate'))} "
                f"| {_fmt_pct(s.get('range_hit_rate'))} "
                f"| {_fmt_pct(s.get('state_proxy_hit_rate'))} "
                f"| {_fmt_bp(s.get('mean_abs_close_error_bp'))} "
                f"| {_fmt_bp(s.get('median_abs_close_error_bp'))} "
                f"| {_fmt_bp(s.get('mean_abs_magnitude_error_bp'))} "
                f"| {_fmt_bp(s.get('median_abs_magnitude_error_bp'))} |"
            )
        lines.append("")
    else:
        lines.append("No strategy metrics available.")
        lines.append("")

    # Baseline Comparisons
    comps = review.get("monthly_baseline_comparisons", [])
    if comps:
        lines.append("## Baseline Comparisons (delta vs UGH)")
        lines.append("")
        lines.append(
            "| Baseline | Dir Acc Delta | Close Err Delta | Mag Err Delta | State Delta |"
        )
        lines.append("|---|---|---|---|---|")
        for c in comps:
            lines.append(
                f"| {c.get('baseline_strategy_kind', '')} "
                f"| {_fmt_delta(c.get('direction_accuracy_delta_vs_ugh'))} "
                f"| {_fmt_delta(c.get('mean_abs_close_error_bp_delta_vs_ugh'), ' bp')} "
                f"| {_fmt_delta(c.get('mean_abs_magnitude_error_bp_delta_vs_ugh'), ' bp')} "
                f"| {_fmt_delta(c.get('state_proxy_hit_rate_delta_vs_ugh'))} |"
            )
        lines.append("")

    # State Metrics
    state_metrics = review.get("monthly_state_metrics", [])
    if state_metrics:
        lines.append("## State Metrics (UGH)")
        lines.append("")
        lines.append("| State | N | Dir Rate | Mean Err |")
        lines.append("|---|---|---|---|")
        for s in state_metrics:
            lines.append(
                f"| {s.get('dominant_state', '')} "
                f"| {s.get('forecast_count', 0)} "
                f"| {_fmt_pct(s.get('direction_hit_rate'))} "
                f"| {_fmt_bp(s.get('mean_abs_close_error_bp'))} |"
            )
        lines.append("")

    # Regime Metrics
    regime_metrics = review.get("monthly_regime_metrics", [])
    if regime_metrics:
        lines.append("## Regime Analysis (UGH, confirmed annotations)")
        lines.append("")
        lines.append("| Regime | N | Dir Rate | Mean Err |")
        lines.append("|---|---|---|---|")
        for r in regime_metrics:
            lines.append(
                f"| {r.get('regime_label', '')} "
                f"| {r.get('observation_count', 0)} "
                f"| {_fmt_pct(r.get('direction_hit_rate'))} "
                f"| {_fmt_bp(r.get('mean_abs_close_error_bp'))} |"
            )
        lines.append("")

    # Volatility Metrics
    vol_metrics = review.get("monthly_volatility_metrics", [])
    if vol_metrics:
        lines.append("## Volatility Analysis (UGH, confirmed annotations)")
        lines.append("")
        lines.append("| Volatility | N | Dir Rate | Mean Err |")
        lines.append("|---|---|---|---|")
        for v in vol_metrics:
            lines.append(
                f"| {v.get('volatility_label', '')} "
                f"| {v.get('observation_count', 0)} "
                f"| {_fmt_pct(v.get('direction_hit_rate'))} "
                f"| {_fmt_bp(v.get('mean_abs_close_error_bp'))} |"
            )
        lines.append("")

    # Intervention Metrics
    int_metrics = review.get("monthly_intervention_metrics", [])
    if int_metrics:
        lines.append("## Intervention Risk Analysis (UGH, confirmed annotations)")
        lines.append("")
        lines.append("| Intervention Risk | N | Dir Rate | Mean Err |")
        lines.append("|---|---|---|---|")
        for i in int_metrics:
            lines.append(
                f"| {i.get('intervention_risk', '')} "
                f"| {i.get('observation_count', 0)} "
                f"| {_fmt_pct(i.get('direction_hit_rate'))} "
                f"| {_fmt_bp(i.get('mean_abs_close_error_bp'))} |"
            )
        lines.append("")

    # Event Tag Metrics
    tag_metrics = review.get("monthly_event_tag_metrics", [])
    if tag_metrics:
        lines.append("## Event Tag Analysis (UGH, confirmed annotations)")
        lines.append("")
        lines.append("| Event Tag | N | Dir Rate | Mean Err |")
        lines.append("|---|---|---|---|")
        for t in tag_metrics:
            lines.append(
                f"| {t.get('event_tag', '')} "
                f"| {t.get('observation_count', 0)} "
                f"| {_fmt_pct(t.get('direction_hit_rate'))} "
                f"| {_fmt_bp(t.get('mean_abs_close_error_bp'))} |"
            )
        lines.append("")

    # Provider Health
    ph = review.get("provider_health_summary", {})
    lines.append("## Provider Health Summary")
    lines.append("")
    lines.append(f"- **Total runs**: {ph.get('total_runs', 0)}")
    lines.append(f"- **Success**: {ph.get('success_count', 0)}")
    lines.append(f"- **Failed**: {ph.get('failed_count', 0)}")
    lines.append(f"- **Skipped**: {ph.get('skipped_count', 0)}")
    lines.append(f"- **Fallback adjustments**: {ph.get('fallback_adjustment_count', 0)}")
    lines.append(f"- **Lagged snapshots**: {ph.get('lagged_snapshot_count', 0)}")
    providers = ph.get("providers", {})
    if providers:
        lines.append(
            f"- **Providers**: {', '.join(f'{k} ({v})' for k, v in providers.items())}"
        )
    lines.append("")

    # Annotation Coverage
    cov = review.get("annotation_coverage_summary", {})
    lines.append("## Annotation Coverage")
    lines.append("")
    lines.append(f"- **Total observations**: {cov.get('total_observations', 0)}")
    lines.append(f"- **Confirmed**: {cov.get('confirmed_count', 0)}")
    lines.append(f"- **Pending**: {cov.get('pending_count', 0)}")
    lines.append(f"- **Unlabeled**: {cov.get('unlabeled_count', 0)}")
    lines.append(f"- **Coverage rate**: {_fmt_pct(cov.get('annotation_coverage_rate', 0))}")
    lines.append("")

    # Representative Cases
    successes = review.get("representative_successes", [])
    if successes:
        lines.append("## Representative Successes")
        lines.append("")
        for i, c in enumerate(successes, 1):
            lines.append(
                f"{i}. **{c.get('as_of_jst', '')}** — "
                f"Predicted {c.get('forecast_direction', '')} "
                f"({c.get('expected_close_change_bp', '')} bp), "
                f"Realized {c.get('realized_direction', '')} "
                f"({c.get('realized_close_change_bp', '')} bp), "
                f"Error: {_fmt_bp(c.get('close_error_bp'))} bp"
            )
        lines.append("")

    failures = review.get("representative_failures", [])
    if failures:
        lines.append("## Representative Failures")
        lines.append("")
        for i, c in enumerate(failures, 1):
            lines.append(
                f"{i}. **{c.get('as_of_jst', '')}** — "
                f"Predicted {c.get('forecast_direction', '')} "
                f"({c.get('expected_close_change_bp', '')} bp), "
                f"Realized {c.get('realized_direction', '')} "
                f"({c.get('realized_close_change_bp', '')} bp), "
                f"Error: {_fmt_bp(c.get('close_error_bp'))} bp"
            )
        lines.append("")

    # Recommendation Summary
    lines.append("## Recommendation Summary")
    lines.append("")
    lines.append(review.get("recommendation_summary", "N/A"))
    lines.append("")

    # Notes
    lines.append("---")
    lines.append("")
    lines.append("*This report is generated from persisted CSV artifacts only. "
                 "No forecast logic was re-executed. "
                 "Internal UGH/baseline/engine logic is unchanged.*")
    lines.append("")

    return "\n".join(lines)


def export_monthly_review_md(
    review: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``monthly_review.md`` and return the absolute path."""
    os.makedirs(output_dir, exist_ok=True)
    content = build_monthly_review_md(review)
    path = os.path.join(output_dir, "monthly_review.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# CSV exports
# ---------------------------------------------------------------------------


def _write_csv(
    path: str,
    rows: list[dict[str, Any]],
    fieldnames: tuple[str, ...],
) -> str:
    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return abs_path


def export_monthly_strategy_metrics_csv(
    review: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``monthly_strategy_metrics.csv`` and return the absolute path."""
    rows = review.get("monthly_strategy_metrics", [])
    path = os.path.join(output_dir, "monthly_strategy_metrics.csv")
    return _write_csv(path, rows, MONTHLY_STRATEGY_METRICS_FIELDNAMES)


def export_monthly_slice_metrics_csv(
    review: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``monthly_slice_metrics.csv`` and return the absolute path."""
    rows = review.get("monthly_slice_metrics", [])
    path = os.path.join(output_dir, "monthly_slice_metrics.csv")
    return _write_csv(path, rows, WEEKLY_SLICE_METRICS_FIELDNAMES)


def export_monthly_review_flags_csv(
    review: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``monthly_review_flags.csv`` and return the absolute path."""
    rows = review.get("review_flags", [])
    path = os.path.join(output_dir, "monthly_review_flags.csv")
    return _write_csv(path, rows, MONTHLY_REVIEW_FLAGS_FIELDNAMES)


# ---------------------------------------------------------------------------
# Full export orchestrator
# ---------------------------------------------------------------------------


def export_monthly_review_artifacts(
    review: dict[str, Any],
    csv_output_dir: str,
    month_str: str,
) -> dict[str, str]:
    """Export all monthly review artifacts to both dated and latest directories.

    Parameters
    ----------
    review:
        The monthly review dict from ``run_monthly_review``.
    csv_output_dir:
        Root CSV output directory.
    month_str:
        YYYYMM string for the dated directory.

    Returns
    -------
    dict[str, str]
        Artifact keys to absolute paths.
    """
    base = os.path.abspath(csv_output_dir)
    dated_dir = os.path.join(base, "analytics", "monthly", month_str)
    latest_dir = os.path.join(base, "analytics", "monthly", "latest")

    paths: dict[str, str] = {}

    # Export to dated directory
    paths["monthly_review_json"] = export_monthly_review_json(review, dated_dir)
    paths["monthly_review_md"] = export_monthly_review_md(review, dated_dir)
    paths["monthly_strategy_metrics_csv"] = export_monthly_strategy_metrics_csv(
        review, dated_dir
    )
    paths["monthly_slice_metrics_csv"] = export_monthly_slice_metrics_csv(review, dated_dir)
    paths["monthly_review_flags_csv"] = export_monthly_review_flags_csv(review, dated_dir)

    # Update review with artifact paths
    review["generated_artifact_paths"] = list(paths.values())

    # Re-export JSON with paths included
    paths["monthly_review_json"] = export_monthly_review_json(review, dated_dir)

    # Mirror to latest/
    os.makedirs(latest_dir, exist_ok=True)
    for filename in [
        "monthly_review.json",
        "monthly_review.md",
        "monthly_strategy_metrics.csv",
        "monthly_slice_metrics.csv",
        "monthly_review_flags.csv",
    ]:
        src = os.path.join(dated_dir, filename)
        dst = os.path.join(latest_dir, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    return paths


# ---------------------------------------------------------------------------
# Enrichment helpers (populate fields missing from labeled_observations.csv)
# ---------------------------------------------------------------------------


def _build_forecast_lookup(
    csv_output_dir: str,
    month_start: str,
    month_end: str,
) -> dict[tuple[str, str], dict[str, str]]:
    """Build a lookup of (as_of_jst_datestr, strategy_kind) -> forecast row.

    Scans ``history/`` for forecast CSVs to extract ``dominant_state`` and ``pair``
    which are not included in ``labeled_observations.csv``.
    """
    base = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(base, "history")
    if not os.path.isdir(history_dir):
        return {}

    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for date_dir in sorted(os.listdir(history_dir)):
        # Quick date range check on directory name (YYYYMMDD)
        if len(date_dir) == 8 and date_dir.isdigit():
            if not _is_in_week(date_dir, month_start, month_end):
                continue

        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            forecast_csv = os.path.join(date_path, batch_dir, "forecast.csv")
            if not os.path.isfile(forecast_csv):
                continue
            for row in _read_csv_rows(forecast_csv):
                as_of = row.get("as_of_jst", "")
                date_str = as_of[:10].replace("-", "") if len(as_of) >= 10 else ""
                sk = row.get("strategy_kind", "")
                if date_str and sk:
                    lookup[(date_str, sk)] = row
    return lookup


def _enrich_observations_with_forecast_data(
    observations: list[dict[str, str]],
    forecast_lookup: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, str]]:
    """Enrich observation rows with ``dominant_state`` and ``pair`` from forecast history.

    ``labeled_observations.csv`` does not include these columns, so we populate
    them from the original forecast CSVs to enable state-level monthly analysis
    and pair filtering.
    """
    for obs in observations:
        as_of = obs.get("as_of_jst", "")
        date_str = as_of[:10].replace("-", "") if len(as_of) >= 10 else ""
        sk = obs.get("strategy_kind", "")
        fc = forecast_lookup.get((date_str, sk), {})

        if not obs.get("dominant_state"):
            obs["dominant_state"] = fc.get("dominant_state", "")
        if not obs.get("pair"):
            obs["pair"] = fc.get("pair", "")

    return observations


def _filter_observations_by_pair(
    observations: list[dict[str, str]],
    pair: str,
) -> list[dict[str, str]]:
    """Filter observations to only include rows matching the given pair.

    Rows without a ``pair`` field are included (conservative: don't drop data
    when the field is unavailable).
    """
    return [
        r for r in observations
        if not r.get("pair") or r["pair"].upper() == pair.upper()
    ]


# ---------------------------------------------------------------------------
# Data loading + review orchestrator (reads CSV, calls pure functions)
# ---------------------------------------------------------------------------


def rebuild_monthly_review(
    csv_output_dir: str,
    review_date_jst: datetime,
    *,
    pair: str = "USDJPY",
    business_day_count: int = 20,
    max_examples: int = 3,
    include_annotations: bool = True,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    """Load data from CSV artifacts and generate a full monthly review.

    This is the high-level orchestrator that:
    1. Resolves the monthly window
    2. Loads labeled observations and provider health from CSV
    3. Calls ``run_monthly_review`` (pure function)
    4. Exports all artifacts (JSON, MD, CSV)

    Does NOT re-run forecast engine.

    Parameters
    ----------
    csv_output_dir:
        Root CSV output directory.
    review_date_jst:
        The reference date for the review (JST).
    pair:
        Currency pair.
    business_day_count:
        Number of business days in the monthly window.
    max_examples:
        Maximum representative success/failure examples.
    include_annotations:
        Whether to include annotation-aware metrics.
    generated_at_utc:
        Timestamp for the review generation.

    Returns
    -------
    dict[str, Any]
        The full monthly review dict with ``generated_artifact_paths`` populated.
    """
    if generated_at_utc is None:
        generated_at_utc = datetime.now(timezone.utc)

    # Step 0: Remove stale labeled_observations.csv so that if rebuild fails,
    # data loading cannot silently use outdated data.
    stale_obs = os.path.join(
        os.path.abspath(csv_output_dir), "analytics", "labeled_observations.csv"
    )
    if os.path.isfile(stale_obs):
        os.remove(stale_obs)

    # Step 1: Rebuild annotation analytics to ensure fresh observations.
    from ugh_quantamental.fx_protocol.analytics_rebuild import rebuild_annotation_analytics

    analytics_result = rebuild_annotation_analytics(
        csv_output_dir, generated_at_utc=generated_at_utc
    )

    if analytics_result.get("labeled_observations_path") is None:
        logger.warning(
            "labeled_observations rebuild produced no output; "
            "monthly review will run on empty observation set."
        )

    # Resolve window
    month_start, month_end = _resolve_month_window(review_date_jst, business_day_count)

    # Load data (reuse weekly data loading helpers)
    observations = _load_labeled_observations_for_week(csv_output_dir, month_start, month_end)
    all_health_rows = _load_provider_health_rows(csv_output_dir)
    month_health_rows = _filter_provider_health_for_week(all_health_rows, month_start, month_end)

    # Enrich observations with dominant_state and pair from forecast history
    # (labeled_observations.csv does not include these columns)
    forecast_lookup = _build_forecast_lookup(csv_output_dir, month_start, month_end)
    observations = _enrich_observations_with_forecast_data(observations, forecast_lookup)

    # Filter observations to the requested pair
    observations = _filter_observations_by_pair(observations, pair)

    # Determine review_generated_at_jst
    if review_date_jst.tzinfo is not None:
        rg_jst = review_date_jst.astimezone(_JST)
    else:
        rg_jst = review_date_jst.replace(tzinfo=_JST)

    # Generate review
    review = run_monthly_review(
        observations,
        month_health_rows,
        pair=pair,
        review_generated_at_jst=rg_jst,
        business_day_count=business_day_count,
        max_examples=max_examples,
        include_annotations=include_annotations,
    )

    # Add slice metrics to review for CSV export
    if include_annotations:
        from ugh_quantamental.fx_protocol.monthly_review import compute_monthly_slice_metrics

        review["monthly_slice_metrics"] = compute_monthly_slice_metrics(observations)

    # Determine month string for directory
    month_str = rg_jst.strftime("%Y%m")

    # Export artifacts
    export_monthly_review_artifacts(review, csv_output_dir, month_str)

    return review
