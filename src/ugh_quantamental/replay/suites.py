"""Synchronous read-only regression suite runner (v1).

Runs multiple named batch-replay cases in one call, computes per-case pass/fail,
and returns a deterministic suite-level report.

Read-only guarantee: does not write, flush, or commit the session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ugh_quantamental.replay.batch import replay_projection_batch, replay_state_batch
from ugh_quantamental.replay.batch_models import (
    ProjectionBatchReplayRequest,
    StateBatchReplayRequest,
)
from ugh_quantamental.replay.suite_models import (
    ProjectionSuiteCaseResult,
    RegressionSuiteAggregate,
    RegressionSuiteRequest,
    RegressionSuiteResult,
    StateSuiteCaseResult,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _case_passed(error_count: int, missing_count: int, mismatch_count: int) -> bool:
    """Return True iff the case has no errors, no missing runs, and no mismatches."""
    return error_count == 0 and missing_count == 0 and mismatch_count == 0


def run_regression_suite(
    session: Session,
    request: RegressionSuiteRequest,
) -> RegressionSuiteResult:
    """Run all named suite cases and return a deterministic suite-level report.

    Projection cases run first (in declaration order), then state cases.
    Each case is converted to a batch replay request and executed via the existing
    batch replay functions.  Per-case pass/fail is computed deterministically.

    Does not write, flush, or commit the session.
    """
    projection_results: list[ProjectionSuiteCaseResult] = []
    for case in request.projection_cases:
        batch_req = ProjectionBatchReplayRequest(
            run_ids=case.run_ids,
            query=case.query,
            deduplicate_run_ids=case.deduplicate_run_ids,
        )
        batch_result = replay_projection_batch(session, batch_req)
        agg = batch_result.aggregate
        passed = _case_passed(agg.error_count, agg.missing_count, agg.mismatch_count)
        projection_results.append(
            ProjectionSuiteCaseResult(
                name=case.name,
                batch_result=batch_result,
                passed=passed,
            )
        )

    state_results: list[StateSuiteCaseResult] = []
    for case in request.state_cases:
        batch_req = StateBatchReplayRequest(
            run_ids=case.run_ids,
            query=case.query,
            deduplicate_run_ids=case.deduplicate_run_ids,
        )
        batch_result = replay_state_batch(session, batch_req)
        agg = batch_result.aggregate
        passed = _case_passed(agg.error_count, agg.missing_count, agg.mismatch_count)
        state_results.append(
            StateSuiteCaseResult(
                name=case.name,
                batch_result=batch_result,
                passed=passed,
            )
        )

    all_case_results: list[ProjectionSuiteCaseResult | StateSuiteCaseResult] = [
        *projection_results,
        *state_results,
    ]
    passed_count = sum(1 for r in all_case_results if r.passed)
    failed_count = len(all_case_results) - passed_count

    aggregate = RegressionSuiteAggregate(
        projection_case_count=len(projection_results),
        state_case_count=len(state_results),
        total_case_count=len(all_case_results),
        passed_case_count=passed_count,
        failed_case_count=failed_count,
        total_projection_requested=sum(
            r.batch_result.aggregate.requested_count for r in projection_results
        ),
        total_state_requested=sum(
            r.batch_result.aggregate.requested_count for r in state_results
        ),
        total_missing_count=sum(r.batch_result.aggregate.missing_count for r in all_case_results),
        total_error_count=sum(r.batch_result.aggregate.error_count for r in all_case_results),
        total_mismatch_count=sum(
            r.batch_result.aggregate.mismatch_count for r in all_case_results
        ),
    )

    return RegressionSuiteResult(
        projection_cases=tuple(projection_results),
        state_cases=tuple(state_results),
        aggregate=aggregate,
    )
