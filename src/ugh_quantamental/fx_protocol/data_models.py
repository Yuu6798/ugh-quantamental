"""Typed market-data contracts for the FX Daily Automation layer (v1)."""

from __future__ import annotations

import math
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EventTag,
    MarketDataProvenance,
    _check_canonical_business_day_window,
    _to_jst,
)


class FxCompletedWindow(BaseModel):
    """One completed OHLC window with event annotations.

    Both ``window_start_jst`` and ``window_end_jst`` must be at exactly 08:00 JST
    on consecutive protocol business days (Mon–Fri), matching the canonical protocol
    window semantics defined in ``models.py``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    window_start_jst: datetime
    window_end_jst: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    event_tags: tuple[EventTag, ...] = ()

    @field_validator("window_start_jst", "window_end_jst")
    @classmethod
    def _normalize_jst(cls, v: datetime) -> datetime:
        """Canonicalize *_jst timestamps to JST-aware datetimes."""
        return _to_jst(v)

    @field_validator("open_price", "high_price", "low_price", "close_price")
    @classmethod
    def _price_finite_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("price must be finite")
        if v <= 0:
            raise ValueError("price must be positive")
        return v

    @model_validator(mode="after")
    def _validate_window(self) -> "FxCompletedWindow":
        _check_canonical_business_day_window(
            self.window_start_jst,
            self.window_end_jst,
            "window_start_jst",
            "window_end_jst",
        )
        if self.high_price < self.low_price:
            raise ValueError("high_price must be >= low_price")
        if not (self.low_price <= self.open_price <= self.high_price):
            raise ValueError("open_price must be within [low_price, high_price]")
        if not (self.low_price <= self.close_price <= self.high_price):
            raise ValueError("close_price must be within [low_price, high_price]")
        return self


class FxProtocolMarketSnapshot(BaseModel):
    """Provider output for one USDJPY market data fetch.

    ``completed_windows`` must be ordered oldest→newest and contain at least
    20 entries.  The newest completed window is used for outcome/evaluation of
    the prior forecast; the full set drives baseline-context derivation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair: CurrencyPair
    as_of_jst: datetime
    current_spot: float
    completed_windows: tuple[FxCompletedWindow, ...] = Field(min_length=20)
    market_data_provenance: MarketDataProvenance

    @field_validator("as_of_jst")
    @classmethod
    def _normalize_as_of(cls, v: datetime) -> datetime:
        return _to_jst(v)

    @field_validator("current_spot")
    @classmethod
    def _spot_finite_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("current_spot must be finite")
        if v <= 0:
            raise ValueError("current_spot must be positive")
        return v

    @model_validator(mode="after")
    def _windows_ordered(self) -> "FxProtocolMarketSnapshot":
        """Enforce oldest→newest ordering of completed_windows."""
        wins = self.completed_windows
        for i in range(len(wins) - 1):
            if wins[i].window_start_jst >= wins[i + 1].window_start_jst:
                raise ValueError(
                    "completed_windows must be ordered oldest→newest "
                    f"(index {i} start={wins[i].window_start_jst} "
                    f">= index {i + 1} start={wins[i + 1].window_start_jst})"
                )
        return self
