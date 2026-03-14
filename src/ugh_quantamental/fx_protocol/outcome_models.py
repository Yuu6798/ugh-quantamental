"""Typed models for the daily FX outcome and evaluation workflow (Phase 2 Milestone 15)."""

from __future__ import annotations

import math
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EvaluationRecord,
    EventTag,
    MarketDataProvenance,
    OutcomeRecord,
    _check_canonical_business_day_window,
    _to_jst,
)


class DailyOutcomeWorkflowRequest(BaseModel):
    """Input contract for recording one canonical outcome and generating per-forecast evaluations.

    ``window_start_jst`` must be 08:00 JST on a protocol business day (Mon–Fri).
    ``window_end_jst`` must be the immediately following business-day 08:00 JST, i.e. equal to
    ``next_as_of_jst(window_start_jst)``.  Both constraints are enforced at construction time.
    All four OHLC prices must be finite and strictly positive.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair: CurrencyPair
    window_start_jst: datetime
    window_end_jst: datetime
    market_data_provenance: MarketDataProvenance
    realized_open: float
    realized_high: float
    realized_low: float
    realized_close: float
    event_tags: tuple[EventTag, ...] = ()
    schema_version: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
    evaluated_at_utc: datetime | None = None

    @field_validator("window_start_jst", "window_end_jst")
    @classmethod
    def _normalize_jst_timestamps(cls, v: datetime) -> datetime:
        """Canonicalize *_jst fields to JST-aware datetimes on ingestion."""
        return _to_jst(v)

    @field_validator("realized_open", "realized_high", "realized_low", "realized_close")
    @classmethod
    def _price_must_be_finite_and_positive(cls, v: float) -> float:
        """Reject non-finite or non-positive prices before outcome construction."""
        if not math.isfinite(v):
            raise ValueError("realized price must be finite")
        if v <= 0:
            raise ValueError("realized price must be positive")
        return v

    @model_validator(mode="after")
    def _validate_canonical_window(self) -> DailyOutcomeWorkflowRequest:
        """Enforce canonical 08:00 JST business-day window semantics.

        Delegates to ``_check_canonical_business_day_window`` which verifies:
        - Both endpoints at exactly 08:00 JST on Mon–Fri.
        - ``window_end_jst`` is the immediately-following business-day 08:00 JST.
        This is equivalent to requiring ``window_end_jst == next_as_of_jst(window_start_jst)``.
        """
        _check_canonical_business_day_window(
            self.window_start_jst,
            self.window_end_jst,
            "window_start_jst",
            "window_end_jst",
        )
        return self


class PersistedOutcomeEvaluationBatch(BaseModel):
    """Result of the daily outcome and evaluation workflow after persistence.

    Contains the one canonical ``OutcomeRecord`` and the four ``EvaluationRecord`` instances
    (one per forecast strategy) that were generated and persisted for the completed window.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: OutcomeRecord
    evaluations: tuple[EvaluationRecord, ...]
