"""Monthly Governance v1 — persistent artifact export helpers.

Separates file I/O from pure governance computation so that the core
``run_monthly_governance`` remains read-only and side-effect-free.

All output is derived from the governance result dict — no engine recomputation.
Importable without SQLAlchemy.

Output layout:
    {csv_output_dir}/analytics/monthly/{YYYYMM}/governance_decision_log.json
    {csv_output_dir}/analytics/monthly/{YYYYMM}/governance_change_candidates.json
    {csv_output_dir}/analytics/monthly/{YYYYMM}/governance_version_decision.json
    {csv_output_dir}/analytics/monthly/{YYYYMM}/governance_summary.md
    {csv_output_dir}/analytics/monthly/latest/...  (mirror)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON exports
# ---------------------------------------------------------------------------


def _write_json(data: Any, path: str) -> str:
    """Write JSON data to a file, return absolute path."""
    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, default=str)
        fh.write("\n")
    return abs_path


def export_governance_decision_log(
    governance: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``governance_decision_log.json`` and return absolute path."""
    return _write_json(
        governance["monthly_decision_log"],
        os.path.join(output_dir, "governance_decision_log.json"),
    )


def export_governance_change_candidates(
    governance: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``governance_change_candidates.json`` and return absolute path."""
    return _write_json(
        governance["change_candidate_list"],
        os.path.join(output_dir, "governance_change_candidates.json"),
    )


def export_governance_version_decision(
    governance: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``governance_version_decision.json`` and return absolute path."""
    return _write_json(
        governance["version_decision_record"],
        os.path.join(output_dir, "governance_version_decision.json"),
    )


# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------


def _fmt_pct(value: Any) -> str:
    if value == "" or value is None:
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
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


def build_governance_summary_md(governance: dict[str, Any]) -> str:
    """Build human-readable governance summary markdown."""
    lines: list[str] = []
    dl = governance.get("monthly_decision_log", {})
    judgment = governance.get("overall_judgment", "unknown")

    lines.append("# FX Monthly Governance Summary v1")
    lines.append("")
    lines.append(f"**Review month**: {dl.get('review_month', 'N/A')}")
    lines.append(f"**Overall judgment**: `{judgment}`")
    lines.append("")

    # Key flags
    key_flags = dl.get("key_flags", [])
    if key_flags:
        lines.append("## Review Flags")
        lines.append("")
        for flag in key_flags:
            lines.append(f"- `{flag}`")
        lines.append("")

    # Baseline comparison summary
    baseline_summary = dl.get("baseline_comparison_summary", [])
    if baseline_summary:
        lines.append("## Baseline Comparison Summary")
        lines.append("")
        lines.append("| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |")
        lines.append("|---|---|---|---|")
        for b in baseline_summary:
            lines.append(
                f"| {b.get('baseline', '')} "
                f"| {_fmt_delta(b.get('direction_delta'))} "
                f"| {_fmt_delta(b.get('close_error_delta'), ' bp')} "
                f"| {_fmt_delta(b.get('magnitude_error_delta'), ' bp')} |"
            )
        lines.append("")

    # Weekly trends
    weekly_trends = governance.get("weekly_trends", [])
    if weekly_trends:
        lines.append("## Weekly Trends")
        lines.append("")
        lines.append(
            "| Week | Obs | UGH Dir Rate | UGH Mean Err | "
            "Prov OK | Prov Fail | Fallback | Ann Cov |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for w in weekly_trends:
            lines.append(
                f"| {w.get('week_start', '')}-{w.get('week_end', '')} "
                f"| {w.get('observation_count', 0)} "
                f"| {_fmt_pct(w.get('ugh_direction_hit_rate', ''))} "
                f"| {w.get('ugh_mean_close_error_bp', '-')} "
                f"| {w.get('provider_success_count', 0)} "
                f"| {w.get('provider_failed_count', 0)} "
                f"| {w.get('provider_fallback_count', 0)} "
                f"| {_fmt_pct(w.get('annotation_coverage_rate', ''))} |"
            )
        lines.append("")

    # Logic audit candidates
    logic_candidates = dl.get("logic_audit_candidates", [])
    if logic_candidates:
        lines.append("## Logic Audit Candidates")
        lines.append("")
        for c in logic_candidates:
            lines.append(f"- {c}")
        lines.append("")

    # Provider / annotation concerns
    concerns = dl.get("provider_annotation_concerns", [])
    if concerns:
        lines.append("## Provider / Annotation Concerns")
        lines.append("")
        for c in concerns:
            lines.append(f"- {c}")
        lines.append("")

    # Change candidates
    candidates = governance.get("change_candidate_list", [])
    if candidates:
        lines.append("## Change Candidates")
        lines.append("")
        lines.append("| ID | Category | Rationale | Status |")
        lines.append("|---|---|---|---|")
        for cc in candidates:
            rationale = cc.get("rationale", "")
            # Truncate long rationale for table readability
            if len(rationale) > 80:
                rationale = rationale[:77] + "..."
            lines.append(
                f"| {cc.get('candidate_id', '')} "
                f"| {cc.get('category', '')} "
                f"| {rationale} "
                f"| {cc.get('status', '')} |"
            )
        lines.append("")

    # Version decision
    vr = governance.get("version_decision_record", {})
    lines.append("## Version Decision")
    lines.append("")
    lines.append(f"- **Update performed**: {vr.get('update_performed', False)}")
    if vr.get("updated_versions"):
        lines.append(f"- **Updated**: {', '.join(str(v) for v in vr['updated_versions'])}")
    if vr.get("unchanged_versions"):
        lines.append(
            f"- **Unchanged**: {', '.join(str(v) for v in vr['unchanged_versions'])}"
        )
    if vr.get("note"):
        lines.append(f"- **Note**: {vr['note']}")
    lines.append("")

    # Final recommendation
    rec = dl.get("final_recommendation", "")
    if rec:
        lines.append("## Final Recommendation")
        lines.append("")
        lines.append(f"> {rec}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(
        "*This governance summary is auto-generated from monthly review and weekly "
        "report artifacts. Logic modifications require human decision.*"
    )
    lines.append("")

    return "\n".join(lines)


def export_governance_summary_md(
    governance: dict[str, Any],
    output_dir: str,
) -> str:
    """Write ``governance_summary.md`` and return absolute path."""
    os.makedirs(output_dir, exist_ok=True)
    content = build_governance_summary_md(governance)
    path = os.path.join(output_dir, "governance_summary.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Full export orchestrator
# ---------------------------------------------------------------------------


def export_governance_artifacts(
    governance: dict[str, Any],
    csv_output_dir: str,
    month_str: str,
) -> dict[str, str]:
    """Export all governance artifacts to both dated and latest directories.

    Returns a dict of artifact keys to absolute paths.
    """
    base = os.path.abspath(csv_output_dir)
    dated_dir = os.path.join(base, "analytics", "monthly", month_str)
    latest_dir = os.path.join(base, "analytics", "monthly", "latest")

    paths: dict[str, str] = {}

    # Export to dated directory
    paths["governance_decision_log"] = export_governance_decision_log(governance, dated_dir)
    paths["governance_change_candidates"] = export_governance_change_candidates(
        governance, dated_dir
    )
    paths["governance_version_decision"] = export_governance_version_decision(
        governance, dated_dir
    )
    paths["governance_summary_md"] = export_governance_summary_md(governance, dated_dir)

    # Mirror to latest/
    os.makedirs(latest_dir, exist_ok=True)
    for filename in [
        "governance_decision_log.json",
        "governance_change_candidates.json",
        "governance_version_decision.json",
        "governance_summary.md",
    ]:
        src = os.path.join(dated_dir, filename)
        dst = os.path.join(latest_dir, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)

    return paths
