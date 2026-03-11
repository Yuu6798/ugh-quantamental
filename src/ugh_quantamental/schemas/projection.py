"""Schema model for projection output snapshots."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectionSnapshot(BaseModel):
    """Projection output contract (no projection math included)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection_id: str = Field(min_length=1)
    horizon_days: int = Field(ge=1)
    point_estimate: float
    lower_bound: float
    upper_bound: float
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "ProjectionSnapshot":
        if self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound must be <= upper_bound")
        return self
