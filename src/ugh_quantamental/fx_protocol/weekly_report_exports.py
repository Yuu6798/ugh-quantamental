"""Weekly Report v2 — persistent artifact export helpers.

Separates file I/O from pure report computation so that the core
``run_weekly_report_v2`` remains read-only and side-effect-free.

All output is derived from the v2 report dict — no engine recomputation.
Importable without SQLAlchemy.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from typing import Any

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
    lines.append("")

    # Annotation coverage
    cov = report.get("annotation_coverage", {})
    lines.append("## Annotation Coverage")
    lines.append("")
    lines.append(f"- **Total observations**: {cov.get('total_observations', 0)}")
    lines.append(f"- **Confirmed**: {cov.get('confirmed_annotation_count', 0)}")
    lines.append(f"- **Pending**: {cov.get('pending_annotation_count', 0)}")
    lines.append(f"- **Unlabeled**: {cov.get('unlabeled_count', 0)}")
    rate = cov.get("annotation_coverage_rate", 0)
    lines.append(f"- **Coverage rate**: {_fmt_pct(rate)}")
    lines.append("")

    # Strategy metrics
    strats = report.get("strategy_metrics", [])
    lines.append("## Strategy Performance")
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

    # Slice metrics summary
    slices = report.get("slice_metrics", [])
    if slices:
        lines.append("## Annotation-Aware Slice Analysis")
        lines.append("")

        # Group by dimension
        dims: dict[str, list[dict[str, Any]]] = {}
        for s in slices:
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
        lines.append(f"- **Providers used**: {', '.join(f'{k} ({v})' for k, v in providers.items())}")
    lines.append("")

    # Notes
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is generated from persisted CSV artifacts only.")
    lines.append("- No forecast logic was re-executed.")
    lines.append("- Confirmed manual annotations are used for labeled analysis.")
    lines.append("- Unlabeled observations are shown separately in slice metrics.")
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


def export_weekly_strategy_metrics_csv(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_strategy_metrics.csv`` and return the absolute path."""
    rows = report.get("strategy_metrics", [])
    path = os.path.join(output_dir, "weekly_strategy_metrics.csv")
    return _write_csv(path, rows, WEEKLY_STRATEGY_METRICS_FIELDNAMES)


def export_weekly_slice_metrics_csv(
    report: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``weekly_slice_metrics.csv`` and return the absolute path."""
    rows = report.get("slice_metrics", [])
    path = os.path.join(output_dir, "weekly_slice_metrics.csv")
    return _write_csv(path, rows, WEEKLY_SLICE_METRICS_FIELDNAMES)


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
    paths["weekly_strategy_metrics_csv"] = export_weekly_strategy_metrics_csv(report, dated_dir)
    paths["weekly_slice_metrics_csv"] = export_weekly_slice_metrics_csv(report, dated_dir)

    # Update report with artifact paths
    report["generated_artifact_paths"] = list(paths.values())

    # Re-export JSON with paths included
    paths["weekly_report_json"] = export_weekly_report_json(report, dated_dir)

    # Mirror to latest/
    os.makedirs(latest_dir, exist_ok=True)
    for filename in ["weekly_report.json", "weekly_report.md",
                     "weekly_strategy_metrics.csv", "weekly_slice_metrics.csv"]:
        src = os.path.join(dated_dir, filename)
        dst = os.path.join(latest_dir, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    return paths
