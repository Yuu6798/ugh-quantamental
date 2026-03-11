"""Schema models for Market-SVP contracts."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ugh_quantamental.schemas.enums import LifecycleState, MarketRegime


class StateProbabilities(BaseModel):
    """Deterministic six-state lifecycle probability vector."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dormant: float = Field(ge=0.0, le=1.0)
    setup: float = Field(ge=0.0, le=1.0)
    fire: float = Field(ge=0.0, le=1.0)
    expansion: float = Field(ge=0.0, le=1.0)
    exhaustion: float = Field(ge=0.0, le=1.0)
    failure: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_total_probability(self) -> "StateProbabilities":
        total = (
            self.dormant
            + self.setup
            + self.fire
            + self.expansion
            + self.exhaustion
            + self.failure
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError("state probabilities must sum to 1.0")
        return self


class Phi(BaseModel):
    """Lifecycle state-probability envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dominant_state: LifecycleState
    probabilities: StateProbabilities


class MarketSVP(BaseModel):
    """Market state vector primitive for downstream contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: str = Field(min_length=1)
    regime: MarketRegime
    phi: Phi
    confidence: float = Field(ge=0.0, le=1.0)
