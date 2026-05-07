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
    EXPECTED_DAILY_BATCH_SIZE,
    DisconfirmerRule,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    StrategyKind,
    is_ugh_kind,
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
    expected_range: ExpectedRange | None = None,
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
    payload = {
        "forecast_id": make_forecast_id(
            request.pair, request.as_of_jst, request.protocol_version, strategy_kind
        ),
        "forecast_batch_id": forecast_batch_id,
        "pair": request.pair,
        "strategy_kind": strategy_kind,
        "as_of_jst": request.as_of_jst,
        "window_end_jst": window_end_jst,
        "locked_at_utc": request.locked_at_utc
        or _as_of_jst_to_utc(request.as_of_jst) - timedelta(seconds=1),
        "market_data_provenance": request.market_data_provenance,
        "forecast_direction": forecast_direction,
        "expected_close_change_bp": expected_close_change_bp,
        "disconfirmers": disconfirmers,
        "theory_version": request.theory_version,
        "engine_version": request.engine_version,
        "schema_version": request.schema_version,
        "protocol_version": request.protocol_version,
    }

    optional_fields = {
        "input_snapshot_ref": request.input_snapshot_ref if is_ugh_kind(strategy_kind) else None,
        "primary_question": primary_question,
        "expected_range": expected_range,
        "dominant_state": dominant_state,
        "state_probabilities": state_probabilities,
        "q_dir": q_dir,
        "q_strength": q_strength,
        "s_q": s_q,
        "temporal_score": temporal_score,
        "grv_raw": grv_raw,
        "grv_lock": grv_lock,
        "alignment": alignment,
        "e_star": e_star,
        "mismatch_px": mismatch_px,
        "mismatch_sem": mismatch_sem,
        "conviction": conviction,
        "urgency": urgency,
    }
    payload.update({k: v for k, v in optional_fields.items() if v is not None})
    return ForecastRecord(**payload)


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
    )


#: Per-variant ``ProjectionConfig`` overrides for the four v2 UGH variants
#: (spec §5.2). ``ugh_v2_alpha`` is conservative — its values match the
#: no-arg ``ProjectionConfig()`` defaults — so the entry below is empty
#: and exists for symmetry / explicitness. ``beta`` / ``gamma`` / ``delta``
#: each override the four directional knobs (``u_weight``, ``t_weight``,
#: ``p_weight``, ``conviction_floor``) from alpha.
_UGH_V2_VARIANT_CONFIGS: dict[StrategyKind, dict[str, float]] = {
    StrategyKind.ugh_v2_alpha: {
        "u_weight": 0.40,
        "t_weight": 0.30,
        "p_weight": 0.20,
        "conviction_floor": 0.5,
    },
    StrategyKind.ugh_v2_beta: {
        "u_weight": 0.20,
        "t_weight": 0.20,
        "p_weight": 0.40,
        "conviction_floor": 0.5,
    },
    StrategyKind.ugh_v2_gamma: {
        "u_weight": 0.40,
        "t_weight": 0.30,
        "p_weight": 0.20,
        "conviction_floor": 0.3,
    },
    StrategyKind.ugh_v2_delta: {
        "u_weight": 0.20,
        "t_weight": 0.30,
        "p_weight": 0.30,
        "conviction_floor": 0.5,
    },
}

#: Order in which v2 UGH variants are emitted into a forecast batch.
UGH_V2_VARIANTS: tuple[StrategyKind, ...] = (
    StrategyKind.ugh_v2_alpha,
    StrategyKind.ugh_v2_beta,
    StrategyKind.ugh_v2_gamma,
    StrategyKind.ugh_v2_delta,
)


def _build_variant_request(
    base_request: DailyForecastWorkflowRequest,
    variant: StrategyKind,
):
    """Return a copy of ``base_request.ugh_request`` with the variant's config.

    The returned object is a fresh ``FullWorkflowRequest`` (the base request's
    ``ugh_request`` is frozen Pydantic). ``projection.config`` is replaced
    with the variant's :class:`ProjectionConfig`; all other fields are
    preserved.
    """
    from ugh_quantamental.engine.projection_models import ProjectionConfig
    from ugh_quantamental.workflows.models import (
        FullWorkflowRequest,
        ProjectionWorkflowRequest,
    )

    overrides = _UGH_V2_VARIANT_CONFIGS[variant]
    base_proj = base_request.ugh_request.projection
    variant_config = ProjectionConfig(**overrides)
    variant_projection = ProjectionWorkflowRequest(
        projection_id=base_proj.projection_id,
        horizon_days=base_proj.horizon_days,
        question_features=base_proj.question_features,
        signal_features=base_proj.signal_features,
        alignment_inputs=base_proj.alignment_inputs,
        config=variant_config,
        # run_id intentionally cleared per variant: ``ProjectionRunRecord``'s
        # primary key is ``run_id``, and 4 variants saving against the same
        # base run_id would collide on flush. ``run_projection_workflow``
        # generates a fresh ``proj-<uuid>`` when run_id is None.
        run_id=None,
        created_at=base_proj.created_at,
    )
    base_state = base_request.ugh_request.state
    # Same reasoning for state runs.
    variant_state = base_state.model_copy(update={"run_id": None})
    return FullWorkflowRequest(
        projection=variant_projection,
        state=variant_state,
    )


def build_ugh_variant_forecast(
    session: Session,
    request: DailyForecastWorkflowRequest,
    forecast_batch_id: str,
    window_end_jst,
    *,
    variant: StrategyKind,
) -> ForecastRecord:
    """Build one ``ForecastRecord`` for the given v2 UGH variant.

    Replaces the v1 ``build_ugh_forecast`` builder, which emitted a single
    ``StrategyKind.ugh`` record. v2 emits four variant records per snapshot
    (spec §5.2); this function produces one of them, parameterized by the
    ``variant`` ``StrategyKind`` (which selects the per-variant
    :class:`ProjectionConfig` from ``_UGH_V2_VARIANT_CONFIGS``).
    """
    if variant not in _UGH_V2_VARIANT_CONFIGS:
        raise ValueError(
            f"variant must be one of {tuple(_UGH_V2_VARIANT_CONFIGS)}; got {variant!r}"
        )

    variant_request = _build_variant_request(request, variant)
    full_result = run_full_workflow(session=session, request=variant_request)
    projection_req = variant_request.projection
    projection_res = full_result.projection.engine_result
    state_res = full_result.state.engine_result

    # e_star is a unitless [-1, 1] score (direction × confidence). Scale it to bp
    # by the trailing mean absolute close change so UGH magnitudes are on the same
    # unit as baseline_simple_technical / baseline_prev_day_direction. Apply a
    # realized-volatility × conviction multiplier (matches PR #87 magnitude
    # scaling, retained for v2).
    ctx = request.baseline_context
    conviction_factor = 0.5 + 0.5 * projection_res.conviction
    expected_close_change_bp = (
        projection_res.e_star * ctx.trailing_mean_abs_close_change_bp * conviction_factor
    )

    return _make_base_record(
        request=request,
        forecast_batch_id=forecast_batch_id,
        window_end_jst=window_end_jst,
        strategy_kind=variant,
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
        if len(existing.forecasts) != EXPECTED_DAILY_BATCH_SIZE:
            raise ValueError(
                f"partial forecast batch exists for {forecast_batch_id}: expected "
                f"{EXPECTED_DAILY_BATCH_SIZE} records, got {len(existing.forecasts)}"
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

    # v2 batch: one forecast per UGH variant (alpha/beta/gamma/delta) plus
    # three baselines = 7 records total (cf. EXPECTED_DAILY_BATCH_SIZE).
    forecasts = (
        *(
            build_ugh_variant_forecast(
                session, request, forecast_batch_id, window_end_jst, variant=variant
            )
            for variant in UGH_V2_VARIANTS
        ),
        build_random_walk_forecast(request, forecast_batch_id, window_end_jst),
        build_prev_day_direction_forecast(request, forecast_batch_id, window_end_jst),
        build_simple_technical_forecast(request, forecast_batch_id, window_end_jst),
    )

    return FxForecastRepository.save_fx_forecast_batch(
        session,
        forecast_batch_id=forecast_batch_id,
        forecasts=forecasts,
    )
