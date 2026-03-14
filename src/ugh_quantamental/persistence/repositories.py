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
from sqlalchemy import select

from ugh_quantamental.persistence.models import (
    FxEvaluationRecord,
    FxForecastRecord,
    FxOutcomeRecord,
    ProjectionRunRecord,
    RegressionSuiteBaselineRecord,
    StateRunRecord,
)
from ugh_quantamental.fx_protocol.forecast_models import PersistedDailyForecastBatch
from ugh_quantamental.fx_protocol.models import EvaluationRecord, ForecastRecord, OutcomeRecord
from ugh_quantamental.persistence.serializers import (
    dump_model_json,
    projection_payload_to_models,
    state_payload_to_models,
)
from ugh_quantamental.schemas.omega import Omega
from ugh_quantamental.schemas.ssv import SSVSnapshot


def _normalize_created_at(created_at: datetime | None) -> datetime:
    """Normalize timestamps to naive UTC for storage in timezone=False columns."""
    if created_at is None:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    if created_at.tzinfo is None:
        return created_at
    return created_at.astimezone(timezone.utc).replace(tzinfo=None)


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
            created_at=_normalize_created_at(created_at),
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


@dataclass(frozen=True)
class RegressionSuiteBaselineRun:
    """Rehydrated regression suite baseline record from the persistence layer."""

    baseline_id: str
    baseline_name: str
    created_at: datetime
    description: str | None
    suite_request_json: dict
    suite_result_json: dict


class RegressionSuiteBaselineRepository:
    """Persistence adapter for regression suite baseline records."""

    @staticmethod
    def save_baseline(
        session: Session,
        *,
        baseline_id: str,
        baseline_name: str,
        created_at: datetime | None = None,
        description: str | None = None,
        suite_request_json: dict,
        suite_result_json: dict,
    ) -> RegressionSuiteBaselineRecord:
        """Persist a new baseline record. Flushes but does not commit."""
        record = RegressionSuiteBaselineRecord(
            baseline_id=baseline_id,
            baseline_name=baseline_name,
            created_at=_normalize_created_at(created_at),
            description=description,
            suite_request_json=suite_request_json,
            suite_result_json=suite_result_json,
        )
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def load_baseline(session: Session, baseline_id: str) -> RegressionSuiteBaselineRun | None:
        """Load a baseline record by primary key."""
        record = session.get(RegressionSuiteBaselineRecord, baseline_id)
        if record is None:
            return None
        return RegressionSuiteBaselineRepository._to_run(record)

    @staticmethod
    def load_baseline_by_name(
        session: Session, baseline_name: str
    ) -> RegressionSuiteBaselineRun | None:
        """Load a baseline record by unique name."""
        record = session.execute(
            select(RegressionSuiteBaselineRecord).where(
                RegressionSuiteBaselineRecord.baseline_name == baseline_name
            )
        ).scalar_one_or_none()
        if record is None:
            return None
        return RegressionSuiteBaselineRepository._to_run(record)

    @staticmethod
    def _to_run(record: RegressionSuiteBaselineRecord) -> RegressionSuiteBaselineRun:
        return RegressionSuiteBaselineRun(
            baseline_id=record.baseline_id,
            baseline_name=record.baseline_name,
            created_at=record.created_at,
            description=record.description,
            suite_request_json=record.suite_request_json,
            suite_result_json=record.suite_result_json,
        )


class FxForecastRepository:
    """Persistence adapter for FX forecast batch records."""

    @staticmethod
    def save_fx_forecast_batch(
        session: Session,
        *,
        forecast_batch_id: str,
        forecasts: tuple[ForecastRecord, ...],
    ) -> PersistedDailyForecastBatch:
        for forecast in forecasts:
            record = FxForecastRecord(
                forecast_id=forecast.forecast_id,
                forecast_batch_id=forecast_batch_id,
                pair=forecast.pair.value,
                strategy_kind=forecast.strategy_kind.value,
                as_of_jst=_normalize_created_at(forecast.as_of_jst),
                window_end_jst=_normalize_created_at(forecast.window_end_jst),
                protocol_version=forecast.protocol_version,
                payload_json=dump_model_json(forecast),
            )
            session.add(record)
        session.flush()
        return PersistedDailyForecastBatch(
            forecast_batch_id=forecast_batch_id,
            forecasts=forecasts,
        )

    @staticmethod
    def load_fx_forecast_batch(
        session: Session,
        forecast_batch_id: str,
    ) -> PersistedDailyForecastBatch | None:
        records = tuple(
            session.execute(
                select(FxForecastRecord)
                .where(FxForecastRecord.forecast_batch_id == forecast_batch_id)
                .order_by(FxForecastRecord.forecast_id.asc())
            ).scalars()
        )
        if not records:
            return None

        forecasts = tuple(
            ForecastRecord.model_validate(record.payload_json)
            for record in records
        )
        return PersistedDailyForecastBatch(
            forecast_batch_id=forecast_batch_id,
            forecasts=forecasts,
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
            created_at=_normalize_created_at(created_at),
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


class FxOutcomeEvaluationRepository:
    """Persistence adapter for FX outcome and evaluation records."""

    @staticmethod
    def save_fx_outcome_record(
        session: Session,
        *,
        outcome: OutcomeRecord,
    ) -> FxOutcomeRecord:
        """Persist a canonical FX outcome record. Flushes but does not commit."""
        record = FxOutcomeRecord(
            outcome_id=outcome.outcome_id,
            pair=outcome.pair.value,
            window_start_jst=_normalize_created_at(outcome.window_start_jst),
            window_end_jst=_normalize_created_at(outcome.window_end_jst),
            protocol_version=outcome.protocol_version,
            payload_json=dump_model_json(outcome),
        )
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def load_fx_outcome_record(session: Session, outcome_id: str) -> OutcomeRecord | None:
        """Load a canonical FX outcome record by primary key."""
        record = session.get(FxOutcomeRecord, outcome_id)
        if record is None:
            return None
        return OutcomeRecord.model_validate(record.payload_json)

    @staticmethod
    def save_fx_evaluation_batch(
        session: Session,
        *,
        outcome_id: str,
        evaluations: tuple[EvaluationRecord, ...],
    ) -> tuple[FxEvaluationRecord, ...]:
        """Persist a batch of FX evaluation records. Flushes but does not commit.

        Requires the corresponding ``FxOutcomeRecord`` to already be present in the session
        so that ``window_start_jst`` / ``window_end_jst`` columns can be populated.
        """
        outcome_rec = session.get(FxOutcomeRecord, outcome_id)
        if outcome_rec is None:
            raise ValueError(
                f"Cannot save evaluations: FxOutcomeRecord {outcome_id!r} not found. "
                "Save the outcome first."
            )
        records = []
        for evaluation in evaluations:
            record = FxEvaluationRecord(
                evaluation_id=evaluation.evaluation_id,
                forecast_id=evaluation.forecast_id,
                outcome_id=outcome_id,
                pair=evaluation.pair.value,
                strategy_kind=evaluation.strategy_kind.value,
                window_start_jst=outcome_rec.window_start_jst,
                window_end_jst=outcome_rec.window_end_jst,
                protocol_version=evaluation.protocol_version,
                payload_json=dump_model_json(evaluation),
            )
            session.add(record)
            records.append(record)
        session.flush()
        return tuple(records)

    @staticmethod
    def load_fx_evaluation_batch(
        session: Session,
        outcome_id: str,
    ) -> tuple[EvaluationRecord, ...] | None:
        """Load all evaluation records for a given outcome_id.

        Returns ``None`` if no records exist, or a tuple of ``EvaluationRecord`` instances.
        """
        records = tuple(
            session.execute(
                select(FxEvaluationRecord)
                .where(FxEvaluationRecord.outcome_id == outcome_id)
                .order_by(FxEvaluationRecord.evaluation_id.asc())
            ).scalars()
        )
        if not records:
            return None
        return tuple(
            EvaluationRecord.model_validate(record.payload_json) for record in records
        )
