"""Tests for replay runners: None on missing, exact-match, mismatch detection, read-only."""

from __future__ import annotations

import importlib.util

import pytest

from ugh_quantamental.engine.projection_models import (
    ProjectionConfig,
    QuestionFeatures,
    SignalFeatures,
    AlignmentInputs,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
from ugh_quantamental.replay.models import ProjectionReplayRequest, StateReplayRequest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

pytestmark = pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_projection_run(
    session,
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
    alignment_inputs: AlignmentInputs,
    projection_config: ProjectionConfig,
    run_id: str = "proj-replay-seed",
) -> str:
    from ugh_quantamental.workflows.models import ProjectionWorkflowRequest
    from ugh_quantamental.workflows.runners import run_projection_workflow

    req = ProjectionWorkflowRequest(
        projection_id="proj-replay-1",
        horizon_days=30,
        question_features=question_features,
        signal_features=signal_features,
        alignment_inputs=alignment_inputs,
        config=projection_config,
        run_id=run_id,
    )
    run_projection_workflow(session, req)
    session.flush()
    return run_id


def _seed_state_run(
    session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features: StateEventFeatures,
    state_config: StateConfig,
    run_id: str = "state-replay-seed",
) -> str:
    from ugh_quantamental.workflows.models import StateWorkflowRequest
    from ugh_quantamental.workflows.runners import run_state_workflow

    req = StateWorkflowRequest(
        snapshot=ssv_snapshot,
        omega=omega,
        projection_result=projection_engine_result,
        event_features=event_features,
        config=state_config,
        run_id=run_id,
    )
    run_state_workflow(session, req)
    session.flush()
    return run_id


# ---------------------------------------------------------------------------
# None on missing run_id
# ---------------------------------------------------------------------------


def test_replay_projection_run_returns_none_for_missing(db_session) -> None:
    from ugh_quantamental.replay.runners import replay_projection_run

    result = replay_projection_run(db_session, ProjectionReplayRequest(run_id="nonexistent"))
    assert result is None


def test_replay_state_run_returns_none_for_missing(db_session) -> None:
    from ugh_quantamental.replay.runners import replay_state_run

    result = replay_state_run(db_session, StateReplayRequest(run_id="nonexistent"))
    assert result is None


# ---------------------------------------------------------------------------
# Exact-match cases
# ---------------------------------------------------------------------------


def test_replay_projection_run_exact_match(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.runners import replay_projection_run

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs, projection_config
    )

    result = replay_projection_run(db_session, ProjectionReplayRequest(run_id=run_id))

    assert result is not None
    assert result.comparison.exact_match is True
    assert result.comparison.projection_snapshot_match is True


def test_replay_state_run_exact_match(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from ugh_quantamental.replay.runners import replay_state_run

    run_id = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result, event_features, state_config
    )

    result = replay_state_run(db_session, StateReplayRequest(run_id=run_id))

    assert result is not None
    assert result.comparison.exact_match is True
    assert result.comparison.dominant_state_match is True


# ---------------------------------------------------------------------------
# Scalar diffs are zero in exact-match
# ---------------------------------------------------------------------------


def test_projection_replay_scalar_diffs_zero_on_exact_match(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.runners import replay_projection_run

    run_id = _seed_projection_run(
        db_session,
        question_features,
        signal_features,
        alignment_inputs,
        projection_config,
        run_id="proj-scalar-check",
    )

    result = replay_projection_run(db_session, ProjectionReplayRequest(run_id=run_id))
    assert result is not None

    cmp = result.comparison
    assert cmp.point_estimate_diff == pytest.approx(0.0)
    assert cmp.confidence_diff == pytest.approx(0.0)
    assert cmp.mismatch_px_diff == pytest.approx(0.0)
    assert cmp.mismatch_sem_diff == pytest.approx(0.0)
    assert cmp.conviction_diff == pytest.approx(0.0)
    assert cmp.urgency_diff == pytest.approx(0.0)


def test_state_replay_flags_true_on_exact_match(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from ugh_quantamental.replay.runners import replay_state_run

    run_id = _seed_state_run(
        db_session,
        ssv_snapshot,
        omega,
        projection_engine_result,
        event_features,
        state_config,
        run_id="state-flags-check",
    )

    result = replay_state_run(db_session, StateReplayRequest(run_id=run_id))
    assert result is not None

    cmp = result.comparison
    assert cmp.exact_match is True
    assert cmp.dominant_state_match is True
    assert cmp.market_svp_match is True
    assert cmp.updated_probabilities_match is True
    assert cmp.transition_confidence_diff == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Mismatch detection
# ---------------------------------------------------------------------------


def test_projection_replay_detects_mismatch(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    """Mutate persisted result_json after save; replay must detect non-zero diff."""
    from ugh_quantamental.persistence.models import ProjectionRunRecord
    from ugh_quantamental.replay.runners import replay_projection_run

    run_id = _seed_projection_run(
        db_session,
        question_features,
        signal_features,
        alignment_inputs,
        projection_config,
        run_id="proj-mismatch",
    )

    # Directly mutate the ORM record's result_json to introduce a discrepancy.
    record = db_session.get(ProjectionRunRecord, run_id)
    assert record is not None
    tampered = dict(record.result_json)
    tampered_snapshot = dict(tampered["projection_snapshot"])
    tampered_snapshot["point_estimate"] = tampered_snapshot["point_estimate"] + 0.1
    tampered["projection_snapshot"] = tampered_snapshot
    record.result_json = tampered
    db_session.flush()

    # Expire the record so the next get() reflects the updated JSON.
    db_session.expire(record)

    result = replay_projection_run(db_session, ProjectionReplayRequest(run_id=run_id))
    assert result is not None
    assert result.comparison.exact_match is False
    assert result.comparison.projection_snapshot_match is False
    assert result.comparison.point_estimate_diff == pytest.approx(0.1, abs=1e-9)


def test_state_replay_detects_mismatch(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    """Mutate persisted result_json after save; replay must detect non-match."""
    from ugh_quantamental.persistence.models import StateRunRecord
    from ugh_quantamental.replay.runners import replay_state_run

    run_id = _seed_state_run(
        db_session,
        ssv_snapshot,
        omega,
        projection_engine_result,
        event_features,
        state_config,
        run_id="state-mismatch",
    )

    record = db_session.get(StateRunRecord, run_id)
    assert record is not None
    tampered = dict(record.result_json)
    # Flip transition_confidence slightly to cause mismatch.
    tampered["transition_confidence"] = max(
        0.0, min(1.0, tampered["transition_confidence"] + 0.05)
    )
    record.result_json = tampered
    db_session.flush()
    db_session.expire(record)

    result = replay_state_run(db_session, StateReplayRequest(run_id=run_id))
    assert result is not None
    assert result.comparison.exact_match is False
    assert result.comparison.transition_confidence_diff == pytest.approx(0.05, abs=1e-9)


# ---------------------------------------------------------------------------
# Read-only guarantee: replay must not create new run records
# ---------------------------------------------------------------------------


def test_projection_replay_performs_no_writes(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from sqlalchemy import func, select

    from ugh_quantamental.persistence.models import ProjectionRunRecord
    from ugh_quantamental.replay.runners import replay_projection_run

    run_id = _seed_projection_run(
        db_session,
        question_features,
        signal_features,
        alignment_inputs,
        projection_config,
        run_id="proj-readonly",
    )
    db_session.flush()

    count_before = db_session.scalar(
        select(func.count()).select_from(ProjectionRunRecord)
    )

    replay_projection_run(db_session, ProjectionReplayRequest(run_id=run_id))

    count_after = db_session.scalar(
        select(func.count()).select_from(ProjectionRunRecord)
    )

    assert count_after == count_before


def test_state_replay_performs_no_writes(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from sqlalchemy import func, select

    from ugh_quantamental.persistence.models import StateRunRecord
    from ugh_quantamental.replay.runners import replay_state_run

    run_id = _seed_state_run(
        db_session,
        ssv_snapshot,
        omega,
        projection_engine_result,
        event_features,
        state_config,
        run_id="state-readonly",
    )
    db_session.flush()

    count_before = db_session.scalar(select(func.count()).select_from(StateRunRecord))

    replay_state_run(db_session, StateReplayRequest(run_id=run_id))

    count_after = db_session.scalar(select(func.count()).select_from(StateRunRecord))

    assert count_after == count_before
