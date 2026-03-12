"""Tests for baseline_models: validation, invariants, and field shapes."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ugh_quantamental.replay.baseline_models import (
    CompareRegressionBaselineRequest,
    CreateRegressionBaselineRequest,
    RegressionBaselineComparison,
    RegressionSuiteBaseline,
    RegressionSuiteCaseDelta,
)
from ugh_quantamental.replay.suite_models import ProjectionSuiteCase, RegressionSuiteRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_suite_request() -> RegressionSuiteRequest:
    return RegressionSuiteRequest(
        projection_cases=(ProjectionSuiteCase(name="smoke", run_ids=("r-001",)),)
    )


# ---------------------------------------------------------------------------
# CreateRegressionBaselineRequest
# ---------------------------------------------------------------------------


def test_create_request_minimal() -> None:
    req = CreateRegressionBaselineRequest(
        baseline_name="v1",
        suite_request=_make_suite_request(),
    )
    assert req.baseline_name == "v1"
    assert req.description is None
    assert req.baseline_id is None
    assert req.created_at is None


def test_create_request_full() -> None:
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    req = CreateRegressionBaselineRequest(
        baseline_name="v1",
        suite_request=_make_suite_request(),
        description="initial golden snapshot",
        baseline_id="base_abc123",
        created_at=ts,
    )
    assert req.description == "initial golden snapshot"
    assert req.baseline_id == "base_abc123"
    assert req.created_at == ts


def test_create_request_empty_name_rejected() -> None:
    with pytest.raises(ValidationError, match="baseline_name must be non-empty"):
        CreateRegressionBaselineRequest(
            baseline_name="   ",
            suite_request=_make_suite_request(),
        )


def test_create_request_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        CreateRegressionBaselineRequest(
            baseline_name="v1",
            suite_request=_make_suite_request(),
            unknown_field="x",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# CompareRegressionBaselineRequest
# ---------------------------------------------------------------------------


def test_compare_request_by_id() -> None:
    req = CompareRegressionBaselineRequest(baseline_id="base_abc123")
    assert req.baseline_id == "base_abc123"
    assert req.baseline_name is None


def test_compare_request_by_name() -> None:
    req = CompareRegressionBaselineRequest(baseline_name="v1")
    assert req.baseline_name == "v1"
    assert req.baseline_id is None


def test_compare_request_both_raises() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        CompareRegressionBaselineRequest(baseline_id="x", baseline_name="y")


def test_compare_request_neither_raises() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        CompareRegressionBaselineRequest()


# ---------------------------------------------------------------------------
# RegressionSuiteBaseline
# ---------------------------------------------------------------------------


def test_baseline_is_frozen() -> None:
    bl = RegressionSuiteBaseline(
        baseline_id="base_abc",
        baseline_name="v1",
        created_at=datetime(2026, 1, 1),
        description=None,
        suite_request=_make_suite_request(),
        suite_result_json={"aggregate": {}, "projection_cases": [], "state_cases": []},
    )
    with pytest.raises(Exception):
        bl.baseline_name = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RegressionSuiteCaseDelta
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "passed_match",
    [True, False, None],
)
def test_case_delta_passed_match_values(passed_match: bool | None) -> None:
    delta = RegressionSuiteCaseDelta(
        group="projection",
        name="smoke",
        exists_in_baseline=True,
        exists_in_current=True,
        passed_match=passed_match,
    )
    assert delta.passed_match is passed_match
    assert delta.group == "projection"


# ---------------------------------------------------------------------------
# RegressionBaselineComparison
# ---------------------------------------------------------------------------


def test_comparison_exact_match_all_zeros() -> None:
    cmp = RegressionBaselineComparison(
        exact_match=True,
        case_count_match=True,
        passed_case_count_diff=0,
        failed_case_count_diff=0,
        total_missing_count_diff=0,
        total_error_count_diff=0,
        total_mismatch_count_diff=0,
        case_deltas=(),
    )
    assert cmp.exact_match is True
    assert cmp.passed_case_count_diff == 0


def test_comparison_non_match() -> None:
    delta = RegressionSuiteCaseDelta(
        group="state",
        name="flaky",
        exists_in_baseline=True,
        exists_in_current=True,
        passed_match=False,
    )
    cmp = RegressionBaselineComparison(
        exact_match=False,
        case_count_match=True,
        passed_case_count_diff=-1,
        failed_case_count_diff=1,
        total_missing_count_diff=0,
        total_error_count_diff=0,
        total_mismatch_count_diff=3,
        case_deltas=(delta,),
    )
    assert cmp.exact_match is False
    assert cmp.total_mismatch_count_diff == 3
    assert len(cmp.case_deltas) == 1
    assert cmp.case_deltas[0].passed_match is False


# ---------------------------------------------------------------------------
# RegressionSuiteCaseDelta — group field
# ---------------------------------------------------------------------------


def test_case_delta_group_projection() -> None:
    delta = RegressionSuiteCaseDelta(
        group="projection",
        name="smoke",
        exists_in_baseline=True,
        exists_in_current=True,
        passed_match=True,
    )
    assert delta.group == "projection"


def test_case_delta_group_state() -> None:
    delta = RegressionSuiteCaseDelta(
        group="state",
        name="smoke",
        exists_in_baseline=True,
        exists_in_current=False,
        passed_match=None,
    )
    assert delta.group == "state"
    assert delta.exists_in_current is False
