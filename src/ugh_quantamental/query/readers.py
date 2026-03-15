"""Synchronous read-only query helpers for persisted run records (v1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import load_only

from ugh_quantamental.persistence.models import (
    ProjectionRunRecord,
    ReviewAuditRunRecord,
    StateRunRecord,
)
from ugh_quantamental.persistence.serializers import (
    projection_payload_to_models,
    review_audit_payload_to_models,
    state_payload_to_models,
)
from ugh_quantamental.query.models import (
    ProjectionRunBundle,
    ProjectionRunQuery,
    ProjectionRunSummary,
    ReviewAuditRunBundle,
    ReviewAuditRunQuery,
    ReviewAuditRunSummary,
    StateRunBundle,
    StateRunQuery,
    StateRunSummary,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def list_projection_run_summaries(
    session: Session,
    query: ProjectionRunQuery,
) -> list[ProjectionRunSummary]:
    """Return lightweight projection run summaries matching the query.

    Ordered newest-first by created_at, then by run_id for deterministic pagination.
    ``point_estimate`` and ``confidence`` are extracted from ``result_json``.
    Only the columns required for the summary are fetched.
    """
    stmt = select(ProjectionRunRecord).options(
        load_only(
            ProjectionRunRecord.run_id,
            ProjectionRunRecord.created_at,
            ProjectionRunRecord.projection_id,
            ProjectionRunRecord.result_json,
        )
    )

    if query.projection_id is not None:
        stmt = stmt.where(ProjectionRunRecord.projection_id == query.projection_id)
    if query.created_at_from is not None:
        stmt = stmt.where(ProjectionRunRecord.created_at >= query.created_at_from)
    if query.created_at_to is not None:
        stmt = stmt.where(ProjectionRunRecord.created_at <= query.created_at_to)

    stmt = stmt.order_by(ProjectionRunRecord.created_at.desc(), ProjectionRunRecord.run_id.asc())
    stmt = stmt.offset(query.offset).limit(query.limit)

    records = session.scalars(stmt).all()
    return [
        ProjectionRunSummary(
            run_id=record.run_id,
            created_at=record.created_at,
            projection_id=record.projection_id,
            point_estimate=record.result_json["projection_snapshot"]["point_estimate"],
            confidence=record.result_json["projection_snapshot"]["confidence"],
        )
        for record in records
    ]


def list_state_run_summaries(
    session: Session,
    query: StateRunQuery,
) -> list[StateRunSummary]:
    """Return lightweight state run summaries matching the query.

    Ordered newest-first by created_at, then by run_id for deterministic pagination.
    All fields are read from typed columns; no JSON columns are loaded.
    """
    stmt = select(StateRunRecord).options(
        load_only(
            StateRunRecord.run_id,
            StateRunRecord.created_at,
            StateRunRecord.snapshot_id,
            StateRunRecord.omega_id,
            StateRunRecord.projection_id,
            StateRunRecord.dominant_state,
            StateRunRecord.transition_confidence,
        )
    )

    if query.snapshot_id is not None:
        stmt = stmt.where(StateRunRecord.snapshot_id == query.snapshot_id)
    if query.omega_id is not None:
        stmt = stmt.where(StateRunRecord.omega_id == query.omega_id)
    if query.projection_id is not None:
        stmt = stmt.where(StateRunRecord.projection_id == query.projection_id)
    if query.dominant_state is not None:
        stmt = stmt.where(StateRunRecord.dominant_state == query.dominant_state)
    if query.created_at_from is not None:
        stmt = stmt.where(StateRunRecord.created_at >= query.created_at_from)
    if query.created_at_to is not None:
        stmt = stmt.where(StateRunRecord.created_at <= query.created_at_to)

    stmt = stmt.order_by(StateRunRecord.created_at.desc(), StateRunRecord.run_id.asc())
    stmt = stmt.offset(query.offset).limit(query.limit)

    records = session.scalars(stmt).all()
    return [
        StateRunSummary(
            run_id=record.run_id,
            created_at=record.created_at,
            snapshot_id=record.snapshot_id,
            omega_id=record.omega_id,
            projection_id=record.projection_id,
            dominant_state=record.dominant_state,
            transition_confidence=record.transition_confidence,
        )
        for record in records
    ]


def get_projection_run_bundle(
    session: Session,
    run_id: str,
) -> ProjectionRunBundle | None:
    """Return a fully-recovered projection run bundle, or None if not found.

    Reconstructs all typed Pydantic models from JSON via existing serializer helpers.
    """
    record = session.get(ProjectionRunRecord, run_id)
    if record is None:
        return None

    question_features, signal_features, alignment_inputs, config, result = (
        projection_payload_to_models({
            "question_features_json": record.question_features_json,
            "signal_features_json": record.signal_features_json,
            "alignment_inputs_json": record.alignment_inputs_json,
            "config_json": record.config_json,
            "result_json": record.result_json,
        })
    )
    return ProjectionRunBundle(
        run_id=record.run_id,
        created_at=record.created_at,
        projection_id=record.projection_id,
        question_features=question_features,
        signal_features=signal_features,
        alignment_inputs=alignment_inputs,
        config=config,
        result=result,
    )


def get_state_run_bundle(
    session: Session,
    run_id: str,
) -> StateRunBundle | None:
    """Return a fully-recovered state run bundle, or None if not found.

    Reconstructs all typed Pydantic models from JSON via existing serializer helpers.
    """
    record = session.get(StateRunRecord, run_id)
    if record is None:
        return None

    snapshot, omega, projection_result, event_features, config, result = (
        state_payload_to_models({
            "snapshot_json": record.snapshot_json,
            "omega_json": record.omega_json,
            "projection_result_json": record.projection_result_json,
            "event_features_json": record.event_features_json,
            "config_json": record.config_json,
            "result_json": record.result_json,
        })
    )
    return StateRunBundle(
        run_id=record.run_id,
        created_at=record.created_at,
        snapshot_id=record.snapshot_id,
        omega_id=record.omega_id,
        projection_id=record.projection_id,
        dominant_state=record.dominant_state,
        transition_confidence=record.transition_confidence,
        snapshot=snapshot,
        omega=omega,
        projection_result=projection_result,
        event_features=event_features,
        config=config,
        result=result,
    )


def list_review_audit_run_summaries(
    session: Session,
    query: ReviewAuditRunQuery,
) -> list[ReviewAuditRunSummary]:
    """Return lightweight review audit run summaries matching the query.

    Ordered newest-first by created_at, then by run_id for deterministic pagination.
    ``por``, ``delta_e``, and ``mismatch_score`` are extracted from ``engine_result_json``.
    Only the columns required for the summary are fetched.
    """
    stmt = select(ReviewAuditRunRecord).options(
        load_only(
            ReviewAuditRunRecord.run_id,
            ReviewAuditRunRecord.created_at,
            ReviewAuditRunRecord.audit_id,
            ReviewAuditRunRecord.pr_number,
            ReviewAuditRunRecord.reviewer_login,
            ReviewAuditRunRecord.verdict,
            ReviewAuditRunRecord.engine_result_json,
        )
    )

    if query.audit_id is not None:
        stmt = stmt.where(ReviewAuditRunRecord.audit_id == query.audit_id)
    if query.pr_number is not None:
        stmt = stmt.where(ReviewAuditRunRecord.pr_number == query.pr_number)
    if query.reviewer_login is not None:
        stmt = stmt.where(ReviewAuditRunRecord.reviewer_login == query.reviewer_login)
    if query.verdict is not None:
        stmt = stmt.where(ReviewAuditRunRecord.verdict == query.verdict)
    if query.created_at_from is not None:
        stmt = stmt.where(ReviewAuditRunRecord.created_at >= query.created_at_from)
    if query.created_at_to is not None:
        stmt = stmt.where(ReviewAuditRunRecord.created_at <= query.created_at_to)

    stmt = stmt.order_by(
        ReviewAuditRunRecord.created_at.desc(), ReviewAuditRunRecord.run_id.asc()
    )
    stmt = stmt.offset(query.offset).limit(query.limit)

    records = session.scalars(stmt).all()
    return [
        ReviewAuditRunSummary(
            run_id=record.run_id,
            created_at=record.created_at,
            audit_id=record.audit_id,
            pr_number=record.pr_number,
            reviewer_login=record.reviewer_login,
            verdict=record.verdict,
            por=record.engine_result_json["audit_snapshot"]["por"],
            delta_e=record.engine_result_json["audit_snapshot"]["delta_e"],
            mismatch_score=record.engine_result_json["audit_snapshot"]["mismatch_score"],
        )
        for record in records
    ]


def get_review_audit_run_bundle(
    session: Session,
    run_id: str,
) -> ReviewAuditRunBundle | None:
    """Return a fully-recovered review audit run bundle, or None if not found.

    Reconstructs all typed models from JSON via existing serializer helpers.
    """
    record = session.get(ReviewAuditRunRecord, run_id)
    if record is None:
        return None

    review_context, observation, intent_features, action_features, result = (
        review_audit_payload_to_models({
            "review_context_json": record.review_context_json,
            "observation_json": record.observation_json,
            "intent_features_json": record.intent_features_json,
            "action_features_json": record.action_features_json,
            "engine_result_json": record.engine_result_json,
        })
    )
    return ReviewAuditRunBundle(
        run_id=record.run_id,
        created_at=record.created_at,
        audit_id=record.audit_id,
        pr_number=record.pr_number,
        reviewer_login=record.reviewer_login,
        verdict=record.verdict,
        extractor_version=record.extractor_version,
        feature_spec_version=record.feature_spec_version,
        review_context=review_context,
        observation=observation,
        intent_features=intent_features,
        action_features=action_features,
        result=result,
    )
