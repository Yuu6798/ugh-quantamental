"""End-to-end tests for deterministic workflow runners."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone

import pytest

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    QuestionDirectionSign,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
from ugh_quantamental.workflows.models import (
    FullWorkflowRequest,
    FullWorkflowStateRequest,
    ProjectionWorkflowRequest,
    StateWorkflowRequest,
)
from ugh_quantamental.workflows.runners import make_run_id

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

# ---------------------------------------------------------------------------
# make_run_id
# ---------------------------------------------------------------------------


def test_make_run_id_includes_prefix() -> None:
    rid = make_run_id("proj-")
    assert rid.startswith("proj-")


def test_make_run_id_is_unique() -> None:
    ids = {make_run_id("x-") for _ in range(50)}
    assert len(ids) == 50


def test_make_run_id_length() -> None:
    rid = make_run_id("pfx-")
    # prefix (4) + 12 hex chars
    assert len(rid) == 16


# ---------------------------------------------------------------------------
# Shared input builders
# ---------------------------------------------------------------------------


def _question() -> QuestionFeatures:
    return QuestionFeatures(
        question_direction=QuestionDirectionSign.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.5,
    )


def _signal() -> SignalFeatures:
    return SignalFeatures(
        fundamental_score=0.3,
        technical_score=0.2,
        price_implied_score=0.1,
        context_score=1.0,
        grv_lock=0.6,
        regime_fit=0.5,
        narrative_dispersion=0.2,
        evidence_confidence=0.7,
        fire_probability=0.4,
    )


def _alignment() -> AlignmentInputs:
    return AlignmentInputs(d_qf=0.1, d_qt=0.2, d_qp=0.3, d_ft=0.1, d_fp=0.2, d_tp=0.2)


def _events() -> StateEventFeatures:
    return StateEventFeatures(
        catalyst_strength=0.5,
        follow_through=0.4,
        pricing_saturation=0.2,
        disconfirmation_strength=0.1,
        regime_shock=0.05,
        observation_freshness=0.9,
    )


# ---------------------------------------------------------------------------
# Projection workflow
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_workflow_returns_result(db_session) -> None:
    from ugh_quantamental.workflows.runners import run_projection_workflow

    req = ProjectionWorkflowRequest(
        projection_id="wf-proj-1",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    result = run_projection_workflow(db_session, req)
    db_session.commit()

    assert result.run_id.startswith("proj-")
    assert result.engine_result.projection_snapshot.projection_id == "wf-proj-1"
    assert result.persisted_run.projection_id == "wf-proj-1"
    assert result.persisted_run.run_id == result.run_id


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_workflow_explicit_run_id(db_session) -> None:
    from ugh_quantamental.workflows.runners import run_projection_workflow

    req = ProjectionWorkflowRequest(
        projection_id="wf-proj-2",
        horizon_days=10,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
        run_id="explicit-run-wf",
    )
    result = run_projection_workflow(db_session, req)
    db_session.commit()

    assert result.run_id == "explicit-run-wf"
    assert result.persisted_run.run_id == "explicit-run-wf"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_workflow_created_at_round_trip(db_session) -> None:
    """created_at supplied to the workflow surfaces as naive UTC on the persisted run."""
    from ugh_quantamental.workflows.runners import run_projection_workflow

    ist = timezone(timedelta(hours=5, minutes=30))
    supplied_at = datetime(2026, 3, 11, 12, 0, 0, tzinfo=ist)
    expected_naive_utc = datetime(2026, 3, 11, 6, 30, 0)

    req = ProjectionWorkflowRequest(
        projection_id="wf-proj-tz",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
        created_at=supplied_at,
    )
    result = run_projection_workflow(db_session, req)
    db_session.commit()

    assert result.persisted_run.created_at == expected_naive_utc
    assert result.persisted_run.created_at.tzinfo is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_workflow_engine_result_matches_persisted(db_session) -> None:
    """The engine result embedded in the workflow result matches what was persisted."""
    from ugh_quantamental.workflows.runners import run_projection_workflow

    req = ProjectionWorkflowRequest(
        projection_id="wf-proj-3",
        horizon_days=15,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    result = run_projection_workflow(db_session, req)
    db_session.commit()

    assert (
        result.persisted_run.result.projection_snapshot.point_estimate
        == result.engine_result.projection_snapshot.point_estimate
    )


# ---------------------------------------------------------------------------
# State workflow
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_workflow_returns_result(
    db_session, make_ssv_snapshot, make_omega, make_projection_engine_result
) -> None:
    from ugh_quantamental.workflows.runners import run_state_workflow

    req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=make_projection_engine_result,
        event_features=_events(),
    )
    result = run_state_workflow(db_session, req)
    db_session.commit()

    assert result.run_id.startswith("state-")
    assert result.persisted_run.snapshot_id == make_ssv_snapshot.snapshot_id
    assert result.persisted_run.omega_id == make_omega.omega_id
    assert result.persisted_run.run_id == result.run_id


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_workflow_snapshot_id_override(
    db_session, make_ssv_snapshot, make_omega, make_projection_engine_result
) -> None:
    from ugh_quantamental.workflows.runners import run_state_workflow

    req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=make_projection_engine_result,
        event_features=_events(),
        snapshot_id="custom-snap-id",
        omega_id="custom-omega-id",
    )
    result = run_state_workflow(db_session, req)
    db_session.commit()

    assert result.persisted_run.snapshot_id == "custom-snap-id"
    assert result.persisted_run.omega_id == "custom-omega-id"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_workflow_created_at_round_trip(
    db_session, make_ssv_snapshot, make_omega, make_projection_engine_result
) -> None:
    """created_at timezone normalization propagates through state workflow."""
    from ugh_quantamental.workflows.runners import run_state_workflow

    ist = timezone(timedelta(hours=5, minutes=30))
    supplied_at = datetime(2026, 3, 11, 12, 0, 0, tzinfo=ist)
    expected_naive_utc = datetime(2026, 3, 11, 6, 30, 0)

    req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=make_projection_engine_result,
        event_features=_events(),
        created_at=supplied_at,
    )
    result = run_state_workflow(db_session, req)
    db_session.commit()

    assert result.persisted_run.created_at == expected_naive_utc
    assert result.persisted_run.created_at.tzinfo is None


# ---------------------------------------------------------------------------
# Full workflow
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_full_workflow_end_to_end(
    db_session, make_ssv_snapshot, make_omega
) -> None:
    from ugh_quantamental.workflows.runners import run_full_workflow

    proj_req = ProjectionWorkflowRequest(
        projection_id="wf-full-proj",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    state_req = FullWorkflowStateRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        event_features=_events(),
    )
    full_req = FullWorkflowRequest(projection=proj_req, state=state_req)
    result = run_full_workflow(db_session, full_req)
    db_session.commit()

    assert result.projection.engine_result.projection_snapshot.projection_id == "wf-full-proj"
    assert result.state.persisted_run.snapshot_id == make_ssv_snapshot.snapshot_id
    assert result.projection.run_id != result.state.run_id


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_full_workflow_projection_id_propagated(
    db_session, make_ssv_snapshot, make_omega
) -> None:
    """State run records the projection_id from the projection snapshot."""
    from ugh_quantamental.workflows.runners import run_full_workflow

    proj_req = ProjectionWorkflowRequest(
        projection_id="wf-prop-proj",
        horizon_days=20,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    state_req = FullWorkflowStateRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        event_features=_events(),
    )
    result = run_full_workflow(db_session, FullWorkflowRequest(projection=proj_req, state=state_req))
    db_session.commit()

    assert result.state.persisted_run.projection_id == "wf-prop-proj"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_full_workflow_state_uses_projection_engine_result(
    db_session, make_ssv_snapshot, make_omega
) -> None:
    """State engine result is derived from the projection workflow output."""
    from ugh_quantamental.workflows.runners import run_full_workflow

    proj_req = ProjectionWorkflowRequest(
        projection_id="wf-chain",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    state_req = FullWorkflowStateRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        event_features=_events(),
    )
    result = run_full_workflow(db_session, FullWorkflowRequest(projection=proj_req, state=state_req))
    db_session.commit()

    # The projection result stored in the state run should match what the projection workflow computed
    assert (
        result.state.persisted_run.projection_result.projection_snapshot.projection_id
        == result.projection.engine_result.projection_snapshot.projection_id
    )


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_workflow_composes_not_reimplements(
    db_session, make_ssv_snapshot, make_omega, make_projection_engine_result
) -> None:
    """Workflow engine results are identical to calling the engines directly."""
    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.state import run_state_engine
    from ugh_quantamental.workflows.runners import run_projection_workflow, run_state_workflow

    q = _question()
    s = _signal()
    a = _alignment()
    cfg_proj = ProjectionConfig()
    cfg_state = StateConfig()
    ev = _events()

    direct_proj = run_projection_engine("wf-direct", 30, q, s, a, cfg_proj)

    wf_proj_req = ProjectionWorkflowRequest(
        projection_id="wf-direct",
        horizon_days=30,
        question_features=q,
        signal_features=s,
        alignment_inputs=a,
        config=cfg_proj,
    )
    wf_proj = run_projection_workflow(db_session, wf_proj_req)
    db_session.commit()

    assert wf_proj.engine_result.projection_snapshot.point_estimate == direct_proj.projection_snapshot.point_estimate

    direct_state = run_state_engine(make_ssv_snapshot, make_omega, direct_proj, ev, cfg_state)

    state_req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=direct_proj,
        event_features=ev,
        config=cfg_state,
    )
    wf_state = run_state_workflow(db_session, state_req)
    db_session.commit()

    assert wf_state.engine_result.dominant_state == direct_state.dominant_state
    assert wf_state.engine_result.transition_confidence == direct_state.transition_confidence
