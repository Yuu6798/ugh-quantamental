"""Deterministic daily FX forecast workflow (Phase 2 Milestone 14)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.calendar import is_protocol_business_day, next_as_of_jst
from ugh_quantamental.fx_protocol.forecast_models import (
    DailyForecastWorkflowRequest,
    PersistedDailyForecastBatch,
)
from ugh_quantamental.fx_protocol.ids import make_forecast_batch_id, make_forecast_id
from ugh_quantamental.fx_protocol.models import (
    DisconfirmerRule,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    StrategyKind,
)
from ugh_quantamental.persistence.repositories import FxForecastRepository
from ugh_quantamental.schemas.enums import QuestionDirection
from ugh_quantamental.workflows.runners import run_full_workflow

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_JST = ZoneInfo("Asia/Tokyo")


def _as_of_jst_to_utc(as_of_jst: datetime) -> datetime:
    """Convert as_of_jst to UTC-aware datetime, treating naive inputs as JST."""
    if as_of_jst.tzinfo is None:
        return as_of_jst.replace(tzinfo=_JST).astimezone(timezone.utc)
    return as_of_jst.astimezone(timezone.utc)


def _direction_from_bp(change_bp: float) -> ForecastDirection:
    if change_bp > 0:
        return ForecastDirection.up
    if change_bp < 0:
        return ForecastDirection.down
    return ForecastDirection.flat


def _shared_range(low: float, high: float) -> ExpectedRange:
    return ExpectedRange(low_price=low, high_price=high)


def _build_range_from_baseline_context(current_spot: float, trailing_mean_range_price: float) -> ExpectedRange:
    band_half = trailing_mean_range_price / 2.0
    return _shared_range(current_spot - band_half, current_spot + band_half)


def _make_base_record(
    *,
    request: DailyForecastWorkflowRequest,
    forecast_batch_id: str,
    window_end_jst,
    strategy_kind: StrategyKind,
    forecast_direction: ForecastDirection,
    expected_close_change_bp: float,
    expected_range: ExpectedRange | None,
    primary_question: str | None = None,
    disconfirmers: tuple[DisconfirmerRule, ...] = (),
    dominant_state=None,
    state_probabilities=None,
    q_dir=None,
    q_strength=None,
    s_q=None,
    temporal_score=None,
    grv_raw=None,
    grv_lock=None,
    alignment=None,
    e_star=None,
    mismatch_px=None,
    mismatch_sem=None,
    conviction=None,
    urgency=None,
) -> ForecastRecord:
    return ForecastRecord(
        forecast_id=make_forecast_id(
            request.pair, request.as_of_jst, request.protocol_version, strategy_kind
        ),
        forecast_batch_id=forecast_batch_id,
        pair=request.pair,
        strategy_kind=strategy_kind,
        as_of_jst=request.as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=request.locked_at_utc
        or _as_of_jst_to_utc(request.as_of_jst) - timedelta(seconds=1),
        market_data_provenance=request.market_data_provenance,
        input_snapshot_ref=request.input_snapshot_ref if strategy_kind == StrategyKind.ugh else None,
        primary_question=primary_question,
        forecast_direction=forecast_direction,
        expected_close_change_bp=expected_close_change_bp,
        expected_range=expected_range,
        disconfirmers=disconfirmers,
        dominant_state=dominant_state,
        state_probabilities=state_probabilities,
        q_dir=q_dir,
        q_strength=q_strength,
        s_q=s_q,
        temporal_score=temporal_score,
        grv_raw=grv_raw,
        grv_lock=grv_lock,
        alignment=alignment,
        e_star=e_star,
        mismatch_px=mismatch_px,
        mismatch_sem=mismatch_sem,
        conviction=conviction,
        urgency=urgency,
        theory_version=request.theory_version,
        engine_version=request.engine_version,
        schema_version=request.schema_version,
        protocol_version=request.protocol_version,
    )


def build_random_walk_forecast(
    request: DailyForecastWorkflowRequest,
    forecast_batch_id: str,
    window_end_jst,
) -> ForecastRecord:
    return _make_base_record(
        request=request,
        forecast_batch_id=forecast_batch_id,
        window_end_jst=window_end_jst,
        strategy_kind=StrategyKind.baseline_random_walk,
        forecast_direction=ForecastDirection.flat,
        expected_close_change_bp=0.0,
        expected_range=None,
    )


def build_prev_day_direction_forecast(
    request: DailyForecastWorkflowRequest,
    forecast_batch_id: str,
    window_end_jst,
) -> ForecastRecord:
    ctx = request.baseline_context
    if ctx.previous_close_change_bp is None:
        raise ValueError("previous_close_change_bp is required for baseline_prev_day_direction")
    return _make_base_record(
        request=request,
        forecast_batch_id=forecast_batch_id,
        window_end_jst=window_end_jst,
        strategy_kind=StrategyKind.baseline_prev_day_direction,
        forecast_direction=_direction_from_bp(ctx.previous_close_change_bp),
        expected_close_change_bp=ctx.previous_close_change_bp,
        expected_range=None,
    )


def build_simple_technical_forecast(
    request: DailyForecastWorkflowRequest,
    forecast_batch_id: str,
    window_end_jst,
) -> ForecastRecord:
    ctx = request.baseline_context
    if ctx.sma5 is None or ctx.sma20 is None:
        raise ValueError("sma5 and sma20 are required for baseline_simple_technical")

    gap = ctx.sma5 - ctx.sma20
    sign = 1.0 if gap > 0 else -1.0 if gap < 0 else 0.0
    expected_change_bp = sign * ctx.trailing_mean_abs_close_change_bp

    return _make_base_record(
        request=request,
        forecast_batch_id=forecast_batch_id,
        window_end_jst=window_end_jst,
        strategy_kind=StrategyKind.baseline_simple_technical,
        forecast_direction=_direction_from_bp(expected_change_bp),
        expected_close_change_bp=expected_change_bp,
        expected_range=None,
    )


def build_ugh_forecast(
    session: Session,
    request: DailyForecastWorkflowRequest,
    forecast_batch_id: str,
    window_end_jst,
) -> ForecastRecord:
    full_result = run_full_workflow(session=session, request=request.ugh_request)
    projection_req = request.ugh_request.projection
    projection_res = full_result.projection.engine_result
    state_res = full_result.state.engine_result

    expected_close_change_bp = projection_res.e_star

    return _make_base_record(
        request=request,
        forecast_batch_id=forecast_batch_id,
        window_end_jst=window_end_jst,
        strategy_kind=StrategyKind.ugh,
        forecast_direction=_direction_from_bp(expected_close_change_bp),
        expected_close_change_bp=expected_close_change_bp,
        expected_range=_build_range_from_baseline_context(
            request.baseline_context.current_spot,
            request.baseline_context.trailing_mean_range_price,
        ),
        primary_question=projection_req.projection_id,
        disconfirmers=(),
        dominant_state=state_res.dominant_state,
        state_probabilities=state_res.updated_probabilities,
        q_dir=QuestionDirection(projection_req.question_features.question_direction.value),
        q_strength=projection_req.question_features.q_strength,
        s_q=projection_req.question_features.s_q,
        temporal_score=projection_req.question_features.temporal_score,
        grv_raw=projection_res.gravity_bias,
        grv_lock=projection_req.signal_features.grv_lock,
        alignment=projection_res.alignment,
        e_star=projection_res.e_star,
        mismatch_px=projection_res.mismatch_px,
        mismatch_sem=projection_res.mismatch_sem,
        conviction=projection_res.conviction,
        urgency=projection_res.urgency,
    )

def run_daily_forecast_workflow(
    session: Session,
    request: DailyForecastWorkflowRequest,
) -> PersistedDailyForecastBatch:
    """Generate and persist one deterministic daily forecast batch."""
    if not is_protocol_business_day(request.as_of_jst, tz="Asia/Tokyo"):
        raise ValueError("as_of_jst must be a protocol business day")
    if (request.as_of_jst.hour, request.as_of_jst.minute, request.as_of_jst.second, request.as_of_jst.microsecond) != (8, 0, 0, 0):
        raise ValueError("as_of_jst must be exactly 08:00 JST")

    forecast_batch_id = make_forecast_batch_id(
        request.pair,
        request.as_of_jst,
        request.protocol_version,
    )

    existing = FxForecastRepository.load_fx_forecast_batch(session, forecast_batch_id)
    if existing is not None:
        if len(existing.forecasts) != 4:
            raise ValueError(
                f"partial forecast batch exists for {forecast_batch_id}: expected 4 records, got {len(existing.forecasts)}"
            )
        return existing

    # Validate baseline inputs before running the UGH workflow (which has side effects).
    # Fail fast here so no orphaned workflow records are created if baseline data is missing.
    ctx = request.baseline_context
    if ctx.previous_close_change_bp is None:
        raise ValueError("previous_close_change_bp is required for baseline_prev_day_direction")
    if ctx.sma5 is None or ctx.sma20 is None:
        raise ValueError("sma5 and sma20 are required for baseline_simple_technical")

    window_end_jst = next_as_of_jst(request.as_of_jst)

    forecasts = (
        build_ugh_forecast(session, request, forecast_batch_id, window_end_jst),
        build_random_walk_forecast(request, forecast_batch_id, window_end_jst),
        build_prev_day_direction_forecast(request, forecast_batch_id, window_end_jst),
        build_simple_technical_forecast(request, forecast_batch_id, window_end_jst),
    )

    return FxForecastRepository.save_fx_forecast_batch(
        session,
        forecast_batch_id=forecast_batch_id,
        forecasts=forecasts,
    )
