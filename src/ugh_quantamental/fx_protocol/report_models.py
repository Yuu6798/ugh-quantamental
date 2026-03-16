"""Typed models for the FX weekly report (Phase 2 Milestone 16)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    ForecastDirection,
    StrategyKind,
    _to_jst,
)
from ugh_quantamental.schemas.enums import LifecycleState


class WeeklyReportRequest(BaseModel):
    """Input contract for generating a weekly FX report.

    ``business_day_count`` determines how many completed protocol windows
    (each ending at 08:00 JST on a Mon–Fri business day) are included.
    Report generation may happen on weekends.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair: CurrencyPair
    report_generated_at_jst: datetime
    business_day_count: int = Field(default=5, ge=1)
    max_examples: int = Field(default=3, ge=1)

    @field_validator("report_generated_at_jst")
    @classmethod
    def _normalize_report_generated_at_jst(cls, v: datetime) -> datetime:
        """Canonicalize report_generated_at_jst to a JST-aware datetime on ingestion.

        Without normalization, a UTC-aware or naive input would carry a timezone
        inconsistent with the ``*_jst`` field name, causing the result's
        ``report_generated_at_jst`` to represent a different instant in JST than
        the window-resolution logic computed.  Naive inputs are treated as already
        in JST, matching the ``ids.py`` / ``models.py`` policy throughout this package.
        """
        return _to_jst(v)


class StrategyWeeklyMetrics(BaseModel):
    """Aggregate evaluation metrics for one strategy over the report window.

    ``range_evaluable_count`` and ``range_hit_rate`` are always 0 / None for
    baseline strategies because baselines carry no ``expected_range``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_kind: StrategyKind
    forecast_count: int
    direction_evaluable_count: int
    direction_hit_count: int
    direction_accuracy: float | None
    range_evaluable_count: int
    range_hit_count: int
    range_hit_rate: float | None
    mean_abs_close_error_bp: float | None
    mean_abs_magnitude_error_bp: float | None


class BaselineWeeklyComparison(BaseModel):
    """Direction-accuracy and close-error comparison between one baseline and UGH.

    Negative ``direction_accuracy_delta_vs_ugh`` means the baseline underperforms UGH.
    Positive ``mean_abs_close_error_bp_delta_vs_ugh`` means the baseline has higher
    absolute close error than UGH.
    Both fields are ``None`` when either side lacks a computable metric.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_strategy_kind: StrategyKind
    direction_accuracy_delta_vs_ugh: float | None
    mean_abs_close_error_bp_delta_vs_ugh: float | None


class StateWeeklyMetrics(BaseModel):
    """Per-dominant-state aggregate metrics for UGH forecasts only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dominant_state: LifecycleState
    forecast_count: int
    direction_accuracy: float | None
    mean_abs_close_error_bp: float | None


class WeeklyGrvFireSummary(BaseModel):
    """GRV-lock and directional-accuracy split by fire vs non-fire state.

    UGH forecasts only.  Fire bucket = ``dominant_state == "fire"``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    fire_count: int
    non_fire_count: int
    mean_grv_lock_fire: float | None
    mean_grv_lock_non_fire: float | None
    fire_direction_accuracy: float | None


class WeeklyMismatchSummary(BaseModel):
    """Directional-accuracy split by sign of ``mismatch_px``.

    UGH forecasts only.  Rows where ``mismatch_px is None`` are excluded from
    both buckets.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    positive_mismatch_count: int
    non_positive_mismatch_count: int
    positive_mismatch_direction_accuracy: float | None
    non_positive_mismatch_direction_accuracy: float | None


class WeeklyCaseExample(BaseModel):
    """One curated forecast–outcome pair for qualitative review.

    UGH forecasts only.  Used for false-positive cases, representative
    successes, and representative failures.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    forecast_id: str
    strategy_kind: StrategyKind
    as_of_jst: datetime
    dominant_state: LifecycleState | None
    forecast_direction: ForecastDirection
    realized_direction: ForecastDirection
    expected_close_change_bp: float
    realized_close_change_bp: float
    close_error_bp: float | None
    conviction: float | None
    urgency: float | None
    disconfirmer_explained: bool | None


class WeeklyReportResult(BaseModel):
    """Full weekly FX report result.

    ``window_end_jst_values`` contains all resolved protocol window-end
    timestamps (chronological order, oldest first).
    ``included_window_count`` is the count of windows that had at least one
    evaluation row in the database.
    ``missing_window_count`` is the count of windows with no data.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair: CurrencyPair
    report_generated_at_jst: datetime
    window_end_jst_values: tuple[datetime, ...]
    requested_window_count: int
    included_window_count: int
    missing_window_count: int
    strategy_metrics: tuple[StrategyWeeklyMetrics, ...]
    baseline_comparisons: tuple[BaselineWeeklyComparison, ...]
    state_metrics: tuple[StateWeeklyMetrics, ...]
    grv_fire_summary: WeeklyGrvFireSummary
    mismatch_summary: WeeklyMismatchSummary
    ugh_disconfirmer_explained_rate: float | None
    false_positive_cases: tuple[WeeklyCaseExample, ...]
    representative_successes: tuple[WeeklyCaseExample, ...]
    representative_failures: tuple[WeeklyCaseExample, ...]
