"""Typed protocol contracts for the FX Daily Protocol v1 (Phase 2 Milestone 13)."""

from __future__ import annotations

import math
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
from ugh_quantamental.schemas.market_svp import StateProbabilities

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class CurrencyPair(str, Enum):
    """Supported FX currency pairs in Phase 2 v1."""

    USDJPY = "USDJPY"


class StrategyKind(str, Enum):
    """Supported forecast strategy kinds."""

    ugh = "ugh"
    baseline_random_walk = "baseline_random_walk"
    baseline_prev_day_direction = "baseline_prev_day_direction"
    baseline_simple_technical = "baseline_simple_technical"


class ForecastDirection(str, Enum):
    """Directional forecast label."""

    up = "up"
    down = "down"
    flat = "flat"


class EventTag(str, Enum):
    """Fixed minimal event taxonomy for Phase 2 v1."""

    fomc = "fomc"
    boj = "boj"
    cpi_us = "cpi_us"
    nfp_us = "nfp_us"
    jp_holiday = "jp_holiday"
    us_holiday = "us_holiday"
    month_end = "month_end"
    quarter_end = "quarter_end"
    other_macro = "other_macro"
    unscheduled_event = "unscheduled_event"


# ---------------------------------------------------------------------------
# Provenance / support models
# ---------------------------------------------------------------------------


class MarketDataProvenance(BaseModel):
    """Source-of-truth metadata for market data used in a protocol record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    vendor: str = Field(min_length=1)
    feed_name: str = Field(min_length=1)
    price_type: Literal["mid"]
    resolution: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    retrieved_at_utc: datetime
    source_ref: str | None = None


class ExpectedRange(BaseModel):
    """Canonical price-envelope forecast: low_price must be <= high_price."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    low_price: float
    high_price: float

    @field_validator("low_price", "high_price")
    @classmethod
    def _must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("price must be finite")
        return v

    @model_validator(mode="after")
    def _ordering(self) -> ExpectedRange:
        if self.low_price > self.high_price:
            raise ValueError("low_price must be <= high_price")
        return self


class DisconfirmerRule(BaseModel):
    """A single disconfirmer rule definition carried in a ForecastRecord."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    audit_kind: Literal["event_tag", "close_change_bp", "range_break", "state_proxy"]
    target_field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    threshold_value: float | str | bool | None = None
    window_scope: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# UGH-required field names (used by ForecastRecord validator)
# ---------------------------------------------------------------------------

_UGH_REQUIRED_FIELDS: tuple[str, ...] = (
    "dominant_state",
    "state_probabilities",
    "q_dir",
    "q_strength",
    "s_q",
    "temporal_score",
    "grv_raw",
    "grv_lock",
    "alignment",
    "e_star",
    "mismatch_px",
    "mismatch_sem",
    "conviction",
    "urgency",
    "input_snapshot_ref",
    "primary_question",
    "expected_range",
)

_BASELINE_STRATEGY_KINDS: frozenset[StrategyKind] = frozenset(
    {
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    }
)


# ---------------------------------------------------------------------------
# Core protocol records
# ---------------------------------------------------------------------------


class ForecastRecord(BaseModel):
    """Immutable locked forecast produced at as_of_jst.

    For ``strategy_kind="ugh"`` all UGH engine fields are required.
    For baseline strategy kinds those fields may be ``None``.
    Baselines still require ``forecast_direction`` and ``expected_close_change_bp``.
    ``disconfirmers`` may be an empty tuple for baselines.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --- identity ---
    forecast_id: str = Field(min_length=1)
    forecast_batch_id: str = Field(min_length=1)

    # --- pair / strategy ---
    pair: CurrencyPair
    strategy_kind: StrategyKind

    # --- time ---
    as_of_jst: datetime
    window_end_jst: datetime
    locked_at_utc: datetime

    # --- provenance ---
    market_data_provenance: MarketDataProvenance

    # --- UGH-only inputs (None for baselines) ---
    input_snapshot_ref: str | None = None
    primary_question: str | None = None

    # --- direction / price forecast (always required) ---
    forecast_direction: ForecastDirection
    expected_close_change_bp: float

    # --- UGH-only price envelope (None for baselines) ---
    expected_range: ExpectedRange | None = None

    # --- disconfirmers (empty tuple allowed for baselines) ---
    disconfirmers: tuple[DisconfirmerRule, ...] = ()

    # --- UGH state engine outputs (None for baselines) ---
    dominant_state: LifecycleState | None = None
    state_probabilities: StateProbabilities | None = None

    # --- UGH question/signal features (None for baselines) ---
    q_dir: QuestionDirection | None = None
    q_strength: float | None = None
    s_q: float | None = None
    temporal_score: float | None = None
    grv_raw: float | None = None
    grv_lock: float | None = None

    # --- UGH projection engine outputs (None for baselines) ---
    alignment: float | None = None
    e_star: float | None = None
    mismatch_px: float | None = None
    mismatch_sem: float | None = None
    conviction: float | None = None
    urgency: float | None = None

    # --- version metadata ---
    theory_version: str = Field(min_length=1)
    engine_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_strategy_consistency(self) -> ForecastRecord:
        if self.strategy_kind == StrategyKind.ugh:
            null_fields = [f for f in _UGH_REQUIRED_FIELDS if getattr(self, f) is None]
            if null_fields:
                raise ValueError(
                    f"strategy_kind='ugh' requires non-null fields: {null_fields}"
                )
        return self


class OutcomeRecord(BaseModel):
    """Canonical market-fact record for a realized forecast window.

    This record is framework-agnostic.  State-proxy fields (``realized_state_proxy``,
    ``actual_state_change``) are intentionally absent: they are evaluation-layer metadata,
    not market-fact observations.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --- identity ---
    outcome_id: str = Field(min_length=1)

    # --- pair / window ---
    pair: CurrencyPair
    window_start_jst: datetime
    window_end_jst: datetime

    # --- provenance ---
    market_data_provenance: MarketDataProvenance

    # --- realized OHLC ---
    realized_open: float
    realized_high: float
    realized_low: float
    realized_close: float

    # --- derived market facts ---
    realized_direction: ForecastDirection
    realized_close_change_bp: float
    realized_range_price: float

    # --- event metadata ---
    event_happened: bool
    event_tags: tuple[EventTag, ...]

    # --- version metadata ---
    schema_version: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)

    @field_validator("realized_open", "realized_high", "realized_low", "realized_close")
    @classmethod
    def _price_must_be_finite_and_positive(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("realized price must be finite")
        if v <= 0:
            raise ValueError("realized price must be positive")
        return v

    @model_validator(mode="after")
    def _ohlc_ordering(self) -> OutcomeRecord:
        if self.realized_high < self.realized_low:
            raise ValueError("realized_high must be >= realized_low")
        if not (self.realized_low <= self.realized_open <= self.realized_high):
            raise ValueError("realized_open must be within [realized_low, realized_high]")
        if not (self.realized_low <= self.realized_close <= self.realized_high):
            raise ValueError("realized_close must be within [realized_low, realized_high]")
        return self


class EvaluationRecord(BaseModel):
    """Atomic diagnostic evaluation joining a ForecastRecord with an OutcomeRecord.

    Stores per-forecast diagnostic fields only.  Aggregate metrics (MAE, RMSE, MASE,
    sMAPE) are intentionally absent and belong to the reporting layer.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --- identity ---
    evaluation_id: str = Field(min_length=1)
    forecast_id: str = Field(min_length=1)
    outcome_id: str = Field(min_length=1)

    # --- context ---
    pair: CurrencyPair
    strategy_kind: StrategyKind

    # --- directional hit (always computable) ---
    direction_hit: bool

    # --- price envelope hit (None when expected_range not provided) ---
    range_hit: bool | None = None

    # --- error metrics (None when not applicable) ---
    close_error_bp: float | None = None
    magnitude_error_bp: float | None = None

    # --- state-proxy diagnostics (UGH only; None for baselines) ---
    state_proxy_hit: bool | None = None
    mismatch_change_bp: float | None = None
    realized_state_proxy: str | None = None
    actual_state_change: bool | None = None

    # --- disconfirmer diagnostics ---
    disconfirmers_hit: tuple[str, ...] = ()
    disconfirmer_explained: bool | None = None

    # --- timestamp ---
    evaluated_at_utc: datetime

    # --- version metadata ---
    theory_version: str = Field(min_length=1)
    engine_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    protocol_version: str = Field(min_length=1)
