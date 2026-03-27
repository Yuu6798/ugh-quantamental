"""Monthly Governance v1 — governance output generation for the FX Daily Protocol.

Consumes the monthly review result (from ``run_monthly_review``) and weekly
report artifacts to produce governance outputs:
- Monthly decision log
- Change candidate list
- Version decision record

This module is a pure post-processing layer:
- No forecast / outcome / evaluation logic is changed.
- All outputs are derived from monthly review and weekly report data.
- Importable without SQLAlchemy.

Design intent: governance outputs are auto-generated; only the resulting
logic modifications (code changes, version bumps) require human decision.
"""

from __future__ import annotations

import logging
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Judgment classification
# ---------------------------------------------------------------------------

JUDGMENT_KEEP = "keep"
JUDGMENT_LOGIC_AUDIT = "logic_audit"
JUDGMENT_DATA_PROVIDER_REMEDIATION = "data_provider_remediation"
JUDGMENT_VERSION_PROMOTION_CANDIDATE = "version_promotion_candidate"


def classify_judgment(
    review_flags: list[dict[str, str]],
    baseline_comparisons: list[dict[str, Any]],
    provider_health_summary: dict[str, Any],
    annotation_coverage_summary: dict[str, Any],
) -> str:
    """Classify the monthly review into one of the four governance categories.

    Priority order (highest first):
    1. Provider / missing window issues → data_provider_remediation
    2. Annotation coverage issues → data_provider_remediation
    3. Clear inferiority to baselines → logic_audit
    4. State / disconfirmer bias → logic_audit
    5. No issues → keep

    This function does NOT produce ``version_promotion_candidate``.
    That category requires prior logic audit investigation and explicit
    human decision — it cannot be auto-classified from a single month's data.

    Returns one of: keep, logic_audit, data_provider_remediation.
    """
    flag_ids = {f["flag"] for f in review_flags}

    # Priority 1 & 2: data / provider / annotation issues
    data_flags = {"provider_quality_issue", "missing_windows", "low_annotation_coverage"}
    if flag_ids & data_flags:
        return JUDGMENT_DATA_PROVIDER_REMEDIATION

    # Priority 3 & 4: logic-related flags
    logic_flags = {"inspect_magnitude_mapping", "inspect_direction_logic", "inspect_state_mapping"}
    if flag_ids & logic_flags:
        return JUDGMENT_LOGIC_AUDIT

    # Priority 5: insufficient data is treated as keep (no action possible)
    if flag_ids == {"insufficient_data"}:
        return JUDGMENT_KEEP

    return JUDGMENT_KEEP


# ---------------------------------------------------------------------------
# Weekly trend extraction
# ---------------------------------------------------------------------------


def extract_weekly_trends(
    weekly_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract week-over-week trends from weekly report artifacts.

    For each week, extracts the UGH direction_hit_rate and mean_close_error_bp.
    Returns a list of per-week summaries ordered chronologically.
    """
    trends: list[dict[str, Any]] = []
    for report in weekly_reports:
        week_window = report.get("week_window", {})
        strategy_metrics = report.get("strategy_metrics", [])

        ugh_metrics: dict[str, Any] | None = None
        for m in strategy_metrics:
            if m.get("strategy_kind") == "ugh":
                ugh_metrics = m
                break

        entry: dict[str, Any] = {
            "week_start": week_window.get("start", ""),
            "week_end": week_window.get("end", ""),
            "observation_count": report.get("observation_count", 0),
        }

        if ugh_metrics is not None:
            entry["ugh_direction_hit_rate"] = ugh_metrics.get("direction_hit_rate", "")
            entry["ugh_mean_close_error_bp"] = ugh_metrics.get("mean_close_error_bp", "")
        else:
            entry["ugh_direction_hit_rate"] = ""
            entry["ugh_mean_close_error_bp"] = ""

        # Provider health
        ph = report.get("provider_health_summary", {})
        entry["provider_success_count"] = ph.get("success_count", 0)
        entry["provider_failed_count"] = ph.get("failed_count", 0)
        entry["provider_fallback_count"] = ph.get("fallback_adjustment_count", 0)

        # Annotation coverage
        cov = report.get("annotation_coverage", {})
        entry["annotation_coverage_rate"] = cov.get("annotation_coverage_rate", 0.0)

        trends.append(entry)

    return trends


# ---------------------------------------------------------------------------
# Monthly decision log
# ---------------------------------------------------------------------------


def build_monthly_decision_log(
    review: dict[str, Any],
    overall_judgment: str,
    weekly_trends: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the monthly decision log from the review result and judgment.

    Fields:
    - review_month: YYYYMM
    - overall_judgment: one of the four categories
    - key_flags: raised review flags
    - baseline_comparison_summary: UGH vs baseline deltas
    - weekly_trends: week-over-week performance trends
    - logic_audit_candidates: items for logic audit (if judgment is logic_audit)
    - provider_annotation_concerns: data/provider issues (if applicable)
    - final_recommendation: recommendation summary from the review
    """
    flags = review.get("review_flags", [])
    flag_ids = [f["flag"] for f in flags]

    # Baseline comparison summary
    comparisons = review.get("monthly_baseline_comparisons", [])
    baseline_summary: list[dict[str, Any]] = []
    for c in comparisons:
        baseline_summary.append({
            "baseline": c.get("baseline_strategy_kind", ""),
            "direction_delta": c.get("direction_accuracy_delta_vs_ugh"),
            "close_error_delta": c.get("mean_abs_close_error_bp_delta_vs_ugh"),
            "magnitude_error_delta": c.get("mean_abs_magnitude_error_bp_delta_vs_ugh"),
        })

    # Logic audit candidates
    logic_audit_candidates: list[str] = []
    for f in flags:
        fid = f["flag"]
        if fid == "inspect_magnitude_mapping":
            logic_audit_candidates.append("magnitude/close-error mapping")
        elif fid == "inspect_direction_logic":
            logic_audit_candidates.append("direction prediction logic")
        elif fid == "inspect_state_mapping":
            logic_audit_candidates.append("state-to-magnitude mapping")

    # Provider / annotation concerns
    provider_concerns: list[str] = []
    for f in flags:
        fid = f["flag"]
        if fid == "provider_quality_issue":
            provider_concerns.append(f["reason"])
        elif fid == "missing_windows":
            provider_concerns.append(f["reason"])
        elif fid == "low_annotation_coverage":
            provider_concerns.append(f["reason"])

    # Review month from review_generated_at_jst
    generated_at = review.get("review_generated_at_jst", "")
    review_month = ""
    if generated_at and len(generated_at) >= 7:
        review_month = generated_at[:7].replace("-", "")[:6]

    return {
        "review_month": review_month,
        "overall_judgment": overall_judgment,
        "key_flags": flag_ids,
        "baseline_comparison_summary": baseline_summary,
        "weekly_trends": weekly_trends,
        "logic_audit_candidates": logic_audit_candidates,
        "provider_annotation_concerns": provider_concerns,
        "final_recommendation": review.get("recommendation_summary", ""),
    }


# ---------------------------------------------------------------------------
# Change candidate list
# ---------------------------------------------------------------------------


def build_change_candidate_list(
    review: dict[str, Any],
    overall_judgment: str,
) -> list[dict[str, Any]]:
    """Build the change candidate list from review flags and judgment.

    Each candidate has: candidate_id, category, rationale, expected_benefit,
    expected_risk, owner, status.

    Candidates are auto-generated from flags. Status is always 'proposed'.
    Owner is always 'unassigned' (human assigns during review).
    """
    flags = review.get("review_flags", [])
    candidates: list[dict[str, Any]] = []
    candidate_counter = 0

    for f in flags:
        fid = f["flag"]
        reason = f["reason"]

        # Skip non-actionable flags
        if fid in ("keep_current_logic", "insufficient_data"):
            continue

        candidate_counter += 1

        if fid == "inspect_magnitude_mapping":
            candidates.append({
                "candidate_id": f"CC-{candidate_counter:03d}",
                "category": JUDGMENT_LOGIC_AUDIT,
                "rationale": reason,
                "expected_benefit": "Reduce close error gap vs baseline_random_walk",
                "expected_risk": "Magnitude mapping change may affect range_hit_rate",
                "owner": "unassigned",
                "status": "proposed",
            })
        elif fid == "inspect_direction_logic":
            candidates.append({
                "candidate_id": f"CC-{candidate_counter:03d}",
                "category": JUDGMENT_LOGIC_AUDIT,
                "rationale": reason,
                "expected_benefit": "Improve direction accuracy vs baseline_simple_technical",
                "expected_risk": "Direction logic change may shift state mapping behavior",
                "owner": "unassigned",
                "status": "proposed",
            })
        elif fid == "inspect_state_mapping":
            candidates.append({
                "candidate_id": f"CC-{candidate_counter:03d}",
                "category": JUDGMENT_LOGIC_AUDIT,
                "rationale": reason,
                "expected_benefit": "Better magnitude prediction when state proxy hits",
                "expected_risk": "State threshold change may affect direction accuracy",
                "owner": "unassigned",
                "status": "proposed",
            })
        elif fid == "low_annotation_coverage":
            candidates.append({
                "candidate_id": f"CC-{candidate_counter:03d}",
                "category": JUDGMENT_DATA_PROVIDER_REMEDIATION,
                "rationale": reason,
                "expected_benefit": "More reliable regime/volatility/intervention analysis",
                "expected_risk": "Annotation effort required",
                "owner": "unassigned",
                "status": "proposed",
            })
        elif fid == "provider_quality_issue":
            candidates.append({
                "candidate_id": f"CC-{candidate_counter:03d}",
                "category": JUDGMENT_DATA_PROVIDER_REMEDIATION,
                "rationale": reason,
                "expected_benefit": "Reduce data lag and fallback reliance",
                "expected_risk": "Provider migration may introduce new data characteristics",
                "owner": "unassigned",
                "status": "proposed",
            })
        elif fid == "missing_windows":
            candidates.append({
                "candidate_id": f"CC-{candidate_counter:03d}",
                "category": JUDGMENT_DATA_PROVIDER_REMEDIATION,
                "rationale": reason,
                "expected_benefit": "Complete daily coverage improves analysis reliability",
                "expected_risk": "Root cause investigation may reveal infrastructure issues",
                "owner": "unassigned",
                "status": "proposed",
            })

    return candidates


# ---------------------------------------------------------------------------
# Version decision record
# ---------------------------------------------------------------------------


def build_version_decision_record(
    overall_judgment: str,
    review_month: str,
) -> dict[str, Any]:
    """Build the version decision record.

    Only ``version_promotion_candidate`` judgment results in an update.
    Since auto-classification never produces that category, the record
    will always indicate no update. Human review may override.
    """
    update_performed = overall_judgment == JUDGMENT_VERSION_PROMOTION_CANDIDATE

    return {
        "update_performed": update_performed,
        "updated_versions": [],
        "unchanged_versions": [
            "theory_version",
            "engine_version",
            "schema_version",
            "protocol_version",
        ],
        "freeze_window_start": "",
        "freeze_window_end": "",
        "rollback_trigger": "",
        "review_month": review_month,
        "note": (
            "Version updates require human decision after logic audit investigation. "
            "This record is auto-generated; update fields manually if a version "
            "promotion is approved."
        ),
    }


# ---------------------------------------------------------------------------
# Full governance generation
# ---------------------------------------------------------------------------


def run_monthly_governance(
    review: dict[str, Any],
    weekly_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate all governance outputs from the monthly review and weekly reports.

    This is the main entry point for governance output generation.
    All inputs are pre-loaded; no file I/O is performed.

    Returns a dict with:
    - governance_version: "v1"
    - overall_judgment: classification result
    - monthly_decision_log: the decision log
    - change_candidate_list: list of change candidates
    - version_decision_record: version update record
    - weekly_trends: week-over-week trends
    """
    # Extract weekly trends
    weekly_trends = extract_weekly_trends(weekly_reports)

    # Classify judgment
    overall_judgment = classify_judgment(
        review_flags=review.get("review_flags", []),
        baseline_comparisons=review.get("monthly_baseline_comparisons", []),
        provider_health_summary=review.get("provider_health_summary", {}),
        annotation_coverage_summary=review.get("annotation_coverage_summary", {}),
    )

    # Build decision log
    decision_log = build_monthly_decision_log(review, overall_judgment, weekly_trends)

    # Build change candidate list
    change_candidates = build_change_candidate_list(review, overall_judgment)

    # Build version decision record
    review_month = decision_log.get("review_month", "")
    version_record = build_version_decision_record(overall_judgment, review_month)

    return {
        "governance_version": "v1",
        "overall_judgment": overall_judgment,
        "monthly_decision_log": decision_log,
        "change_candidate_list": change_candidates,
        "version_decision_record": version_record,
        "weekly_trends": weekly_trends,
    }
