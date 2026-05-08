"""Weekly Report v2 — persistent artifact export helpers.

Separates file I/O from pure report computation so that the core
``run_weekly_report_v2`` remains read-only and side-effect-free.

All output is derived from the v2 report dict — no engine recomputation.
Importable without SQLAlchemy.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any

from ugh_quantamental.fx_protocol.csv_utils import write_csv_rows
from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
    WEEKLY_SLICE_METRICS_FIELDNAMES,
    WEEKLY_STRATEGY_METRICS_FIELDNAMES,
)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


def export_weekly_report_json(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_report.json`` and return the absolute path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "weekly_report.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2, default=str)
        fh.write("\n")
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------


def _fmt_pct(value: Any) -> str:
    """Format a rate value as percentage string."""
    if value == "" or value is None:
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(value)


def _fmt_bp(value: Any) -> str:
    """Format a basis-point value."""
    if value == "" or value is None:
        return "-"
    try:
        return f"{float(value):.1f}"
    except (ValueError, TypeError):
        return str(value)


def build_weekly_report_md(report: dict[str, Any]) -> str:
    """Build human-readable weekly report markdown from the v2 report dict."""
    lines: list[str] = []
    week = report.get("week_window", {})

    # Header
    lines.append(f"# FX Weekly Report v2 — {week.get('start', '?')} to {week.get('end', '?')}")
    lines.append("")
    lines.append(f"Generated: {report.get('generated_at_utc', 'N/A')}")
    lines.append(f"Report date (JST): {report.get('report_date_jst', 'N/A')}")
    lines.append(f"Business days: {report.get('business_day_count', 'N/A')}")
    lines.append(f"Total observations: {report.get('observation_count', 0)}")
    lines.append(
        f"Core analysis ready: {'Yes' if report.get('core_analysis_ready') else 'No'}"
    )
    lines.append(
        f"Annotated analysis ready: "
        f"{'Yes' if report.get('annotated_analysis_ready') else 'No'}"
    )
    lines.append("")

    # --- Core Analysis (always available) ---
    lines.append("## Core Analysis")
    lines.append("")

    # Strategy metrics
    strats = report.get("strategy_metrics", [])
    lines.append("### Strategy Performance")
    lines.append("")
    if strats:
        lines.append(
            "| Strategy | Obs | Dir Hit | Dir Rate | Range Rate "
            "| State Rate | Mean Err (bp) | Median Err (bp) |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for s in strats:
            lines.append(
                f"| {s.get('strategy_kind', '')} "
                f"| {s.get('observation_count', 0)} "
                f"| {s.get('direction_hit_count', 0)} "
                f"| {_fmt_pct(s.get('direction_hit_rate', ''))} "
                f"| {_fmt_pct(s.get('range_hit_rate', ''))} "
                f"| {_fmt_pct(s.get('state_proxy_hit_rate', ''))} "
                f"| {_fmt_bp(s.get('mean_close_error_bp', ''))} "
                f"| {_fmt_bp(s.get('median_close_error_bp', ''))} |"
            )
        lines.append("")
    else:
        lines.append("No strategy metrics available.")
        lines.append("")

    # Event-tag analysis (uses effective_event_tags, available without annotations)
    slices = report.get("slice_metrics", [])
    event_tag_slices = [s for s in slices if s.get("slice_dimension") == "event_tag"]
    if event_tag_slices:
        et_summary = report.get("event_tag_slice_source_summary", {})
        source_parts = [
            f"{k}: {v}" for k, v in sorted(et_summary.items()) if v > 0
        ]
        source_note = f" (sources: {', '.join(source_parts)})" if source_parts else ""
        lines.append(f"### Event-Tag Analysis{source_note}")
        lines.append("")
        lines.append(
            "| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |"
        )
        lines.append("|---|---|---|---|---|---|")
        for s in event_tag_slices:
            lines.append(
                f"| {s.get('strategy_kind', '')} "
                f"| {s.get('label', '')} "
                f"| {s.get('observation_count', 0)} "
                f"| {_fmt_pct(s.get('direction_hit_rate', ''))} "
                f"| {_fmt_pct(s.get('range_hit_rate', ''))} "
                f"| {_fmt_bp(s.get('mean_close_error_bp', ''))} |"
            )
        lines.append("")

    # --- AI Annotation Layer ---
    src_summary = report.get("annotation_source_summary", {})
    ai_count = src_summary.get("ai_annotated_count", 0)
    auto_count = src_summary.get("auto_annotated_count", 0)
    manual_count = src_summary.get("manual_annotated_count", 0)
    unannotated = src_summary.get("unannotated_count", 0)

    lines.append("## AI Annotation Layer")
    lines.append("")
    lines.append(f"- **AI annotated**: {ai_count}")
    lines.append(f"- **Auto annotated**: {auto_count}")
    lines.append(f"- **Manual compat**: {manual_count}")
    lines.append(f"- **Unannotated**: {unannotated}")

    model_vs = report.get("ai_annotation_model_versions", [])
    if model_vs:
        lines.append(f"- **Model versions**: {', '.join(model_vs)}")
    prompt_vs = report.get("ai_annotation_prompt_versions", [])
    if prompt_vs:
        lines.append(f"- **Prompt versions**: {', '.join(prompt_vs)}")

    ev_refs = src_summary.get("evidence_ref_count", 0)
    if ev_refs:
        lines.append(f"- **Evidence references**: {ev_refs}")

    annotated_ready = report.get("annotated_analysis_ready", False)
    lines.append(
        f"- **Slices interpretable**: {'Yes' if annotated_ready else 'No'}"
    )
    lines.append("")

    # Field-level coverage table
    field_cov = report.get("annotation_field_coverage", {})
    if field_cov:
        lines.append("### Field-Level Coverage")
        lines.append("")
        lines.append(
            "| Field | AI | Auto | Manual | Effective | Missing |"
        )
        lines.append("|---|---|---|---|---|---|")
        for field_name in (
            "regime_label", "event_tags", "volatility_label",
            "intervention_risk", "failure_reason",
        ):
            fc = field_cov.get(field_name, {})
            lines.append(
                f"| {field_name} "
                f"| {fc.get('ai_populated_count', 0)} "
                f"| {fc.get('auto_populated_count', 0)} "
                f"| {fc.get('manual_populated_count', 0)} "
                f"| {fc.get('effective_populated_count', 0)} "
                f"| {fc.get('missing_count', 0)} |"
            )
        lines.append("")

    # --- Annotation-Dependent Analysis ---
    annotated_slices = [
        s for s in slices if s.get("slice_dimension") != "event_tag"
    ]
    if report.get("annotated_analysis_ready"):
        lines.append("## Annotation-Dependent Analysis")
        lines.append("")

        # Group by dimension
        dims: dict[str, list[dict[str, Any]]] = {}
        for s in annotated_slices:
            dim = s.get("slice_dimension", "unknown")
            dims.setdefault(dim, []).append(s)

        for dim in sorted(dims.keys()):
            dim_label = dim.replace("_", " ").title()
            lines.append(f"### {dim_label}")
            lines.append("")
            lines.append(
                "| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |"
            )
            lines.append("|---|---|---|---|---|---|")
            for s in dims[dim]:
                lines.append(
                    f"| {s.get('strategy_kind', '')} "
                    f"| {s.get('label', '')} "
                    f"| {s.get('observation_count', 0)} "
                    f"| {_fmt_pct(s.get('direction_hit_rate', ''))} "
                    f"| {_fmt_pct(s.get('range_hit_rate', ''))} "
                    f"| {_fmt_bp(s.get('mean_close_error_bp', ''))} |"
                )
            lines.append("")
    elif annotated_slices:
        lines.append("## Annotation-Dependent Analysis")
        lines.append("")
        lines.append(
            "> No confirmed annotations available. "
            "Regime, volatility, and intervention-risk slices show aggregate "
            "metrics per strategy (label='all'). Add confirmed annotations "
            "for labeled breakdown."
        )
        lines.append("")

        dims = {}
        for s in annotated_slices:
            dim = s.get("slice_dimension", "unknown")
            dims.setdefault(dim, []).append(s)

        for dim in sorted(dims.keys()):
            dim_label = dim.replace("_", " ").title()
            lines.append(f"### {dim_label}")
            lines.append("")
            lines.append(
                "| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |"
            )
            lines.append("|---|---|---|---|---|---|")
            for s in dims[dim]:
                lines.append(
                    f"| {s.get('strategy_kind', '')} "
                    f"| {s.get('label', '')} "
                    f"| {s.get('observation_count', 0)} "
                    f"| {_fmt_pct(s.get('direction_hit_rate', ''))} "
                    f"| {_fmt_pct(s.get('range_hit_rate', ''))} "
                    f"| {_fmt_bp(s.get('mean_close_error_bp', ''))} |"
                )
            lines.append("")

    # Provider health summary
    ph = report.get("provider_health_summary", {})
    lines.append("## Provider Health Summary")
    lines.append("")
    lines.append(f"- **Total runs**: {ph.get('total_runs', 0)}")
    lines.append(f"- **Success**: {ph.get('success_count', 0)}")
    lines.append(f"- **Failed**: {ph.get('failed_count', 0)}")
    lines.append(f"- **Skipped**: {ph.get('skipped_count', 0)}")
    lines.append(f"- **Fallback adjustments**: {ph.get('fallback_adjustment_count', 0)}")
    lines.append(f"- **Lag occurrences**: {ph.get('lag_count', 0)}")
    providers = ph.get("providers", {})
    if providers:
        lines.append(
            f"- **Providers used**: "
            f"{', '.join(f'{k} ({v})' for k, v in providers.items())}"
        )
    lines.append("")

    # Notes
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is generated from persisted CSV artifacts only.")
    lines.append("- No forecast logic was re-executed.")
    lines.append("- Core analysis (strategy performance) is always available.")
    lines.append(
        "- AI annotations are the primary source for slice analysis."
    )
    lines.append(
        "- Manual annotations are optional compatibility inputs."
    )
    lines.append("")

    return "\n".join(lines)


def export_weekly_report_md(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_report.md`` and return the absolute path."""
    os.makedirs(output_dir, exist_ok=True)
    content = build_weekly_report_md(report)
    path = os.path.join(output_dir, "weekly_report.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# CSV exports
# ---------------------------------------------------------------------------


def export_weekly_strategy_metrics_csv(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_strategy_metrics.csv`` and return the absolute path."""
    rows = report.get("strategy_metrics", [])
    path = os.path.join(output_dir, "weekly_strategy_metrics.csv")
    return write_csv_rows(path, rows, WEEKLY_STRATEGY_METRICS_FIELDNAMES, extrasaction="ignore")


def export_weekly_slice_metrics_csv(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_slice_metrics.csv`` and return the absolute path."""
    rows = report.get("slice_metrics", [])
    path = os.path.join(output_dir, "weekly_slice_metrics.csv")
    return write_csv_rows(path, rows, WEEKLY_SLICE_METRICS_FIELDNAMES, extrasaction="ignore")


WEEKLY_ANNOTATION_COVERAGE_FIELDNAMES: tuple[str, ...] = (
    "field",
    "total_observations",
    "ai_populated_count",
    "ai_populated_rate",
    "auto_populated_count",
    "auto_populated_rate",
    "manual_populated_count",
    "manual_populated_rate",
    "effective_populated_count",
    "effective_populated_rate",
    "missing_count",
    "missing_rate",
)


def export_weekly_annotation_coverage_csv(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_annotation_coverage.csv`` and return the absolute path."""
    field_cov = report.get("annotation_field_coverage", {})
    rows: list[dict[str, Any]] = []
    for field_name in (
        "regime_label", "event_tags", "volatility_label",
        "intervention_risk", "failure_reason",
    ):
        fc = field_cov.get(field_name, {})
        row = {"field": field_name}
        row.update(fc)
        rows.append(row)
    path = os.path.join(output_dir, "weekly_annotation_coverage.csv")
    return write_csv_rows(path, rows, WEEKLY_ANNOTATION_COVERAGE_FIELDNAMES, extrasaction="ignore")


WEEKLY_AI_ANNOTATION_SUMMARY_FIELDNAMES: tuple[str, ...] = (
    "metric",
    "value",
)


def export_weekly_ai_annotation_summary_csv(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_ai_annotation_summary.csv`` and return the absolute path."""
    src = report.get("annotation_source_summary", {})
    rows: list[dict[str, Any]] = [
        {"metric": "total_observations", "value": src.get("total_observations", 0)},
        {"metric": "ai_annotated_count", "value": src.get("ai_annotated_count", 0)},
        {"metric": "auto_annotated_count", "value": src.get("auto_annotated_count", 0)},
        {"metric": "manual_annotated_count", "value": src.get("manual_annotated_count", 0)},
        {"metric": "unannotated_count", "value": src.get("unannotated_count", 0)},
        {"metric": "evidence_ref_count", "value": src.get("evidence_ref_count", 0)},
    ]
    for mv in report.get("ai_annotation_model_versions", []):
        rows.append({"metric": "model_version", "value": mv})
    for pv in report.get("ai_annotation_prompt_versions", []):
        rows.append({"metric": "prompt_version", "value": pv})
    path = os.path.join(output_dir, "weekly_ai_annotation_summary.csv")
    return write_csv_rows(path, rows, WEEKLY_AI_ANNOTATION_SUMMARY_FIELDNAMES, extrasaction="ignore")


# ---------------------------------------------------------------------------
# Full export orchestrator
# ---------------------------------------------------------------------------


def export_weekly_report_artifacts(
    report: dict[str, Any],
    csv_output_dir: str,
    date_str: str,
) -> dict[str, str]:
    """Export all weekly v2 artifacts to both dated and latest directories.

    Layout:
        {csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_report.json
        {csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_report.md
        {csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_strategy_metrics.csv
        {csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_slice_metrics.csv
        {csv_output_dir}/analytics/weekly/latest/...

    Returns a dict of artifact keys to absolute paths.
    """
    base = os.path.abspath(csv_output_dir)
    dated_dir = os.path.join(base, "analytics", "weekly", date_str)
    latest_dir = os.path.join(base, "analytics", "weekly", "latest")

    paths: dict[str, str] = {}

    # Export to dated directory
    paths["weekly_report_json"] = export_weekly_report_json(report, dated_dir)
    paths["weekly_report_md"] = export_weekly_report_md(report, dated_dir)
    paths["weekly_strategy_metrics_csv"] = export_weekly_strategy_metrics_csv(
        report, dated_dir,
    )
    paths["weekly_slice_metrics_csv"] = export_weekly_slice_metrics_csv(
        report, dated_dir,
    )
    paths["weekly_annotation_coverage_csv"] = export_weekly_annotation_coverage_csv(
        report, dated_dir,
    )
    paths["weekly_ai_annotation_summary_csv"] = export_weekly_ai_annotation_summary_csv(
        report, dated_dir,
    )

    # Update report with artifact paths
    report["generated_artifact_paths"] = list(paths.values())

    # Re-export JSON with paths included
    paths["weekly_report_json"] = export_weekly_report_json(report, dated_dir)

    # Mirror to latest/
    os.makedirs(latest_dir, exist_ok=True)
    for filename in [
        "weekly_report.json", "weekly_report.md",
        "weekly_strategy_metrics.csv", "weekly_slice_metrics.csv",
        "weekly_annotation_coverage.csv",
        "weekly_ai_annotation_summary.csv",
    ]:
        src = os.path.join(dated_dir, filename)
        dst = os.path.join(latest_dir, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    return paths
