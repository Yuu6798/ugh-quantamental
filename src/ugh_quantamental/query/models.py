"""Read-only query and summary models for the inspection layer (v1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEngineResult, StateEventFeatures
from ugh_quantamental.schemas.omega import Omega
from ugh_quantamental.schemas.ssv import SSVSnapshot


class CreatedAtRange(BaseModel):
    """Closed-ended naive-UTC date range for created_at filtering."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    created_at_from: datetime | None = None
    created_at_to: datetime | None = None


class ProjectionRunQuery(BaseModel):
    """Filter parameters for listing projection run summaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection_id: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class StateRunQuery(BaseModel):
    """Filter parameters for listing state run summaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str | None = None
    omega_id: str | None = None
    projection_id: str | None = None
    dominant_state: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ProjectionRunSummary(BaseModel):
    """Lightweight read-only view of a persisted projection run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    created_at: datetime
    projection_id: str
    point_estimate: float
    confidence: float


class StateRunSummary(BaseModel):
    """Lightweight read-only view of a persisted state run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    created_at: datetime
    snapshot_id: str
    omega_id: str
    projection_id: str | None
    dominant_state: str
    transition_confidence: float


@dataclass(frozen=True)
class ProjectionRunBundle:
    """Fully-recovered projection run with all typed models reconstructed from JSON."""

    run_id: str
    created_at: datetime
    projection_id: str
    question_features: QuestionFeatures
    signal_features: SignalFeatures
    alignment_inputs: AlignmentInputs
    config: ProjectionConfig
    result: ProjectionEngineResult


@dataclass(frozen=True)
class StateRunBundle:
    """Fully-recovered state run with all typed models reconstructed from JSON."""

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
