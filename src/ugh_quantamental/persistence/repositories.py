"""Minimal repositories for saving/loading deterministic projection and state runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEngineResult, StateEventFeatures
from ugh_quantamental.persistence.models import ProjectionRunRecord, StateRunRecord
from ugh_quantamental.persistence.serializers import (
    dump_model_json,
    projection_payload_to_models,
    state_payload_to_models,
)
from ugh_quantamental.schemas.omega import Omega
from ugh_quantamental.schemas.ssv import SSVSnapshot


@dataclass(frozen=True)
class ProjectionRun:
    run_id: str
    created_at: datetime
    projection_id: str
    question_features: QuestionFeatures
    signal_features: SignalFeatures
    alignment_inputs: AlignmentInputs
    config: ProjectionConfig
    result: ProjectionEngineResult


@dataclass(frozen=True)
class StateRun:
    run_id: str
    created_at: datetime
    snapshot_id: str
    omega_id: str
    projection_id: str | None
    dominant_state: str
    transition_confidence: float
    snapshot: SSVSnapshot
    omega: Omega
    projection_result: ProjectionEngineResult
    event_features: StateEventFeatures
    config: StateConfig
    result: StateEngineResult


class ProjectionRunRepository:
    """Persistence adapter for projection run records."""

    @staticmethod
    def save_run(
        session: Session,
        *,
        run_id: str,
        projection_id: str,
        question_features: QuestionFeatures,
        signal_features: SignalFeatures,
        alignment_inputs: AlignmentInputs,
        config: ProjectionConfig,
        result: ProjectionEngineResult,
        created_at: datetime | None = None,
    ) -> ProjectionRunRecord:
        record = ProjectionRunRecord(
            run_id=run_id,
            created_at=(created_at or datetime.now(timezone.utc)).replace(tzinfo=None),
            projection_id=projection_id,
            question_features_json=dump_model_json(question_features),
            signal_features_json=dump_model_json(signal_features),
            alignment_inputs_json=dump_model_json(alignment_inputs),
            config_json=dump_model_json(config),
            result_json=dump_model_json(result),
        )
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def load_run(session: Session, run_id: str) -> ProjectionRun | None:
        record = session.get(ProjectionRunRecord, run_id)
        if record is None:
            return None

        question_features, signal_features, alignment_inputs, config, result = (
            projection_payload_to_models(record.__dict__)
        )
        return ProjectionRun(
            run_id=record.run_id,
            created_at=record.created_at,
            projection_id=record.projection_id,
            question_features=question_features,
            signal_features=signal_features,
            alignment_inputs=alignment_inputs,
            config=config,
            result=result,
        )


class StateRunRepository:
    """Persistence adapter for state run records."""

    @staticmethod
    def save_run(
        session: Session,
        *,
        run_id: str,
        snapshot_id: str,
        omega_id: str,
        projection_id: str | None,
        dominant_state: str,
        transition_confidence: float,
        snapshot: SSVSnapshot,
        omega: Omega,
        projection_result: ProjectionEngineResult,
        event_features: StateEventFeatures,
        config: StateConfig,
        result: StateEngineResult,
        created_at: datetime | None = None,
    ) -> StateRunRecord:
        record = StateRunRecord(
            run_id=run_id,
            created_at=(created_at or datetime.now(timezone.utc)).replace(tzinfo=None),
            snapshot_id=snapshot_id,
            omega_id=omega_id,
            projection_id=projection_id,
            dominant_state=dominant_state,
            transition_confidence=transition_confidence,
            snapshot_json=dump_model_json(snapshot),
            omega_json=dump_model_json(omega),
            projection_result_json=dump_model_json(projection_result),
            event_features_json=dump_model_json(event_features),
            config_json=dump_model_json(config),
            result_json=dump_model_json(result),
        )
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def load_run(session: Session, run_id: str) -> StateRun | None:
        record = session.get(StateRunRecord, run_id)
        if record is None:
            return None

        snapshot, omega, projection_result, event_features, config, result = state_payload_to_models(
            record.__dict__
        )
        return StateRun(
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
