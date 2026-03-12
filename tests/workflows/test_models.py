"""Validation tests for workflow request/response model contracts."""

from __future__ import annotations

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
    ProjectionWorkflowRequest,
    StateWorkflowRequest,
)

# ---------------------------------------------------------------------------
# Shared minimal fixture builders
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


# ---------------------------------------------------------------------------
# ProjectionWorkflowRequest
# ---------------------------------------------------------------------------


def test_projection_request_defaults() -> None:
    req = ProjectionWorkflowRequest(
        projection_id="p-1",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    assert req.config == ProjectionConfig()
    assert req.run_id is None
    assert req.created_at is None


def test_projection_request_explicit_run_id() -> None:
    req = ProjectionWorkflowRequest(
        projection_id="p-1",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
        run_id="my-run-001",
    )
    assert req.run_id == "my-run-001"


def test_projection_request_rejects_extra_fields() -> None:
    with pytest.raises(Exception):
        ProjectionWorkflowRequest(  # type: ignore[call-arg]
            projection_id="p-1",
            horizon_days=30,
            question_features=_question(),
            signal_features=_signal(),
            alignment_inputs=_alignment(),
            unknown_field="bad",
        )


def test_projection_request_horizon_days_minimum() -> None:
    with pytest.raises(Exception):
        ProjectionWorkflowRequest(
            projection_id="p-1",
            horizon_days=0,
            question_features=_question(),
            signal_features=_signal(),
            alignment_inputs=_alignment(),
        )


def test_projection_request_is_frozen() -> None:
    req = ProjectionWorkflowRequest(
        projection_id="p-1",
        horizon_days=30,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    with pytest.raises(Exception):
        req.projection_id = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# StateWorkflowRequest (field presence only; engine types tested elsewhere)
# ---------------------------------------------------------------------------


def test_state_request_optional_ids_default_none(
    make_ssv_snapshot,
    make_omega,
    make_projection_engine_result,
) -> None:
    req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=make_projection_engine_result,
        event_features=StateEventFeatures(
            catalyst_strength=0.5,
            follow_through=0.4,
            pricing_saturation=0.2,
            disconfirmation_strength=0.1,
            regime_shock=0.05,
            observation_freshness=0.9,
        ),
    )
    assert req.snapshot_id is None
    assert req.omega_id is None
    assert req.projection_id is None
    assert req.run_id is None
    assert req.config == StateConfig()


def test_state_request_explicit_ids(
    make_ssv_snapshot,
    make_omega,
    make_projection_engine_result,
) -> None:
    req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=make_projection_engine_result,
        event_features=StateEventFeatures(
            catalyst_strength=0.5,
            follow_through=0.4,
            pricing_saturation=0.2,
            disconfirmation_strength=0.1,
            regime_shock=0.05,
            observation_freshness=0.9,
        ),
        snapshot_id="snap-x",
        omega_id="omega-x",
        projection_id="proj-x",
        run_id="state-run-x",
    )
    assert req.snapshot_id == "snap-x"
    assert req.omega_id == "omega-x"
    assert req.projection_id == "proj-x"
    assert req.run_id == "state-run-x"


# ---------------------------------------------------------------------------
# FullWorkflowRequest
# ---------------------------------------------------------------------------


def test_full_request_composes_sub_requests(
    make_ssv_snapshot,
    make_omega,
    make_projection_engine_result,
) -> None:
    proj_req = ProjectionWorkflowRequest(
        projection_id="p-full",
        horizon_days=20,
        question_features=_question(),
        signal_features=_signal(),
        alignment_inputs=_alignment(),
    )
    state_req = StateWorkflowRequest(
        snapshot=make_ssv_snapshot,
        omega=make_omega,
        projection_result=make_projection_engine_result,
        event_features=StateEventFeatures(
            catalyst_strength=0.5,
            follow_through=0.4,
            pricing_saturation=0.2,
            disconfirmation_strength=0.1,
            regime_shock=0.05,
            observation_freshness=0.9,
        ),
    )
    full = FullWorkflowRequest(projection=proj_req, state=state_req)
    assert full.projection.projection_id == "p-full"
    assert full.state.snapshot is make_ssv_snapshot
