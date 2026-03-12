"""Request and response models for deterministic workflow composition (v1)."""

from __future__ import annotations

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
from ugh_quantamental.persistence.repositories import ProjectionRun, StateRun
from ugh_quantamental.schemas.omega import Omega
from ugh_quantamental.schemas.ssv import SSVSnapshot


class ProjectionWorkflowRequest(BaseModel):
    """All inputs needed to run and persist a single deterministic projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection_id: str = Field(min_length=1)
    horizon_days: int = Field(ge=1)
    question_features: QuestionFeatures
    signal_features: SignalFeatures
    alignment_inputs: AlignmentInputs
    config: ProjectionConfig = Field(default_factory=ProjectionConfig)
    run_id: str | None = None
    created_at: datetime | None = None


class StateWorkflowRequest(BaseModel):
    """All inputs needed to run and persist a single deterministic state update."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot: SSVSnapshot
    omega: Omega
    projection_result: ProjectionEngineResult
    event_features: StateEventFeatures
    config: StateConfig = Field(default_factory=StateConfig)
    snapshot_id: str | None = None
    omega_id: str | None = None
    projection_id: str | None = None
    run_id: str | None = None
    created_at: datetime | None = None


class FullWorkflowRequest(BaseModel):
    """Combined request for projection-then-state full workflow execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection: ProjectionWorkflowRequest
    state: StateWorkflowRequest


class ProjectionWorkflowResult(BaseModel):
    """Outputs from a completed projection workflow run."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    run_id: str
    engine_result: ProjectionEngineResult
    persisted_run: ProjectionRun


class StateWorkflowResult(BaseModel):
    """Outputs from a completed state workflow run."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    run_id: str
    engine_result: StateEngineResult
    persisted_run: StateRun


class FullWorkflowResult(BaseModel):
    """Combined outputs from a full projection-then-state workflow execution."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    projection: ProjectionWorkflowResult
    state: StateWorkflowResult
