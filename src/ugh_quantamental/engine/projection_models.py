"""Normalized deterministic feature contracts for projection math (v1)."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ugh_quantamental.schemas.projection import ProjectionSnapshot


class QuestionDirectionSign(str, Enum):
    """Signed directional interpretation for a normalized question."""

    positive = "positive"
    negative = "negative"
    neutral = "neutral"

    @property
    def sign(self) -> int:
        if self is QuestionDirectionSign.positive:
            return 1
        if self is QuestionDirectionSign.negative:
            return -1
        return 0


class QuestionFeatures(BaseModel):
    """Normalized question features consumed by deterministic projection math."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question_direction: QuestionDirectionSign
    q_strength: float = Field(ge=0.0, le=1.0)
    s_q: float = Field(ge=0.0, le=1.0)
    temporal_score: float = Field(ge=0.0, le=1.0)


class SignalFeatures(BaseModel):
    """Normalized deterministic signal block inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fundamental_score: float = Field(ge=-1.0, le=1.0)
    technical_score: float = Field(ge=-1.0, le=1.0)
    price_implied_score: float = Field(ge=-1.0, le=1.0)
    context_score: float = Field(ge=0.0, le=2.0)
    grv_lock: float = Field(ge=0.0, le=1.0)
    regime_fit: float = Field(ge=0.0, le=1.0)
    narrative_dispersion: float = Field(ge=0.0, le=1.0)
    evidence_confidence: float = Field(ge=0.0, le=1.0)
    fire_probability: float = Field(ge=0.0, le=1.0)


class AlignmentInputs(BaseModel):
    """Pairwise normalized disagreement (gap) inputs and optional weighting."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    d_qf: float = Field(ge=0.0, le=1.0)
    d_qt: float = Field(ge=0.0, le=1.0)
    d_qp: float = Field(ge=0.0, le=1.0)
    d_ft: float = Field(ge=0.0, le=1.0)
    d_fp: float = Field(ge=0.0, le=1.0)
    d_tp: float = Field(ge=0.0, le=1.0)

    w_qf: float = Field(default=1.0, ge=0.0)
    w_qt: float = Field(default=1.0, ge=0.0)
    w_qp: float = Field(default=1.0, ge=0.0)
    w_ft: float = Field(default=1.0, ge=0.0)
    w_fp: float = Field(default=1.0, ge=0.0)
    w_tp: float = Field(default=1.0, ge=0.0)


class ProjectionConfig(BaseModel):
    """Configuration coefficients for deterministic v1 projection calculations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    u_weight: float = Field(default=0.5, ge=0.0)
    f_weight: float = Field(default=0.3, ge=0.0)
    t_weight: float = Field(default=0.2, ge=0.0)

    pair_weight_qf: float = Field(default=1.0, ge=0.0)
    pair_weight_qt: float = Field(default=1.0, ge=0.0)
    pair_weight_qp: float = Field(default=1.0, ge=0.0)
    pair_weight_ft: float = Field(default=1.0, ge=0.0)
    pair_weight_fp: float = Field(default=1.0, ge=0.0)
    pair_weight_tp: float = Field(default=1.0, ge=0.0)

    gravity_lock_coef: float = 0.20
    gravity_regime_coef: float = 0.15
    gravity_dispersion_coef: float = 0.10

    bounds_base_width: float = Field(default=0.10, ge=0.0)
    bounds_mismatch_coef: float = Field(default=0.20, ge=0.0)
    bounds_low_conf_coef: float = Field(default=0.25, ge=0.0)
    bounds_urgency_coef: float = Field(default=0.15, ge=0.0)
    bounds_max_width: float = Field(default=1.0, gt=0.0)


class ProjectionEngineResult(BaseModel):
    """Rich deterministic output from the v1 projection engine."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    u_score: float
    alignment: float
    e_raw: float
    gravity_bias: float
    e_star: float
    mismatch_px: float
    mismatch_sem: float
    conviction: float
    urgency: float
    projection_snapshot: ProjectionSnapshot
