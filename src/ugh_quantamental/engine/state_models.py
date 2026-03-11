"""Deterministic normalized inputs/config/results for the v1 state engine."""

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from ugh_quantamental.schemas.enums import LifecycleState
from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities


class StateEventFeatures(BaseModel):
    """Normalized event features used by deterministic state evidence rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    catalyst_strength: float = Field(ge=0.0, le=1.0)
    follow_through: float = Field(ge=0.0, le=1.0)
    pricing_saturation: float = Field(ge=0.0, le=1.0)
    disconfirmation_strength: float = Field(ge=0.0, le=1.0)
    regime_shock: float = Field(ge=0.0, le=1.0)
    observation_freshness: float = Field(ge=0.0, le=1.0)


class StateConfig(BaseModel):
    """Deterministic coefficients for prior blending, evidence shaping, and confidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    prior_weight: FiniteFloat = Field(default=0.55, ge=0.0, le=1.0)
    evidence_weight: FiniteFloat = Field(default=0.45, ge=0.0, le=1.0)
    softmax_temperature: FiniteFloat = Field(default=1.0, ge=1e-8)
    tie_break_epsilon: FiniteFloat = Field(default=1e-8, ge=1e-8, le=1e-4)

    dormant_weight: FiniteFloat = Field(default=1.0, ge=0.0)
    setup_weight: FiniteFloat = Field(default=1.0, ge=0.0)
    fire_weight: FiniteFloat = Field(default=1.0, ge=0.0)
    expansion_weight: FiniteFloat = Field(default=1.0, ge=0.0)
    exhaustion_weight: FiniteFloat = Field(default=1.0, ge=0.0)
    failure_weight: FiniteFloat = Field(default=1.0, ge=0.0)

    quality_confidence_weight: FiniteFloat = Field(default=0.55, ge=0.0, le=1.0)
    transition_confidence_weight: FiniteFloat = Field(default=0.45, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_blend_weight_sum(self) -> "StateConfig":
        if self.prior_weight + self.evidence_weight <= 0.0:
            raise ValueError("prior_weight + evidence_weight must be positive")
        return self

class StateEngineResult(BaseModel):
    """Deterministic state engine outputs for downstream use."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_scores: StateProbabilities
    updated_probabilities: StateProbabilities
    updated_phi: Phi
    updated_market_svp: MarketSVP
    dominant_state: LifecycleState
    transition_confidence: float = Field(ge=0.0, le=1.0)
