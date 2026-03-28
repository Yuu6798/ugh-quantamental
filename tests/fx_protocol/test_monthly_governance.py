"""Tests for monthly_governance.py — pure governance output generation."""

from __future__ import annotations

from ugh_quantamental.fx_protocol.monthly_governance import (
    JUDGMENT_DATA_PROVIDER_REMEDIATION,
    JUDGMENT_KEEP,
    JUDGMENT_LOGIC_AUDIT,
    _resolve_review_month,
    build_change_candidate_list,
    build_monthly_decision_log,
    build_version_decision_record,
    classify_judgment,
    extract_weekly_trends,
    run_monthly_governance,
)


# ---------------------------------------------------------------------------
# classify_judgment
# ---------------------------------------------------------------------------


class TestClassifyJudgment:
    """Test judgment classification from review flags."""

    def test_keep_when_no_flags(self) -> None:
        flags = [{"flag": "keep_current_logic", "reason": "All OK"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_KEEP

    def test_keep_when_insufficient_data(self) -> None:
        flags = [{"flag": "insufficient_data", "reason": "Not enough data"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_KEEP

    def test_data_remediation_on_provider_issue(self) -> None:
        flags = [{"flag": "provider_quality_issue", "reason": "Lag too high"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_DATA_PROVIDER_REMEDIATION

    def test_data_remediation_on_missing_windows(self) -> None:
        flags = [{"flag": "missing_windows", "reason": "25% missing"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_DATA_PROVIDER_REMEDIATION

    def test_data_remediation_on_low_annotation_coverage(self) -> None:
        flags = [{"flag": "low_annotation_coverage", "reason": "Coverage low"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_DATA_PROVIDER_REMEDIATION

    def test_logic_audit_on_direction_logic(self) -> None:
        flags = [{"flag": "inspect_direction_logic", "reason": "Baseline outperforming"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_LOGIC_AUDIT

    def test_logic_audit_on_magnitude_mapping(self) -> None:
        flags = [{"flag": "inspect_magnitude_mapping", "reason": "Error too high"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_LOGIC_AUDIT

    def test_logic_audit_on_state_mapping(self) -> None:
        flags = [{"flag": "inspect_state_mapping", "reason": "State hit high but error high"}]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_LOGIC_AUDIT

    def test_data_remediation_takes_priority_over_logic(self) -> None:
        """Provider issues take priority over logic issues (priority order)."""
        flags = [
            {"flag": "inspect_direction_logic", "reason": "Baseline outperforming"},
            {"flag": "provider_quality_issue", "reason": "Lag too high"},
        ]
        result = classify_judgment(flags, [], {}, {})
        assert result == JUDGMENT_DATA_PROVIDER_REMEDIATION


# ---------------------------------------------------------------------------
# extract_weekly_trends
# ---------------------------------------------------------------------------


class TestExtractWeeklyTrends:
    """Test weekly trend extraction from report artifacts."""

    def test_empty_reports(self) -> None:
        result = extract_weekly_trends([])
        assert result == []

    def test_single_report(self) -> None:
        report = {
            "week_window": {"start": "20260301", "end": "20260305"},
            "observation_count": 20,
            "strategy_metrics": [
                {
                    "strategy_kind": "ugh",
                    "direction_hit_rate": "0.6500",
                    "mean_close_error_bp": "12.50",
                },
                {
                    "strategy_kind": "baseline_random_walk",
                    "direction_hit_rate": "0.5000",
                    "mean_close_error_bp": "15.00",
                },
            ],
            "provider_health_summary": {
                "success_count": 5,
                "failed_count": 0,
                "fallback_adjustment_count": 1,
            },
            "annotation_coverage": {
                "annotation_coverage_rate": 0.85,
            },
        }
        result = extract_weekly_trends([report])
        assert len(result) == 1
        assert result[0]["week_start"] == "20260301"
        assert result[0]["week_end"] == "20260305"
        assert result[0]["observation_count"] == 20
        assert result[0]["ugh_direction_hit_rate"] == "0.6500"
        assert result[0]["provider_success_count"] == 5
        assert result[0]["annotation_coverage_rate"] == 0.85

    def test_multiple_reports_preserve_order(self) -> None:
        reports = [
            {
                "week_window": {"start": "20260301", "end": "20260305"},
                "observation_count": 20,
                "strategy_metrics": [],
                "provider_health_summary": {},
                "annotation_coverage": {},
            },
            {
                "week_window": {"start": "20260308", "end": "20260312"},
                "observation_count": 25,
                "strategy_metrics": [],
                "provider_health_summary": {},
                "annotation_coverage": {},
            },
        ]
        result = extract_weekly_trends(reports)
        assert len(result) == 2
        assert result[0]["week_start"] == "20260301"
        assert result[1]["week_start"] == "20260308"


# ---------------------------------------------------------------------------
# _resolve_review_month
# ---------------------------------------------------------------------------


class TestResolveReviewMonth:
    """Test that review_month is derived from the observation window, not generation date."""

    def test_april_1_review_resolves_to_march(self) -> None:
        """Review generated 2026-04-01 with 20-day window should label as 202603."""
        review = {
            "review_generated_at_jst": "2026-04-01T08:00:00+09:00",
            "requested_window_count": 20,
        }
        assert _resolve_review_month(review) == "202603"

    def test_march_1_review_resolves_to_february(self) -> None:
        review = {
            "review_generated_at_jst": "2026-03-01T08:00:00+09:00",
            "requested_window_count": 20,
        }
        assert _resolve_review_month(review) == "202602"

    def test_mid_month_review_stays_in_same_month(self) -> None:
        """Review generated mid-month with small window stays in same month."""
        review = {
            "review_generated_at_jst": "2026-03-20T08:00:00+09:00",
            "requested_window_count": 5,
        }
        assert _resolve_review_month(review) == "202603"

    def test_empty_generated_at(self) -> None:
        review = {"review_generated_at_jst": "", "requested_window_count": 20}
        assert _resolve_review_month(review) == ""


# ---------------------------------------------------------------------------
# build_monthly_decision_log
# ---------------------------------------------------------------------------


class TestBuildMonthlyDecisionLog:
    """Test decision log generation."""

    def _make_review(
        self,
        flags: list[dict[str, str]] | None = None,
        comparisons: list[dict] | None = None,
    ) -> dict:
        return {
            "review_generated_at_jst": "2026-04-01T08:00:00+09:00",
            "requested_window_count": 20,
            "review_flags": flags or [{"flag": "keep_current_logic", "reason": "All OK"}],
            "monthly_baseline_comparisons": comparisons or [],
            "recommendation_summary": "All good",
        }

    def test_basic_structure(self) -> None:
        review = self._make_review()
        result = build_monthly_decision_log(review, JUDGMENT_KEEP, [])
        # Generated on 2026-04-01, window=20 business days → midpoint is in March
        assert result["review_month"] == "202603"
        assert result["overall_judgment"] == JUDGMENT_KEEP
        assert result["key_flags"] == ["keep_current_logic"]
        assert result["logic_audit_candidates"] == []
        assert result["provider_annotation_concerns"] == []
        assert result["final_recommendation"] == "All good"

    def test_logic_audit_candidates_populated(self) -> None:
        flags = [
            {"flag": "inspect_direction_logic", "reason": "Baseline outperforming"},
            {"flag": "inspect_state_mapping", "reason": "State hit high but error high"},
        ]
        review = self._make_review(flags=flags)
        result = build_monthly_decision_log(review, JUDGMENT_LOGIC_AUDIT, [])
        assert "direction prediction logic" in result["logic_audit_candidates"]
        assert "state-to-magnitude mapping" in result["logic_audit_candidates"]

    def test_provider_concerns_populated(self) -> None:
        flags = [
            {"flag": "provider_quality_issue", "reason": "Lag rate 40%"},
            {"flag": "missing_windows", "reason": "30% missing"},
        ]
        review = self._make_review(flags=flags)
        result = build_monthly_decision_log(
            review, JUDGMENT_DATA_PROVIDER_REMEDIATION, []
        )
        assert len(result["provider_annotation_concerns"]) == 2

    def test_weekly_trends_included(self) -> None:
        review = self._make_review()
        trends = [{"week_start": "20260301", "week_end": "20260305"}]
        result = build_monthly_decision_log(review, JUDGMENT_KEEP, trends)
        assert result["weekly_trends"] == trends


# ---------------------------------------------------------------------------
# build_change_candidate_list
# ---------------------------------------------------------------------------


class TestBuildChangeCandidateList:
    """Test change candidate list generation."""

    def test_no_candidates_on_keep(self) -> None:
        review = {
            "review_flags": [{"flag": "keep_current_logic", "reason": "All OK"}],
        }
        result = build_change_candidate_list(review, JUDGMENT_KEEP)
        assert result == []

    def test_no_candidates_on_insufficient_data(self) -> None:
        review = {
            "review_flags": [{"flag": "insufficient_data", "reason": "Not enough"}],
        }
        result = build_change_candidate_list(review, JUDGMENT_KEEP)
        assert result == []

    def test_logic_flags_produce_candidates(self) -> None:
        review = {
            "review_flags": [
                {"flag": "inspect_direction_logic", "reason": "Baseline outperforming"},
                {"flag": "inspect_magnitude_mapping", "reason": "Error too high"},
            ],
        }
        result = build_change_candidate_list(review, JUDGMENT_LOGIC_AUDIT)
        assert len(result) == 2
        assert all(c["status"] == "proposed" for c in result)
        assert all(c["owner"] == "unassigned" for c in result)
        assert result[0]["category"] == JUDGMENT_LOGIC_AUDIT
        assert "CC-001" == result[0]["candidate_id"]
        assert "CC-002" == result[1]["candidate_id"]

    def test_provider_flags_produce_candidates(self) -> None:
        review = {
            "review_flags": [
                {"flag": "provider_quality_issue", "reason": "Lag rate 40%"},
                {"flag": "missing_windows", "reason": "30% missing"},
                {"flag": "low_annotation_coverage", "reason": "Coverage 20%"},
            ],
        }
        result = build_change_candidate_list(
            review, JUDGMENT_DATA_PROVIDER_REMEDIATION
        )
        assert len(result) == 3
        assert all(c["category"] == JUDGMENT_DATA_PROVIDER_REMEDIATION for c in result)


# ---------------------------------------------------------------------------
# build_version_decision_record
# ---------------------------------------------------------------------------


class TestBuildVersionDecisionRecord:
    """Test version decision record generation."""

    def test_no_update_on_keep(self) -> None:
        result = build_version_decision_record(JUDGMENT_KEEP, "202603")
        assert result["update_performed"] is False
        assert result["updated_versions"] == []
        assert len(result["unchanged_versions"]) == 4
        assert result["review_month"] == "202603"

    def test_no_update_on_logic_audit(self) -> None:
        result = build_version_decision_record(JUDGMENT_LOGIC_AUDIT, "202603")
        assert result["update_performed"] is False

    def test_no_update_on_data_remediation(self) -> None:
        result = build_version_decision_record(
            JUDGMENT_DATA_PROVIDER_REMEDIATION, "202603"
        )
        assert result["update_performed"] is False


# ---------------------------------------------------------------------------
# run_monthly_governance (integration)
# ---------------------------------------------------------------------------


class TestRunMonthlyGovernance:
    """Test the full governance generation entry point."""

    def _make_review(self, flags: list[dict[str, str]] | None = None) -> dict:
        return {
            "review_version": "v1",
            "review_generated_at_jst": "2026-04-01T08:00:00+09:00",
            "requested_window_count": 20,
            "included_window_count": 18,
            "missing_window_count": 2,
            "monthly_strategy_metrics": [
                {"strategy_kind": "ugh", "forecast_count": 18, "direction_hit_rate": 0.6},
            ],
            "monthly_baseline_comparisons": [
                {
                    "baseline_strategy_kind": "baseline_random_walk",
                    "direction_accuracy_delta_vs_ugh": -0.1,
                    "mean_abs_close_error_bp_delta_vs_ugh": 3.0,
                    "mean_abs_magnitude_error_bp_delta_vs_ugh": 2.0,
                },
            ],
            "provider_health_summary": {"total_runs": 18},
            "annotation_coverage_summary": {"annotation_coverage_rate": 0.8},
            "review_flags": flags
            or [{"flag": "keep_current_logic", "reason": "All OK"}],
            "recommendation_summary": "All metrics within thresholds.",
        }

    def test_full_governance_keep(self) -> None:
        review = self._make_review()
        result = run_monthly_governance(review, [])
        assert result["governance_version"] == "v1"
        assert result["overall_judgment"] == JUDGMENT_KEEP
        assert result["monthly_decision_log"]["review_month"] == "202603"
        assert result["change_candidate_list"] == []
        assert result["version_decision_record"]["update_performed"] is False

    def test_full_governance_with_weekly_trends(self) -> None:
        review = self._make_review()
        weekly_reports = [
            {
                "week_window": {"start": "20260301", "end": "20260305"},
                "observation_count": 20,
                "strategy_metrics": [
                    {"strategy_kind": "ugh", "direction_hit_rate": "0.65",
                     "mean_close_error_bp": "12.5"},
                ],
                "provider_health_summary": {"success_count": 5, "failed_count": 0,
                                            "fallback_adjustment_count": 0},
                "annotation_coverage": {"annotation_coverage_rate": 0.9},
            },
        ]
        result = run_monthly_governance(review, weekly_reports)
        assert len(result["weekly_trends"]) == 1
        assert result["monthly_decision_log"]["weekly_trends"][0]["week_start"] == "20260301"

    def test_full_governance_logic_audit(self) -> None:
        flags = [
            {"flag": "inspect_direction_logic", "reason": "Baseline outperforming UGH"},
        ]
        review = self._make_review(flags=flags)
        result = run_monthly_governance(review, [])
        assert result["overall_judgment"] == JUDGMENT_LOGIC_AUDIT
        assert len(result["change_candidate_list"]) == 1
        assert result["version_decision_record"]["update_performed"] is False

    def test_full_governance_data_remediation(self) -> None:
        flags = [
            {"flag": "provider_quality_issue", "reason": "Lag rate 40%"},
            {"flag": "inspect_direction_logic", "reason": "Baseline outperforming"},
        ]
        review = self._make_review(flags=flags)
        result = run_monthly_governance(review, [])
        # Data remediation takes priority over logic audit
        assert result["overall_judgment"] == JUDGMENT_DATA_PROVIDER_REMEDIATION
        assert len(result["change_candidate_list"]) == 2
