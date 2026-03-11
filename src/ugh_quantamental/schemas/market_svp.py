"""Schema models for Market-SVP contracts."""

import math

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
        if not math.isclose(total, 1.0, abs_tol=1e-5):
            raise ValueError("state probabilities must sum to 1.0 within tolerance")
        return self


class Phi(BaseModel):
    """Lifecycle state-probability envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dominant_state: LifecycleState
    probabilities: StateProbabilities

    @model_validator(mode="after")
    def validate_dominant_state(self) -> "Phi":
        probability_map = self.probabilities.model_dump()
        max_probability = max(probability_map.values())
        highest_states = [
            state_name
            for state_name, probability in probability_map.items()
            if math.isclose(probability, max_probability, abs_tol=1e-12)
        ]

        if len(highest_states) != 1:
            raise ValueError("dominant_state is ambiguous due to tied highest probabilities")

        if self.dominant_state.value != highest_states[0]:
            raise ValueError("dominant_state must match the unique highest lifecycle probability")

        return self


class MarketSVP(BaseModel):
    """Market state vector primitive for downstream contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: str = Field(min_length=1)
    regime: MarketRegime
    phi: Phi
    confidence: float = Field(ge=0.0, le=1.0)
