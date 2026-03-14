"""Typed models for the daily FX forecast workflow (Phase 2 Milestone 14)."""

from __future__ import annotations

import math
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ugh_quantamental.fx_protocol.calendar import is_protocol_business_day
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    ForecastRecord,
    MarketDataProvenance,
)
from ugh_quantamental.workflows.models import FullWorkflowRequest


class BaselineContext(BaseModel):
    """Deterministic baseline context needed to construct daily baseline forecasts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    current_spot: float
    previous_close_change_bp: float | None
    trailing_mean_range_price: float
    trailing_mean_abs_close_change_bp: float
    sma5: float | None
    sma20: float | None
    warmup_window_count: int = Field(ge=0)

    @field_validator(
        "current_spot",
        "trailing_mean_range_price",
        "trailing_mean_abs_close_change_bp",
        "sma5",
        "sma20",
        "previous_close_change_bp",
    )
    @classmethod
    def _finite_or_none(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("value must be finite")
        return v

    @model_validator(mode="after")
    def _validate_ranges(self) -> "BaselineContext":
        if self.trailing_mean_range_price <= 0:
            raise ValueError("trailing_mean_range_price must be > 0")
        if self.trailing_mean_abs_close_change_bp < 0:
            raise ValueError("trailing_mean_abs_close_change_bp must be >= 0")
        return self


class DailyForecastWorkflowRequest(BaseModel):
    """Input contract for deterministic daily FX forecast batch generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair: CurrencyPair
    as_of_jst: datetime
    market_data_provenance: MarketDataProvenance
    input_snapshot_ref: str = Field(min_length=1)
    ugh_request: FullWorkflowRequest
    baseline_context: BaselineContext
    theory_version: str = Field(min_length=1)
    engine_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    locked_at_utc: datetime | None = None

    @field_validator("as_of_jst")
    @classmethod
    def _as_of_must_be_protocol_open(cls, v: datetime) -> datetime:
        if not is_protocol_business_day(v, tz="Asia/Tokyo"):
            raise ValueError("as_of_jst must be a protocol business day")
        if (v.hour, v.minute, v.second, v.microsecond) != (8, 0, 0, 0):
            raise ValueError("as_of_jst must be exactly 08:00 JST")
        return v

    @model_validator(mode="after")
    def _warmup_guard(self) -> "DailyForecastWorkflowRequest":
        if self.baseline_context.warmup_window_count < 20:
            raise ValueError("baseline_context.warmup_window_count must be >= 20")
        return self


class DailyForecastBatch(BaseModel):
    """In-memory generated forecast batch prior to persistence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    forecast_batch_id: str = Field(min_length=1)
    pair: CurrencyPair
    as_of_jst: datetime
    window_end_jst: datetime
    forecasts: tuple[ForecastRecord, ...] = Field(min_length=1)


class PersistedDailyForecastBatch(BaseModel):
    """Persisted daily forecast batch payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    forecast_batch_id: str = Field(min_length=1)
    forecasts: tuple[ForecastRecord, ...] = Field(min_length=1)
