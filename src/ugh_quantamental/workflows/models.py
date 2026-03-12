"""Request and response models for deterministic workflow composition (v1)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from ugh_quantamental.persistence.repositories import ProjectionRun, StateRun


def make_run_id(prefix: str) -> str:
    """Generate a short opaque run identifier with the given prefix.

    Format: ``"{prefix}{uuid4_hex[:12]}"``.
    """
    return f"{prefix}{uuid.uuid4().hex[:12]}"


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


class FullWorkflowStateRequest(BaseModel):
    """State portion of a full workflow request.

    Does not include ``projection_result``; that is supplied automatically by
    ``run_full_workflow`` from the projection step it just executed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot: SSVSnapshot
    omega: Omega
    event_features: StateEventFeatures
    config: StateConfig = Field(default_factory=StateConfig)
    snapshot_id: str | None = None
    omega_id: str | None = None
    run_id: str | None = None
    created_at: datetime | None = None


class FullWorkflowRequest(BaseModel):
    """Combined request for projection-then-state full workflow execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection: ProjectionWorkflowRequest
    state: FullWorkflowStateRequest


# ---------------------------------------------------------------------------
# Result containers — plain frozen dataclasses so that persistence types
# (ProjectionRun, StateRun) are never imported at module load time; they
# are only referenced via TYPE_CHECKING above.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectionWorkflowResult:
    """Outputs from a completed projection workflow run."""

    run_id: str
    engine_result: ProjectionEngineResult
    persisted_run: ProjectionRun


@dataclass(frozen=True)
class StateWorkflowResult:
    """Outputs from a completed state workflow run."""

    run_id: str
    engine_result: StateEngineResult
    persisted_run: StateRun


@dataclass(frozen=True)
class FullWorkflowResult:
    """Combined outputs from a full projection-then-state workflow execution."""

    projection: ProjectionWorkflowResult
    state: StateWorkflowResult
