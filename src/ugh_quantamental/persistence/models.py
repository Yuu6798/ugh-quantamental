"""SQLAlchemy ORM models for minimal persistence v1 run records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, JSON, String
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
