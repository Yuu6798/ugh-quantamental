"""Synchronous read-only query helpers for persisted run records (v1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from ugh_quantamental.persistence.models import ProjectionRunRecord, StateRunRecord
from ugh_quantamental.persistence.serializers import (
    projection_payload_to_models,
    state_payload_to_models,
)
from ugh_quantamental.query.models import (
    ProjectionRunBundle,
    ProjectionRunQuery,
    ProjectionRunSummary,
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

    Ordered newest-first by created_at. Applies offset and limit.
    ``point_estimate`` and ``confidence`` are extracted from ``result_json``.
    """
    stmt = select(ProjectionRunRecord)

    if query.projection_id is not None:
        stmt = stmt.where(ProjectionRunRecord.projection_id == query.projection_id)
    if query.created_at_from is not None:
        stmt = stmt.where(ProjectionRunRecord.created_at >= query.created_at_from)
    if query.created_at_to is not None:
        stmt = stmt.where(ProjectionRunRecord.created_at <= query.created_at_to)

    stmt = stmt.order_by(ProjectionRunRecord.created_at.desc())
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

    Ordered newest-first by created_at. Applies offset and limit.
    All fields are read from typed columns; no JSON parsing required.
    """
    stmt = select(StateRunRecord)

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

    stmt = stmt.order_by(StateRunRecord.created_at.desc())
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
        projection_payload_to_models(record.__dict__)
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
        state_payload_to_models(record.__dict__)
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
