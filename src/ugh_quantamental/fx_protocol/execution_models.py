"""Typed records for the FX execution layer v1 (``docs/specs/fx_execution_layer_v1.md``).

The execution layer sits *outside* the forecast engine: it consumes a persisted
daily forecast batch and records one paper-trading decision per book
(:class:`BookId`, spec §4), then one evaluation per decision once the window's
outcome is known (spec §5). Records are frozen ``extra="forbid"`` contracts and
use the same timestamp canonicalization as :mod:`fx_protocol.models`:
``*_jst`` fields are stored JST-aware, ``*_utc`` fields UTC-aware, so the same
instant never serializes two ways.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import math
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ugh_quantamental.fx_protocol.models import (
    ForecastDirection,
    StrategyKind,
    _to_aware_utc,
    _to_jst,
)

# ---------------------------------------------------------------------------
# Enumerations / literals
# ---------------------------------------------------------------------------


class BookId(str, Enum):
    """Pre-registered paper-trading books (spec §4), frozen under ``execution_version = "x1"``.

    Definition order is the canonical row order emitted by
    :func:`ugh_quantamental.fx_protocol.execution.build_execution_decisions`.
    """

    ugh_x1 = "ugh_x1"
    ugh_beta_unit = "ugh_beta_unit"
    ugh_consensus = "ugh_consensus"
    ugh_divergence = "ugh_divergence"
    bench_gpt_m3 = "bench_gpt_m3"
    bench_long = "bench_long"


#: Canonical book order: one decision / evaluation row per book per window, in this order.
EXECUTION_BOOK_ORDER: tuple[BookId, ...] = (
    BookId.ugh_x1,
    BookId.ugh_beta_unit,
    BookId.ugh_consensus,
    BookId.ugh_divergence,
    BookId.bench_gpt_m3,
    BookId.bench_long,
)

#: Why a book stayed out of the market on a window (spec §4 ``skip_reason`` column).
SkipReason = Literal[
    "flat",
    "shock_filter",
    "no_consensus",
    "agree_with_technical",
    "momentum_zero",
]

#: How the entry price was obtained. ``backfill_bar`` is reserved for the history
#: backfill (spec §10, brief FX-EXEC-REPORTING): no live spot, bar-based P&L only.
EntryStatus = Literal["live", "live_unavailable", "backfill_bar"]

_VALID_SIDES: frozenset[int] = frozenset({-1, 0, 1})


# ---------------------------------------------------------------------------
# Shared validation helpers
# ---------------------------------------------------------------------------


def _validate_side(v: int) -> int:
    if v not in _VALID_SIDES:
        raise ValueError("side must be one of -1, 0, 1")
    return v


def _validate_size(v: float) -> float:
    if not math.isfinite(v):
        raise ValueError("size must be finite")
    if not 0.0 <= v <= 1.0:
        raise ValueError("size must be within [0.0, 1.0]")
    return v


def _validate_positive_price(v: float) -> float:
    if not math.isfinite(v):
        raise ValueError("price must be finite")
    if v <= 0:
        raise ValueError("price must be positive")
    return v


def _validate_finite_or_none(v: float | None) -> float | None:
    if v is not None and not math.isfinite(v):
        raise ValueError("value must be finite")
    return v


def _check_side_size_coupling(side: int, size: float) -> None:
    if (side == 0) != (size == 0.0):
        raise ValueError("size must be 0.0 exactly when side == 0 and positive otherwise")


def _check_entry_price_coupling(entry_status: str, entry_price_live: float | None) -> None:
    if (entry_price_live is not None) != (entry_status == "live"):
        raise ValueError("entry_price_live must be set exactly when entry_status == 'live'")


def _check_window_order(as_of_jst: datetime, window_end_jst: datetime) -> None:
    if window_end_jst <= as_of_jst:
        raise ValueError("window_end_jst must be strictly after as_of_jst")


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class LiveEntry(BaseModel):
    """Live spot observed at decision time (spec §6): the canonical entry price."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    price: float
    retrieved_at_utc: datetime
    vendor: str = Field(min_length=1)
    feed: str = Field(min_length=1)

    @field_validator("price")
    @classmethod
    def _price_must_be_finite_and_positive(cls, v: float) -> float:
        return _validate_positive_price(v)

    @field_validator("retrieved_at_utc")
    @classmethod
    def _normalize_retrieved_at_utc(cls, v: datetime) -> datetime:
        return _to_aware_utc(v)


class ExecutionDecision(BaseModel):
    """One book's paper-trading decision for one forecast window (spec §5.1).

    ``side``/``size``/``skip_reason`` are coupled: a skipped window has
    ``side == 0``, ``size == 0.0`` and a ``skip_reason``; a traded window has a
    non-zero side, a positive size and no ``skip_reason``. The audit columns
    (``beta_direction`` … ``previous_close_change_bp``) carry the shared inputs
    every book saw, so a row can be re-derived without the forecast batch.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --- key ---
    execution_version: str = Field(min_length=1)
    book_id: BookId
    as_of_jst: datetime
    window_end_jst: datetime
    forecast_batch_id: str = Field(min_length=1)
    source_strategy_kind: StrategyKind | None

    # --- decision ---
    side: int
    size: float
    skip_reason: SkipReason | None

    # --- entry ---
    entry_status: EntryStatus
    entry_price_live: float | None
    entry_time_utc: datetime
    entry_vendor: str | None
    entry_feed: str | None

    # --- audit inputs (identical on every row of a batch) ---
    beta_direction: ForecastDirection
    consensus_up_count: int = Field(ge=0)
    consensus_down_count: int = Field(ge=0)
    technical_direction: ForecastDirection
    momentum_3d: float
    trailing_mean_abs_close_change_bp: float
    previous_close_change_bp: float | None

    @field_validator("as_of_jst", "window_end_jst")
    @classmethod
    def _normalize_jst_timestamps(cls, v: datetime) -> datetime:
        return _to_jst(v)

    @field_validator("entry_time_utc")
    @classmethod
    def _normalize_entry_time_utc(cls, v: datetime) -> datetime:
        return _to_aware_utc(v)

    @field_validator("side")
    @classmethod
    def _side_in_range(cls, v: int) -> int:
        return _validate_side(v)

    @field_validator("size")
    @classmethod
    def _size_in_unit_interval(cls, v: float) -> float:
        return _validate_size(v)

    @field_validator("entry_price_live")
    @classmethod
    def _entry_price_finite_and_positive(cls, v: float | None) -> float | None:
        return None if v is None else _validate_positive_price(v)

    @field_validator("momentum_3d", "previous_close_change_bp")
    @classmethod
    def _audit_values_finite(cls, v: float | None) -> float | None:
        return _validate_finite_or_none(v)

    @field_validator("trailing_mean_abs_close_change_bp")
    @classmethod
    def _trailing_finite_and_non_negative(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("trailing_mean_abs_close_change_bp must be finite")
        if v < 0:
            raise ValueError("trailing_mean_abs_close_change_bp must be >= 0")
        return v

    @model_validator(mode="after")
    def _validate_coupling(self) -> ExecutionDecision:
        _check_side_size_coupling(self.side, self.size)
        if (self.skip_reason is not None) != (self.side == 0):
            raise ValueError("skip_reason must be set exactly when side == 0")
        _check_entry_price_coupling(self.entry_status, self.entry_price_live)
        _check_window_order(self.as_of_jst, self.window_end_jst)
        return self


class ExecutionEvaluation(BaseModel):
    """One book's realized result for one forecast window (spec §5.2).

    ``side``/``size``/``entry_status``/``entry_price_live`` are copied from the
    :class:`ExecutionDecision`; ``realized_open``/``realized_close`` from the
    window's ``OutcomeRecord``. Exit is always ``realized_close``. The
    ``*_live`` columns are priced off ``entry_price_live`` (canonical series,
    ``None`` when no live spot was recorded); the ``*_bar`` columns off
    ``realized_open`` (always available). Amounts in JPY are intentionally
    absent: equity curves are folded by the reporting layer (spec §8).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --- key ---
    execution_version: str = Field(min_length=1)
    book_id: BookId
    as_of_jst: datetime
    window_end_jst: datetime
    forecast_batch_id: str = Field(min_length=1)
    outcome_id: str = Field(min_length=1)

    # --- decision copy ---
    side: int
    size: float
    entry_status: EntryStatus
    entry_price_live: float | None

    # --- outcome copy ---
    realized_open: float
    realized_close: float

    # --- result (``*_live`` uses entry_price_live, ``*_bar`` uses realized_open) ---
    pnl_live_bp: float | None
    pnl_bar_bp: float
    cost_live_bp: float | None
    cost_bar_bp: float
    hit: bool | None
    evaluated_at_utc: datetime

    @field_validator("as_of_jst", "window_end_jst")
    @classmethod
    def _normalize_jst_timestamps(cls, v: datetime) -> datetime:
        return _to_jst(v)

    @field_validator("evaluated_at_utc")
    @classmethod
    def _normalize_evaluated_at_utc(cls, v: datetime) -> datetime:
        return _to_aware_utc(v)

    @field_validator("side")
    @classmethod
    def _side_in_range(cls, v: int) -> int:
        return _validate_side(v)

    @field_validator("size")
    @classmethod
    def _size_in_unit_interval(cls, v: float) -> float:
        return _validate_size(v)

    @field_validator("entry_price_live")
    @classmethod
    def _entry_price_finite_and_positive(cls, v: float | None) -> float | None:
        return None if v is None else _validate_positive_price(v)

    @field_validator("realized_open", "realized_close")
    @classmethod
    def _realized_prices_finite_and_positive(cls, v: float) -> float:
        return _validate_positive_price(v)

    @field_validator("pnl_live_bp", "pnl_bar_bp")
    @classmethod
    def _pnl_finite(cls, v: float | None) -> float | None:
        return _validate_finite_or_none(v)

    @field_validator("cost_live_bp", "cost_bar_bp")
    @classmethod
    def _cost_finite_and_non_negative(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if not math.isfinite(v):
            raise ValueError("cost must be finite")
        if v < 0:
            raise ValueError("cost must be >= 0")
        return v

    @model_validator(mode="after")
    def _validate_coupling(self) -> ExecutionEvaluation:
        _check_side_size_coupling(self.side, self.size)
        _check_entry_price_coupling(self.entry_status, self.entry_price_live)
        if (self.pnl_live_bp is None) != (self.entry_price_live is None):
            raise ValueError("pnl_live_bp must be None exactly when entry_price_live is None")
        if (self.cost_live_bp is None) != (self.entry_price_live is None):
            raise ValueError("cost_live_bp must be None exactly when entry_price_live is None")
        if (self.hit is None) != (self.side == 0):
            raise ValueError("hit must be None exactly when side == 0")
        if self.side == 0:
            if self.pnl_bar_bp != 0.0 or self.cost_bar_bp != 0.0:
                raise ValueError("side == 0 requires pnl_bar_bp == 0.0 and cost_bar_bp == 0.0")
            if self.pnl_live_bp not in (None, 0.0) or self.cost_live_bp not in (None, 0.0):
                raise ValueError(
                    "side == 0 requires pnl_live_bp and cost_live_bp to be None or 0.0"
                )
        _check_window_order(self.as_of_jst, self.window_end_jst)
        return self
