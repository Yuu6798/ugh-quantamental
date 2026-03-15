"""Deterministic workflow runners composing projection engine, state engine, and persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from ugh_quantamental.engine.projection import run_projection_engine
from ugh_quantamental.engine.review_audit import run_review_audit_engine
from ugh_quantamental.engine.state import run_state_engine
from ugh_quantamental.persistence.repositories import (
    ProjectionRunRepository,
    ReviewAuditRunRepository,
    StateRunRepository,
)
from ugh_quantamental.workflows.models import (
    FullWorkflowRequest,
    FullWorkflowResult,
    ProjectionWorkflowRequest,
    ProjectionWorkflowResult,
    ReviewAuditWorkflowRequest,
    ReviewAuditWorkflowResult,
    StateWorkflowRequest,
    StateWorkflowResult,
    make_run_id,  # re-exported for callers who import from runners
)


def run_projection_workflow(
    session: Session,
    request: ProjectionWorkflowRequest,
) -> ProjectionWorkflowResult:
    """Run the projection engine, persist the result, reload it, and return both.

    The caller owns the session and must commit or roll back after this call returns.
    """
    run_id = request.run_id or make_run_id("proj-")

    engine_result = run_projection_engine(
        request.projection_id,
        request.horizon_days,
        request.question_features,
        request.signal_features,
        request.alignment_inputs,
        request.config,
    )

    ProjectionRunRepository.save_run(
        session,
        run_id=run_id,
        projection_id=request.projection_id,
        question_features=request.question_features,
        signal_features=request.signal_features,
        alignment_inputs=request.alignment_inputs,
        config=request.config,
        result=engine_result,
        created_at=request.created_at,
    )

    persisted_run = ProjectionRunRepository.load_run(session, run_id)
    if persisted_run is None:
        raise RuntimeError(f"Failed to reload projection run {run_id!r} after save")

    return ProjectionWorkflowResult(
        run_id=run_id,
        engine_result=engine_result,
        persisted_run=persisted_run,
    )


def run_state_workflow(
    session: Session,
    request: StateWorkflowRequest,
) -> StateWorkflowResult:
    """Run the state engine, persist the result, reload it, and return both.

    The caller owns the session and must commit or roll back after this call returns.
    """
    run_id = request.run_id or make_run_id("state-")
    snapshot_id = request.snapshot_id or request.snapshot.snapshot_id
    omega_id = request.omega_id or request.omega.omega_id
    projection_id = (
        request.projection_id
        or request.projection_result.projection_snapshot.projection_id
    )

    engine_result = run_state_engine(
        request.snapshot,
        request.omega,
        request.projection_result,
        request.event_features,
        request.config,
    )

    StateRunRepository.save_run(
        session,
        run_id=run_id,
        snapshot_id=snapshot_id,
        omega_id=omega_id,
        projection_id=projection_id,
        dominant_state=engine_result.dominant_state.value,
        transition_confidence=engine_result.transition_confidence,
        snapshot=request.snapshot,
        omega=request.omega,
        projection_result=request.projection_result,
        event_features=request.event_features,
        config=request.config,
        result=engine_result,
        created_at=request.created_at,
    )

    persisted_run = StateRunRepository.load_run(session, run_id)
    if persisted_run is None:
        raise RuntimeError(f"Failed to reload state run {run_id!r} after save")

    return StateWorkflowResult(
        run_id=run_id,
        engine_result=engine_result,
        persisted_run=persisted_run,
    )


def run_review_audit_workflow(
    session: Session,
    request: ReviewAuditWorkflowRequest,
) -> ReviewAuditWorkflowResult:
    """Run the review audit engine, persist the result, reload it, and return both.

    The caller owns the session and must commit or roll back after this call returns.
    """
    run_id = request.run_id or make_run_id("raudit-")

    engine_result = run_review_audit_engine(
        audit_id=request.audit_id,
        intent=request.intent_features,
        action=request.action_features,
        config=request.config,
    )

    ReviewAuditRunRepository.save_run(
        session,
        run_id=run_id,
        review_context=request.review_context,
        observation=request.observation,
        result=engine_result,
        created_at=request.created_at,
    )

    persisted_run = ReviewAuditRunRepository.load_run(session, run_id)
    if persisted_run is None:
        raise RuntimeError(f"Failed to reload review audit run {run_id!r} after save")

    return ReviewAuditWorkflowResult(
        run_id=run_id,
        engine_result=engine_result,
        persisted_run=persisted_run,
    )


def run_full_workflow(
    session: Session,
    request: FullWorkflowRequest,
) -> FullWorkflowResult:
    """Run projection then state in sequence, persisting both within the same session.

    The projection result is automatically fed into the state workflow.
    The projection_id from the projection snapshot is propagated into state persistence.
    The caller owns the session and must commit or roll back.
    """
    proj_result = run_projection_workflow(session, request.projection)

    derived_projection_id = proj_result.engine_result.projection_snapshot.projection_id

    state_request = StateWorkflowRequest(
        snapshot=request.state.snapshot,
        omega=request.state.omega,
        projection_result=proj_result.engine_result,  # injected from projection output
        event_features=request.state.event_features,
        config=request.state.config,
        snapshot_id=request.state.snapshot_id,
        omega_id=request.state.omega_id,
        projection_id=derived_projection_id,
        run_id=request.state.run_id,
        created_at=request.state.created_at,
    )

    state_result = run_state_workflow(session, state_request)

    return FullWorkflowResult(
        projection=proj_result,
        state=state_result,
    )
