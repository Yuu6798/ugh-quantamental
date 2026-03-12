"""Tests for regression suite runner (Milestone 11)."""

from __future__ import annotations

import importlib.util

import pytest

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
from ugh_quantamental.replay.suite_models import (
    ProjectionSuiteCase,
    RegressionSuiteRequest,
    StateSuiteCase,
)

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

pytestmark = pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------


def _seed_projection(
    session,
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
    alignment_inputs: AlignmentInputs,
    config: ProjectionConfig,
    run_id: str,
    projection_id: str = "proj-suite-1",
) -> str:
    from ugh_quantamental.workflows.models import ProjectionWorkflowRequest
    from ugh_quantamental.workflows.runners import run_projection_workflow

    run_projection_workflow(
        session,
        ProjectionWorkflowRequest(
            projection_id=projection_id,
            horizon_days=30,
            question_features=question_features,
            signal_features=signal_features,
            alignment_inputs=alignment_inputs,
            config=config,
            run_id=run_id,
        ),
    )
    session.flush()
    return run_id


def _seed_state(
    session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features: StateEventFeatures,
    config: StateConfig,
    run_id: str,
) -> str:
    from ugh_quantamental.workflows.models import StateWorkflowRequest
    from ugh_quantamental.workflows.runners import run_state_workflow

    run_state_workflow(
        session,
        StateWorkflowRequest(
            snapshot=ssv_snapshot,
            omega=omega,
            projection_result=projection_engine_result,
            event_features=event_features,
            config=config,
            run_id=run_id,
        ),
    )
    session.flush()
    return run_id


# ---------------------------------------------------------------------------
# Projection-only suite
# ---------------------------------------------------------------------------


def test_suite_projection_only(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-p-1")
    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-p-2")

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="case-a", run_ids=("suite-p-1",)),
            ProjectionSuiteCase(name="case-b", run_ids=("suite-p-2",)),
        )
    )
    result = run_regression_suite(db_session, req)

    agg = result.aggregate
    assert agg.projection_case_count == 2
    assert agg.state_case_count == 0
    assert agg.total_case_count == 2
    assert agg.passed_case_count == 2
    assert agg.failed_case_count == 0
    assert agg.total_projection_requested == 2
    assert agg.total_state_requested == 0
    assert agg.total_mismatch_count == 0
    assert agg.total_missing_count == 0
    assert agg.total_error_count == 0
    assert all(r.passed for r in result.projection_cases)


# ---------------------------------------------------------------------------
# State-only suite
# ---------------------------------------------------------------------------


def test_suite_state_only(
    db_session, ssv_snapshot, omega, projection_engine_result, event_features, state_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-s-1")
    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-s-2")

    req = RegressionSuiteRequest(
        state_cases=(
            StateSuiteCase(name="state-a", run_ids=("suite-s-1",)),
            StateSuiteCase(name="state-b", run_ids=("suite-s-2",)),
        )
    )
    result = run_regression_suite(db_session, req)

    agg = result.aggregate
    assert agg.projection_case_count == 0
    assert agg.state_case_count == 2
    assert agg.passed_case_count == 2
    assert agg.total_state_requested == 2
    assert agg.total_projection_requested == 0
    assert all(r.passed for r in result.state_cases)


# ---------------------------------------------------------------------------
# Mixed projection + state suite
# ---------------------------------------------------------------------------


def test_suite_mixed(
    db_session,
    question_features, signal_features, alignment_inputs, projection_config,
    ssv_snapshot, omega, projection_engine_result, event_features, state_config,
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-mix-p-1")
    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-mix-s-1")

    req = RegressionSuiteRequest(
        projection_cases=(ProjectionSuiteCase(name="proj", run_ids=("suite-mix-p-1",)),),
        state_cases=(StateSuiteCase(name="state", run_ids=("suite-mix-s-1",)),),
    )
    result = run_regression_suite(db_session, req)

    assert result.aggregate.total_case_count == 2
    assert result.aggregate.passed_case_count == 2
    assert result.aggregate.projection_case_count == 1
    assert result.aggregate.state_case_count == 1


# ---------------------------------------------------------------------------
# Case order preservation
# ---------------------------------------------------------------------------


def test_suite_preserves_projection_case_order(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-ord-x")
    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-ord-y")

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="first", run_ids=("suite-ord-x",)),
            ProjectionSuiteCase(name="second", run_ids=("suite-ord-y",)),
        )
    )
    result = run_regression_suite(db_session, req)

    assert result.projection_cases[0].name == "first"
    assert result.projection_cases[1].name == "second"


def test_suite_preserves_state_case_order(
    db_session, ssv_snapshot, omega, projection_engine_result, event_features, state_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-sord-x")
    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-sord-y")

    req = RegressionSuiteRequest(
        state_cases=(
            StateSuiteCase(name="first", run_ids=("suite-sord-x",)),
            StateSuiteCase(name="second", run_ids=("suite-sord-y",)),
        )
    )
    result = run_regression_suite(db_session, req)

    assert result.state_cases[0].name == "first"
    assert result.state_cases[1].name == "second"


# ---------------------------------------------------------------------------
# Pass/fail logic
# ---------------------------------------------------------------------------


def test_suite_case_fails_on_missing(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="missing-case", run_ids=("no-such-run",)),
        )
    )
    result = run_regression_suite(db_session, req)

    case = result.projection_cases[0]
    assert case.passed is False
    assert result.aggregate.failed_case_count == 1
    assert result.aggregate.total_missing_count == 1


def test_suite_case_fails_on_mismatch(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from ugh_quantamental.persistence.models import ProjectionRunRecord
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-mismatch")

    record = db_session.get(ProjectionRunRecord, "suite-mismatch")
    t = dict(record.result_json)
    snap = dict(t["projection_snapshot"])
    snap["point_estimate"] = snap["point_estimate"] + 0.1
    t["projection_snapshot"] = snap
    record.result_json = t
    db_session.flush()
    db_session.expire(record)

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="mismatch-case", run_ids=("suite-mismatch",)),
        )
    )
    result = run_regression_suite(db_session, req)

    assert result.projection_cases[0].passed is False
    assert result.aggregate.total_mismatch_count == 1
    assert result.aggregate.failed_case_count == 1


def test_suite_case_fails_on_error(
    db_session, question_features, signal_features, alignment_inputs, projection_config, monkeypatch
) -> None:
    from ugh_quantamental.replay import suites as suites_module

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-err-ok")

    def _always_error(session, request):
        from ugh_quantamental.replay.batch_models import (
            BatchReplayStatus,
            ProjectionBatchReplayAggregate,
            ProjectionBatchReplayItem,
            ProjectionBatchReplayResult,
        )
        item = ProjectionBatchReplayItem(
            run_id="suite-err-ok",
            status=BatchReplayStatus.error,
            result=None,
            error_message="forced",
        )
        agg = ProjectionBatchReplayAggregate(
            requested_count=1,
            processed_count=1,
            exact_match_count=0,
            mismatch_count=0,
            missing_count=0,
            error_count=1,
            max_point_estimate_diff=0.0,
            max_confidence_diff=0.0,
        )
        return ProjectionBatchReplayResult(items=(item,), aggregate=agg)

    monkeypatch.setattr(suites_module, "replay_projection_batch", _always_error)

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="error-case", run_ids=("suite-err-ok",)),
        )
    )
    result = suites_module.run_regression_suite(db_session, req)

    assert result.projection_cases[0].passed is False
    assert result.aggregate.total_error_count == 1
    assert result.aggregate.failed_case_count == 1


# ---------------------------------------------------------------------------
# Aggregate counts in mixed-outcome suite
# ---------------------------------------------------------------------------


def test_suite_aggregate_mixed_outcomes(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-agg-ok")

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="ok-case", run_ids=("suite-agg-ok",)),
            ProjectionSuiteCase(name="missing-case", run_ids=("nonexistent-agg",)),
        )
    )
    result = run_regression_suite(db_session, req)

    agg = result.aggregate
    assert agg.total_case_count == 2
    assert agg.passed_case_count == 1
    assert agg.failed_case_count == 1
    assert agg.total_missing_count == 1
    assert agg.total_projection_requested == 2


# ---------------------------------------------------------------------------
# Query-driven case execution
# ---------------------------------------------------------------------------


def test_suite_query_driven_case(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    pid = "proj-suite-qd"
    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-qd-1", projection_id=pid)
    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-qd-2", projection_id=pid)

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(
                name="q-driven",
                query=ProjectionRunQuery(projection_id=pid, limit=10),
            ),
        )
    )
    result = run_regression_suite(db_session, req)

    assert result.projection_cases[0].batch_result.aggregate.requested_count == 2
    assert result.projection_cases[0].passed is True


def test_suite_state_query_driven_case(
    db_session, ssv_snapshot, omega, projection_engine_result, event_features, state_config
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-sqd-1")
    _seed_state(db_session, ssv_snapshot, omega, projection_engine_result,
                event_features, state_config, "suite-sqd-2")

    req = RegressionSuiteRequest(
        state_cases=(
            StateSuiteCase(
                name="q-driven-state",
                query=StateRunQuery(snapshot_id=ssv_snapshot.snapshot_id, limit=10),
            ),
        )
    )
    result = run_regression_suite(db_session, req)

    assert result.state_cases[0].batch_result.aggregate.requested_count >= 2
    assert result.state_cases[0].passed is True


# ---------------------------------------------------------------------------
# Read-only guarantee
# ---------------------------------------------------------------------------


def test_suite_no_writes(
    db_session, question_features, signal_features, alignment_inputs, projection_config
) -> None:
    from sqlalchemy import func, select

    from ugh_quantamental.persistence.models import ProjectionRunRecord
    from ugh_quantamental.replay.suites import run_regression_suite

    _seed_projection(db_session, question_features, signal_features, alignment_inputs,
                     projection_config, "suite-ro")
    db_session.flush()
    count_before = db_session.scalar(select(func.count()).select_from(ProjectionRunRecord))

    run_regression_suite(
        db_session,
        RegressionSuiteRequest(
            projection_cases=(ProjectionSuiteCase(name="ro-case", run_ids=("suite-ro",)),)
        ),
    )

    count_after = db_session.scalar(select(func.count()).select_from(ProjectionRunRecord))
    assert count_after == count_before


# ---------------------------------------------------------------------------
# Suite with all mismatches/errors still returns complete report
# ---------------------------------------------------------------------------


def test_suite_complete_report_despite_failures(
    db_session, question_features, signal_features, alignment_inputs, projection_config,
    ssv_snapshot, omega, projection_engine_result, event_features, state_config,
) -> None:
    from ugh_quantamental.replay.suites import run_regression_suite

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="all-missing-proj", run_ids=("missing-1", "missing-2")),
        ),
        state_cases=(
            StateSuiteCase(name="all-missing-state", run_ids=("missing-s-1",)),
        ),
    )
    result = run_regression_suite(db_session, req)

    # Suite completes; both cases fail; aggregate is populated
    assert result.aggregate.total_case_count == 2
    assert result.aggregate.failed_case_count == 2
    assert result.aggregate.passed_case_count == 0
    assert result.aggregate.total_missing_count == 3
    assert len(result.projection_cases) == 1
    assert len(result.state_cases) == 1
    assert result.projection_cases[0].passed is False
    assert result.state_cases[0].passed is False


# ---------------------------------------------------------------------------
# Zero-run case is always a failure (P1 fix: false-positive green prevention)
# ---------------------------------------------------------------------------


def test_suite_empty_run_ids_case_fails(db_session) -> None:
    """A case with run_ids=() must fail even though error/missing/mismatch are all zero."""
    from ugh_quantamental.replay.suites import run_regression_suite

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(name="empty-proj", run_ids=()),
        )
    )
    result = run_regression_suite(db_session, req)

    case = result.projection_cases[0]
    assert case.batch_result.aggregate.requested_count == 0
    assert case.passed is False
    assert result.aggregate.failed_case_count == 1
    assert result.aggregate.passed_case_count == 0


def test_suite_zero_match_query_case_fails(db_session) -> None:
    """A query-driven case that matches no runs must fail, not silently pass."""
    from ugh_quantamental.replay.suites import run_regression_suite

    req = RegressionSuiteRequest(
        projection_cases=(
            ProjectionSuiteCase(
                name="no-match-query",
                query=ProjectionRunQuery(projection_id="proj-does-not-exist-xyz"),
            ),
        )
    )
    result = run_regression_suite(db_session, req)

    case = result.projection_cases[0]
    assert case.batch_result.aggregate.requested_count == 0
    assert case.passed is False
    assert result.aggregate.failed_case_count == 1


def test_suite_state_empty_run_ids_case_fails(db_session) -> None:
    """State case with run_ids=() must fail."""
    from ugh_quantamental.replay.suites import run_regression_suite

    req = RegressionSuiteRequest(
        state_cases=(
            StateSuiteCase(name="empty-state", run_ids=()),
        )
    )
    result = run_regression_suite(db_session, req)

    assert result.state_cases[0].passed is False
    assert result.aggregate.failed_case_count == 1
