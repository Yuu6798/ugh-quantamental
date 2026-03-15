"""Typed request, comparison, and result models for the deterministic replay layer (v1)."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from ugh_quantamental.engine.projection_models import ProjectionEngineResult
from ugh_quantamental.engine.review_audit_models import ReviewAuditEngineResult, ReviewIntentFeatures, ReviewObservation
from ugh_quantamental.engine.state_models import StateEngineResult
from ugh_quantamental.query.models import ProjectionRunBundle, ReviewAuditRunBundle, StateRunBundle


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


# ---------------------------------------------------------------------------
# Review audit engine replay
# ---------------------------------------------------------------------------


class ReviewAuditReplayRequest(BaseModel):
    """Request to replay a persisted review audit run by run_id (engine replay)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str


class ReviewAuditReplayComparison(BaseModel):
    """Explicit deterministic comparison of stored vs recomputed review audit engine result.

    ``exact_match`` uses full JSON equality via Pydantic's ``model_dump(mode="json")``.
    ``snapshot_match`` compares the ``audit_snapshot`` sub-object JSON.
    All scalar diffs are absolute differences (non-negative).
    ``delta_e_diff`` and ``mismatch_score_diff`` are ``None`` when both stored and
    recomputed values are ``None``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    exact_match: bool
    snapshot_match: bool
    por_diff: float
    delta_e_diff: float | None
    mismatch_score_diff: float | None
    verdict_match: bool


@dataclass(frozen=True)
class ReviewAuditReplayResult:
    """Full outcome of replaying a persisted review audit run (engine replay)."""

    bundle: ReviewAuditRunBundle
    recomputed_result: ReviewAuditEngineResult
    comparison: ReviewAuditReplayComparison


# ---------------------------------------------------------------------------
# Review audit extractor replay
# ---------------------------------------------------------------------------


class ReviewAuditExtractorReplayRequest(BaseModel):
    """Request to replay feature extraction for a persisted review audit run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str


class ReviewAuditExtractorReplayComparison(BaseModel):
    """Explicit comparison of stored vs re-extracted observation and intent features.

    ``exact_match`` is ``True`` iff both ``observation_match`` and
    ``intent_features_match`` are ``True``.
    Numeric diffs are absolute differences; boolean/string fields use match flags.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    exact_match: bool
    observation_match: bool
    intent_features_match: bool

    # --- ReviewIntentFeatures numeric diffs ---
    intent_clarity_diff: float
    locality_strength_diff: float
    mechanicalness_diff: float
    scope_boundness_diff: float
    semantic_change_risk_diff: float
    validation_intensity_diff: float

    # --- ReviewObservation numeric count diffs ---
    mechanical_keyword_hits_diff: int
    skip_keyword_hits_diff: int
    ambiguity_signal_count_diff: int

    # --- ReviewObservation non-numeric field matches ---
    has_path_hint_match: bool
    has_line_anchor_match: bool
    has_diff_hunk_match: bool
    priority_match: bool
    behavior_preservation_signal_match: bool
    scope_limit_signal_match: bool
    target_file_present_match: bool
    review_kind_match: bool


@dataclass(frozen=True)
class ReviewAuditExtractorReplayResult:
    """Full outcome of replaying feature extraction for a persisted review audit run."""

    bundle: ReviewAuditRunBundle
    recomputed_observation: ReviewObservation
    recomputed_intent_features: ReviewIntentFeatures
    comparison: ReviewAuditExtractorReplayComparison
