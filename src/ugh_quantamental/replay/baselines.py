"""Synchronous read-mostly baseline / golden snapshot runner (v1).

Creates, loads, and compares named regression suite baselines persisted in the DB.

Read/write policy:
- ``create_regression_baseline`` writes one baseline record (flush only; caller commits).
- ``get_regression_baseline`` is read-only.
- ``compare_regression_baseline`` is read-only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ugh_quantamental.replay.baseline_models import (
    CompareRegressionBaselineRequest,
    CreateRegressionBaselineRequest,
    RegressionBaselineComparison,
    RegressionBaselineCompareResult,
    RegressionSuiteBaseline,
    RegressionSuiteBaselineBundle,
    RegressionSuiteCaseDelta,
)
from ugh_quantamental.replay.suite_models import (
    RegressionSuiteRequest,
    RegressionSuiteResult,
)
from ugh_quantamental.replay.suites import run_regression_suite

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def make_baseline_id(prefix: str = "base_") -> str:
    """Return a short unique baseline identifier."""
    return f"{prefix}{uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Internal serialization helpers
# ---------------------------------------------------------------------------


def _dump_suite_result(result: RegressionSuiteResult) -> dict[str, Any]:
    """Serialize a RegressionSuiteResult to a JSON-compatible dict.

    Captures aggregate counts and per-case pass/fail + batch aggregate.
    Individual per-run replay results are not stored; the aggregate is
    sufficient for deterministic comparison.
    """

    def _case_entry(case: Any) -> dict[str, Any]:
        return {
            "name": case.name,
            "passed": case.passed,
            "batch_aggregate": case.batch_result.aggregate.model_dump(mode="json"),
        }

    return {
        "aggregate": result.aggregate.model_dump(mode="json"),
        "projection_cases": [_case_entry(c) for c in result.projection_cases],
        "state_cases": [_case_entry(c) for c in result.state_cases],
    }


def _build_baseline(record: Any) -> RegressionSuiteBaseline:
    """Reconstruct a typed RegressionSuiteBaseline from a persisted record."""
    suite_request = RegressionSuiteRequest.model_validate(record.suite_request_json)
    return RegressionSuiteBaseline(
        baseline_id=record.baseline_id,
        baseline_name=record.baseline_name,
        created_at=record.created_at,
        description=record.description,
        suite_request=suite_request,
        suite_result_json=record.suite_result_json,
    )


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------


def _compare_results(
    stored_json: dict[str, Any],
    current_json: dict[str, Any],
) -> RegressionBaselineComparison:
    """Compute a deterministic comparison between stored and current suite result dicts."""
    exact_match = stored_json == current_json

    stored_agg = stored_json["aggregate"]
    current_agg = current_json["aggregate"]

    case_count_match = stored_agg["total_case_count"] == current_agg["total_case_count"]

    # Build per-case lookup by name within each group
    stored_proj = {c["name"]: c for c in stored_json["projection_cases"]}
    stored_state = {c["name"]: c for c in stored_json["state_cases"]}
    current_proj = {c["name"]: c for c in current_json["projection_cases"]}
    current_state = {c["name"]: c for c in current_json["state_cases"]}

    all_names = sorted(
        set(stored_proj) | set(current_proj) | set(stored_state) | set(current_state)
    )

    deltas: list[RegressionSuiteCaseDelta] = []
    for name in all_names:
        in_stored = name in stored_proj or name in stored_state
        in_current = name in current_proj or name in current_state

        if name in stored_proj and name in current_proj:
            passed_match: bool | None = stored_proj[name]["passed"] == current_proj[name]["passed"]
        elif name in stored_state and name in current_state:
            passed_match = stored_state[name]["passed"] == current_state[name]["passed"]
        else:
            # Case is absent on one side or changed group — comparison undefined
            passed_match = None

        deltas.append(
            RegressionSuiteCaseDelta(
                name=name,
                exists_in_baseline=in_stored,
                exists_in_current=in_current,
                passed_match=passed_match,
            )
        )

    return RegressionBaselineComparison(
        exact_match=exact_match,
        case_count_match=case_count_match,
        passed_case_count_diff=current_agg["passed_case_count"] - stored_agg["passed_case_count"],
        failed_case_count_diff=current_agg["failed_case_count"] - stored_agg["failed_case_count"],
        total_missing_count_diff=(
            current_agg["total_missing_count"] - stored_agg["total_missing_count"]
        ),
        total_error_count_diff=(
            current_agg["total_error_count"] - stored_agg["total_error_count"]
        ),
        total_mismatch_count_diff=(
            current_agg["total_mismatch_count"] - stored_agg["total_mismatch_count"]
        ),
        case_deltas=tuple(deltas),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_regression_baseline(
    session: Session,
    request: CreateRegressionBaselineRequest,
) -> RegressionSuiteBaselineBundle:
    """Run the suite, persist the result as a named baseline, and return the bundle.

    Flushes but does not commit; the caller owns the transaction.
    """
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    suite_result = run_regression_suite(session, request.suite_request)
    suite_result_json = _dump_suite_result(suite_result)
    suite_request_json = request.suite_request.model_dump(mode="json")

    baseline_id = request.baseline_id or make_baseline_id()
    created_at = request.created_at or datetime.now(timezone.utc)

    RegressionSuiteBaselineRepository.save_baseline(
        session,
        baseline_id=baseline_id,
        baseline_name=request.baseline_name,
        created_at=created_at,
        description=request.description,
        suite_request_json=suite_request_json,
        suite_result_json=suite_result_json,
    )

    record = RegressionSuiteBaselineRepository.load_baseline(session, baseline_id)
    assert record is not None, f"baseline {baseline_id!r} not found after flush"

    baseline = _build_baseline(record)
    return RegressionSuiteBaselineBundle(
        baseline=baseline,
        persisted_run_id=baseline_id,
    )


def get_regression_baseline(
    session: Session,
    *,
    baseline_id: str | None = None,
    baseline_name: str | None = None,
) -> RegressionSuiteBaselineBundle | None:
    """Load a baseline by id or unique name. Returns None if not found.

    Exactly one of baseline_id or baseline_name must be provided.
    Read-only: no writes, flushes, or commits.
    """
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    if (baseline_id is None) == (baseline_name is None):
        raise ValueError("exactly one of baseline_id or baseline_name must be provided")

    if baseline_id is not None:
        record = RegressionSuiteBaselineRepository.load_baseline(session, baseline_id)
    else:
        assert baseline_name is not None
        record = RegressionSuiteBaselineRepository.load_baseline_by_name(session, baseline_name)

    if record is None:
        return None

    baseline = _build_baseline(record)
    return RegressionSuiteBaselineBundle(
        baseline=baseline,
        persisted_run_id=record.baseline_id,
    )


def compare_regression_baseline(
    session: Session,
    request: CompareRegressionBaselineRequest,
) -> RegressionBaselineCompareResult | None:
    """Compare a stored baseline against a fresh suite rerun.

    Returns None if the baseline is not found.
    Read-only: no writes, flushes, or commits.
    """
    bundle = get_regression_baseline(
        session,
        baseline_id=request.baseline_id,
        baseline_name=request.baseline_name,
    )
    if bundle is None:
        return None

    current_result = run_regression_suite(session, bundle.baseline.suite_request)
    current_json = _dump_suite_result(current_result)

    comparison = _compare_results(bundle.baseline.suite_result_json, current_json)

    return RegressionBaselineCompareResult(
        baseline=bundle.baseline,
        current_result_json=current_json,
        comparison=comparison,
    )
