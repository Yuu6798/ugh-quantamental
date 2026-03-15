"""SQLAlchemy ORM models for minimal persistence v1 run records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for persistence v1 models."""


class ProjectionRunRecord(Base):
    """JSON-backed projection run record with searchable metadata columns."""

    __tablename__ = "projection_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    projection_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    question_features_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    signal_features_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    alignment_inputs_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class StateRunRecord(Base):
    """JSON-backed state run record with searchable metadata columns."""

    __tablename__ = "state_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

    snapshot_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    omega_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    projection_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    dominant_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    transition_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    omega_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    projection_result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    event_features_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class FxForecastRecord(Base):
    """JSON-backed FX forecast record with minimal searchable metadata columns."""

    __tablename__ = "fx_forecast_records"

    forecast_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    forecast_batch_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(16), nullable=False)
    strategy_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    as_of_jst: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    window_end_jst: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    protocol_version: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class FxOutcomeRecord(Base):
    """JSON-backed FX outcome record with minimal searchable metadata columns."""

    __tablename__ = "fx_outcome_records"

    outcome_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    pair: Mapped[str] = mapped_column(String(16), nullable=False)
    window_start_jst: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    window_end_jst: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    protocol_version: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class FxEvaluationRecord(Base):
    """JSON-backed FX evaluation record with minimal searchable metadata columns."""

    __tablename__ = "fx_evaluation_records"

    evaluation_id: Mapped[str] = mapped_column(String(512), primary_key=True)
    forecast_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    outcome_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pair: Mapped[str] = mapped_column(String(16), nullable=False)
    strategy_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    window_start_jst: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    window_end_jst: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    protocol_version: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class ReviewAuditRunRecord(Base):
    """JSON-backed review audit run record with searchable metadata columns."""

    __tablename__ = "review_audit_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

    audit_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reviewer_login: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    extractor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_spec_version: Mapped[str] = mapped_column(String(32), nullable=False)

    review_context_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    observation_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    intent_features_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    action_features_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    engine_result_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class RegressionSuiteBaselineRecord(Base):
    """Persisted regression suite baseline (golden snapshot)."""

    __tablename__ = "regression_suite_baselines"

    baseline_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    baseline_name: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    suite_request_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    suite_result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
