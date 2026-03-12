"""Typed request, comparison, and result models for the deterministic replay layer (v1)."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from ugh_quantamental.engine.projection_models import ProjectionEngineResult
from ugh_quantamental.engine.state_models import StateEngineResult
from ugh_quantamental.query.models import ProjectionRunBundle, StateRunBundle


class ProjectionReplayRequest(BaseModel):
    """Request to replay a persisted projection run by run_id."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str


class StateReplayRequest(BaseModel):
    """Request to replay a persisted state run by run_id."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str


class ProjectionReplayComparison(BaseModel):
    """Explicit deterministic comparison of stored vs recomputed projection result.

    All scalar diffs are absolute differences (non-negative).
    ``exact_match`` uses full JSON equality via Pydantic's ``model_dump(mode="json")``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    exact_match: bool
    projection_snapshot_match: bool
    point_estimate_diff: float
    confidence_diff: float
    mismatch_px_diff: float
    mismatch_sem_diff: float
    conviction_diff: float
    urgency_diff: float


class StateReplayComparison(BaseModel):
    """Explicit deterministic comparison of stored vs recomputed state result.

    ``exact_match`` uses full JSON equality via Pydantic's ``model_dump(mode="json")``.
    Structural flags use direct sub-object JSON equality.
    ``transition_confidence_diff`` is an absolute difference (non-negative).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    exact_match: bool
    dominant_state_match: bool
    transition_confidence_diff: float
    market_svp_match: bool
    updated_probabilities_match: bool


@dataclass(frozen=True)
class ProjectionReplayResult:
    """Full outcome of replaying a persisted projection run."""

    bundle: ProjectionRunBundle
    recomputed_result: ProjectionEngineResult
    comparison: ProjectionReplayComparison


@dataclass(frozen=True)
class StateReplayResult:
    """Full outcome of replaying a persisted state run."""

    bundle: StateRunBundle
    recomputed_result: StateEngineResult
    comparison: StateReplayComparison
