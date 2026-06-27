"""Tests for deterministic daily forecast workflow generation."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionDirectionSign,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateEngineResult, StateEventFeatures
from ugh_quantamental.fx_protocol.forecast_models import (
    BaselineContext,
    DailyForecastWorkflowRequest,
)
from ugh_quantamental.fx_protocol.ids import make_forecast_batch_id
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    ForecastDirection,
    MarketDataProvenance,
    StrategyKind,
)
from ugh_quantamental.schemas.enums import LifecycleState, MacroCycleRegime, MarketRegime
from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
from ugh_quantamental.schemas.omega import BlockObservability, EvidenceLineageRecord, Omega
from ugh_quantamental.schemas.projection import ProjectionSnapshot
from ugh_quantamental.schemas.ssv import (
    FBlock,
    PBlock,
    QBlock,
    QuestionLedger,
    QuestionRecord,
    RBlock,
    SSVSnapshot,
    TBlock,
    XBlock,
)
from ugh_quantamental.workflows.models import (
    FullWorkflowRequest,
    FullWorkflowResult,
    FullWorkflowStateRequest,
    ProjectionWorkflowRequest,
    ProjectionWorkflowResult,
    StateWorkflowResult,
)

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

if HAS_SQLALCHEMY:
    from ugh_quantamental.fx_protocol.forecasting import (
        _build_range_from_projection_width,
        _direction_from_bp_with_epsilon,
        build_prev_day_direction_forecast,
        build_random_walk_forecast,
        build_simple_technical_forecast,
        build_ugh_variant_forecast,
        run_daily_forecast_workflow,
    )
else:
    _build_range_from_projection_width = None
    _direction_from_bp_with_epsilon = None
    build_prev_day_direction_forecast = None
    build_random_walk_forecast = None
    build_simple_technical_forecast = None
    build_ugh_variant_forecast = None
    run_daily_forecast_workflow = None


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test_vendor",
        feed_name="test_feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 13, 0, 0, 0, tzinfo=timezone.utc),
    )


def _snapshot() -> SSVSnapshot:
    probs = StateProbabilities(
        dormant=0.2,
        setup=0.4,
        fire=0.2,
        expansion=0.1,
        exhaustion=0.05,
        failure=0.05,
    )
    return SSVSnapshot(
        snapshot_id="snap-1",
        q=QBlock(
            ledger=QuestionLedger(
                as_of="2026-03-13",
                coverage_ratio=1.0,
                questions=(
                    QuestionRecord(
                        question_id="q-1",
                        direction="positive",
                        score=0.6,
                        weight=1.0,
                    ),
                ),
            )
        ),
        f=FBlock(factor_count=3, aggregate_signal=0.2),
        t=TBlock(timestamp="2026-03-13T00:00:00Z", lookback_days=30),
        p=PBlock(implied_move_30d=0.03, implied_volatility=0.2, skew_25d=0.01),
        phi=Phi(dominant_state=LifecycleState.setup, probabilities=probs),
        r=RBlock(
            market_regime=MarketRegime.neutral,
            macro_cycle_regime=MacroCycleRegime.expansion,
            conviction=0.5,
        ),
        x=XBlock(tags=("test",)),
    )


def _omega(snapshot: SSVSnapshot) -> Omega:
    obs = BlockObservability(q=0.9, f=0.9, t=0.9, p=0.9, r=0.9, x=0.9)
    return Omega(
        omega_id="omega-1",
        market_svp=MarketSVP(
            as_of="2026-03-13T00:00:00Z",
            regime=MarketRegime.neutral,
            phi=snapshot.phi,
            confidence=0.9,
        ),
        question_ledger=snapshot.q.ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="src-1",
                observed_at="2026-03-13T00:00:00Z",
                source_type="internal",
            ),
        ),
        block_confidence=obs,
        block_observability=obs,
        confidence=0.9,
    )


def _full_request() -> FullWorkflowRequest:
    snap = _snapshot()
    omg = _omega(snap)
    return FullWorkflowRequest(
        projection=ProjectionWorkflowRequest(
            projection_id="Will USDJPY close higher?",
            horizon_days=1,
            question_features=QuestionFeatures(
                question_direction=QuestionDirectionSign.positive,
                q_strength=0.7,
                s_q=0.6,
                temporal_score=0.8,
            ),
            signal_features=SignalFeatures(
                fundamental_score=0.2,
                technical_score=0.3,
                price_implied_score=0.1,
                context_score=1.0,
                grv_lock=0.7,
                regime_fit=0.6,
                narrative_dispersion=0.3,
                evidence_confidence=0.8,
                fire_probability=0.4,
            ),
            alignment_inputs=AlignmentInputs(
                d_qf=0.1,
                d_qt=0.1,
                d_qp=0.1,
                d_ft=0.1,
                d_fp=0.1,
                d_tp=0.1,
            ),
        ),
        state=FullWorkflowStateRequest(
            snapshot=snap,
            omega=omg,
            event_features=StateEventFeatures(
                catalyst_strength=0.6,
                follow_through=0.5,
                pricing_saturation=0.3,
                disconfirmation_strength=0.2,
                regime_shock=0.1,
                observation_freshness=0.8,
            ),
        ),
    )


def _request(**kwargs) -> DailyForecastWorkflowRequest:
    base = {
        "pair": CurrencyPair.USDJPY,
        "as_of_jst": datetime(2026, 3, 13, 8, 0, 0),
        "market_data_provenance": _provenance(),
        "input_snapshot_ref": "snapshot/ref/001",
        "ugh_request": _full_request(),
        "baseline_context": BaselineContext(
            current_spot=150.0,
            previous_close_change_bp=12.0,
            trailing_mean_range_price=1.2,
            trailing_mean_abs_close_change_bp=20.0,
            sma5=150.2,
            sma20=149.8,
            warmup_window_count=20,
        ),
        "theory_version": "v1",
        "engine_version": "v1",
        "schema_version": "v1",
        "protocol_version": "v1",
    }
    base.update(kwargs)
    return DailyForecastWorkflowRequest(**base)


@pytest.fixture()
def db_session():
    if not HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")
    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine, create_session_factory

    engine = create_db_engine()
    create_all_tables(engine)
    session = create_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()


def _projection_result(
    *,
    e_star: float,
    conviction: float,
    width_score: float = 0.1,
) -> ProjectionEngineResult:
    return ProjectionEngineResult(
        u_score=e_star,
        alignment=0.8,
        e_raw=e_star,
        gravity_bias=0.0,
        e_star=e_star,
        mismatch_px=0.0,
        mismatch_sem=0.0,
        conviction=conviction,
        urgency=0.5,
        projection_snapshot=ProjectionSnapshot(
            projection_id="Will USDJPY close higher?",
            horizon_days=1,
            point_estimate=e_star,
            lower_bound=e_star - width_score,
            upper_bound=e_star + width_score,
            confidence=conviction,
        ),
    )


def _state_result(req: DailyForecastWorkflowRequest) -> StateEngineResult:
    return StateEngineResult(
        evidence_scores=req.ugh_request.state.snapshot.phi.probabilities,
        updated_probabilities=req.ugh_request.state.snapshot.phi.probabilities,
        updated_phi=req.ugh_request.state.snapshot.phi,
        updated_market_svp=req.ugh_request.state.omega.market_svp,
        dominant_state=LifecycleState.setup,
        transition_confidence=0.5,
    )


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_baseline_construction_rules_are_deterministic() -> None:
    request = _request()
    batch_id = make_forecast_batch_id(request.pair, request.as_of_jst, request.protocol_version)
    window_end = datetime(2026, 3, 16, 8, 0, 0)

    rw = build_random_walk_forecast(request, batch_id, window_end)
    assert rw.strategy_kind == StrategyKind.baseline_random_walk
    assert rw.forecast_direction == ForecastDirection.flat
    assert rw.expected_close_change_bp == 0.0
    assert rw.expected_range is None

    pd = build_prev_day_direction_forecast(request, batch_id, window_end)
    assert pd.forecast_direction == ForecastDirection.up
    assert pd.expected_close_change_bp == 12.0
    assert pd.expected_range is None

    st = build_simple_technical_forecast(request, batch_id, window_end)
    assert st.forecast_direction == ForecastDirection.up
    assert st.expected_close_change_bp == 20.0
    assert st.expected_range is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_ugh_variant_flat_epsilon_zeroes_record_bp(monkeypatch) -> None:
    from ugh_quantamental.fx_protocol import forecasting

    req = _request()
    projection_result = _projection_result(e_star=0.2, conviction=0.0)
    state_result = _state_result(req)

    def _fake_full_workflow(session, request):
        del session, request
        return FullWorkflowResult(
            projection=ProjectionWorkflowResult("proj-1", projection_result, None),
            state=StateWorkflowResult("state-1", state_result, None),
        )

    monkeypatch.setattr(forecasting, "run_full_workflow", _fake_full_workflow)

    rec = build_ugh_variant_forecast(
        object(),
        req,
        make_forecast_batch_id(req.pair, req.as_of_jst, req.protocol_version),
        datetime(2026, 3, 16, 8, 0, 0),
        variant=StrategyKind.ugh_v2_alpha,
    )

    assert rec.forecast_direction == ForecastDirection.flat
    assert rec.expected_close_change_bp == 0.0
    assert rec.expected_range is not None
    assert rec.expected_range.low_price + rec.expected_range.high_price == pytest.approx(
        2 * req.baseline_context.current_spot
    )


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_ugh_variant_preserves_caller_flat_epsilon_overrides(monkeypatch) -> None:
    from ugh_quantamental.fx_protocol import forecasting

    base_ugh_request = _full_request()
    projection = base_ugh_request.projection.model_copy(
        update={
            "config": ProjectionConfig(
                direction_flat_epsilon_ratio=0.0,
                direction_flat_epsilon_floor_bp=0.0,
            )
        }
    )
    req = _request(
        ugh_request=base_ugh_request.model_copy(update={"projection": projection})
    )
    projection_result = _projection_result(e_star=0.2, conviction=0.0)
    state_result = _state_result(req)

    def _fake_full_workflow(session, request):
        del session, request
        return FullWorkflowResult(
            projection=ProjectionWorkflowResult("proj-1", projection_result, None),
            state=StateWorkflowResult("state-1", state_result, None),
        )

    monkeypatch.setattr(forecasting, "run_full_workflow", _fake_full_workflow)

    rec = build_ugh_variant_forecast(
        object(),
        req,
        make_forecast_batch_id(req.pair, req.as_of_jst, req.protocol_version),
        datetime(2026, 3, 16, 8, 0, 0),
        variant=StrategyKind.ugh_v2_alpha,
    )

    assert rec.forecast_direction == ForecastDirection.up
    assert rec.expected_close_change_bp == pytest.approx(2.0)
    assert rec.expected_range is not None
    range_center = (rec.expected_range.low_price + rec.expected_range.high_price) / 2.0
    expected_center = req.baseline_context.current_spot * (1.0 + 2.0 / 10000.0)
    assert range_center == pytest.approx(expected_center)
    assert range_center != pytest.approx(req.baseline_context.current_spot)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_width_range_builder_enforces_half_width_floor() -> None:
    config = ProjectionConfig(range_width_scale=0.0, range_width_floor_ratio=0.5)
    snapshot = ProjectionSnapshot(
        projection_id="Will USDJPY close higher?",
        horizon_days=1,
        point_estimate=0.2,
        lower_bound=0.2,
        upper_bound=0.2,
        confidence=0.8,
    )

    expected_range = _build_range_from_projection_width(
        current_spot=150.0,
        expected_close_change_bp=10.0,
        trailing_mean_abs_close_change_bp=20.0,
        projection_snapshot=snapshot,
        config=config,
    )

    center = (expected_range.low_price + expected_range.high_price) / 2.0
    half_width = (expected_range.high_price - expected_range.low_price) / 2.0
    assert center == pytest.approx(150.0 * (1.0 + 10.0 / 10000.0))
    assert half_width == pytest.approx(150.0 * (20.0 * 0.5) / 10000.0)
    assert expected_range.low_price <= expected_range.high_price


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_width_range_builder_preserves_order_for_extreme_floor() -> None:
    config = ProjectionConfig(range_width_scale=0.0, range_width_floor_ratio=1.0)
    snapshot = ProjectionSnapshot(
        projection_id="Will USDJPY close higher?",
        horizon_days=1,
        point_estimate=0.0,
        lower_bound=0.0,
        upper_bound=0.0,
        confidence=0.8,
    )

    expected_range = _build_range_from_projection_width(
        current_spot=1.0,
        expected_close_change_bp=0.0,
        trailing_mean_abs_close_change_bp=20000.0,
        projection_snapshot=snapshot,
        config=config,
    )

    half_width = (expected_range.high_price - expected_range.low_price) / 2.0
    assert expected_range.low_price > 0.0
    assert expected_range.low_price <= expected_range.high_price
    assert half_width == pytest.approx(1.0 * 20000.0 / 10000.0)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_ugh_flat_epsilon_preserves_direction_outside_band() -> None:
    config = ProjectionConfig()

    up_dir, up_bp = _direction_from_bp_with_epsilon(3.1, 20.0, config)
    down_dir, down_bp = _direction_from_bp_with_epsilon(-3.1, 20.0, config)

    assert up_dir == ForecastDirection.up
    assert up_bp == pytest.approx(3.1)
    assert down_dir == ForecastDirection.down
    assert down_bp == pytest.approx(-3.1)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_baseline_directions_ignore_ugh_flat_epsilon() -> None:
    req = _request(
        baseline_context=BaselineContext(
            current_spot=150.0,
            previous_close_change_bp=2.0,
            trailing_mean_range_price=1.2,
            trailing_mean_abs_close_change_bp=2.0,
            sma5=150.1,
            sma20=150.0,
            warmup_window_count=20,
        )
    )
    batch_id = make_forecast_batch_id(req.pair, req.as_of_jst, req.protocol_version)
    window_end = datetime(2026, 3, 16, 8, 0, 0)

    pd = build_prev_day_direction_forecast(req, batch_id, window_end)
    st = build_simple_technical_forecast(req, batch_id, window_end)

    assert pd.forecast_direction == ForecastDirection.up
    assert pd.expected_close_change_bp == pytest.approx(2.0)
    assert st.forecast_direction == ForecastDirection.up
    assert st.expected_close_change_bp == pytest.approx(2.0)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_daily_workflow_generates_seven_with_shared_metadata(db_session, monkeypatch) -> None:
    from ugh_quantamental.fx_protocol import forecasting

    req = _request()

    projection_result = ProjectionEngineResult(
        u_score=0.4,
        alignment=0.8,
        e_raw=0.5,
        gravity_bias=0.1,
        e_star=15.0,
        mismatch_px=0.2,
        mismatch_sem=0.1,
        conviction=0.7,
        urgency=0.6,
        projection_snapshot=ProjectionSnapshot(
            projection_id="Will USDJPY close higher?",
            horizon_days=1,
            point_estimate=0.4,
            lower_bound=0.2,
            upper_bound=0.6,
            confidence=0.7,
        ),
    )
    state_result = StateEngineResult(
        evidence_scores=req.ugh_request.state.snapshot.phi.probabilities,
        updated_probabilities=req.ugh_request.state.snapshot.phi.probabilities,
        updated_phi=req.ugh_request.state.snapshot.phi,
        updated_market_svp=req.ugh_request.state.omega.market_svp,
        dominant_state=LifecycleState.setup,
        transition_confidence=0.7,
    )

    def _fake_full_workflow(session, request):
        del session, request
        return FullWorkflowResult(
            projection=ProjectionWorkflowResult(
                run_id="proj-1",
                engine_result=projection_result,
                persisted_run=None,
            ),
            state=StateWorkflowResult(
                run_id="state-1",
                engine_result=state_result,
                persisted_run=None,
            ),
        )

    monkeypatch.setattr(forecasting, "run_full_workflow", _fake_full_workflow)

    result = run_daily_forecast_workflow(db_session, req)

    # v2: 4 UGH variants (alpha/beta/gamma/delta) + 3 baselines = 7 forecasts.
    from ugh_quantamental.fx_protocol.models import EXPECTED_DAILY_BATCH_SIZE

    assert len(result.forecasts) == EXPECTED_DAILY_BATCH_SIZE
    batch_ids = {f.forecast_batch_id for f in result.forecasts}
    assert batch_ids == {result.forecast_batch_id}
    assert {f.pair for f in result.forecasts} == {CurrencyPair.USDJPY}
    _JST = ZoneInfo("Asia/Tokyo")
    assert {f.as_of_jst for f in result.forecasts} == {req.as_of_jst.replace(tzinfo=_JST)}
    assert len({f.forecast_id for f in result.forecasts}) == EXPECTED_DAILY_BATCH_SIZE

    # All 4 UGH variants share the projection result under a fake workflow.
    ugh_alpha = next(
        f for f in result.forecasts if f.strategy_kind == StrategyKind.ugh_v2_alpha
    )
    assert ugh_alpha.primary_question == "Will USDJPY close higher?"
    assert ugh_alpha.q_strength == req.ugh_request.projection.question_features.q_strength
    assert ugh_alpha.grv_lock == req.ugh_request.projection.signal_features.grv_lock
    assert ugh_alpha.e_star == 15.0
    # expected_close_change_bp = e_star * trailing_mean_abs_close_change_bp * (0.5 + 0.5*conviction)
    # = 15.0 * 20.0 * (0.5 + 0.5*0.7) = 15.0 * 20.0 * 0.85 = 255.0
    assert ugh_alpha.expected_close_change_bp == pytest.approx(255.0)
    assert ugh_alpha.forecast_direction == ForecastDirection.up


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_ugh_variant_ranges_diverge_with_projection_configs(db_session) -> None:
    req = _request(engine_version="v2.3")

    result = run_daily_forecast_workflow(db_session, req)

    ugh_ranges = {
        (
            round(f.expected_range.low_price, 8),
            round(f.expected_range.high_price, 8),
        )
        for f in result.forecasts
        if f.strategy_kind
        in {
            StrategyKind.ugh_v2_alpha,
            StrategyKind.ugh_v2_beta,
            StrategyKind.ugh_v2_gamma,
            StrategyKind.ugh_v2_delta,
        }
        and f.expected_range is not None
    }
    assert len(ugh_ranges) >= 2


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_ugh_magnitude_scales_with_volatility_and_conviction(db_session, monkeypatch) -> None:
    """UGH expected_close_change_bp must equal e_star * trailing_mean_abs_close_change_bp
    * (0.5 + 0.5*conviction). A negative e_star produces DOWN; near-zero conviction
    halves the magnitude."""
    from ugh_quantamental.fx_protocol import forecasting

    req = _request()

    projection_result = ProjectionEngineResult(
        u_score=-0.4,
        alignment=0.8,
        e_raw=-0.5,
        gravity_bias=-0.1,
        e_star=-0.6,
        mismatch_px=0.0,
        mismatch_sem=0.0,
        conviction=0.0,
        urgency=0.5,
        projection_snapshot=ProjectionSnapshot(
            projection_id="Will USDJPY close higher?",
            horizon_days=1,
            point_estimate=-0.6,
            lower_bound=-0.8,
            upper_bound=-0.4,
            confidence=0.0,
        ),
    )
    state_result = StateEngineResult(
        evidence_scores=req.ugh_request.state.snapshot.phi.probabilities,
        updated_probabilities=req.ugh_request.state.snapshot.phi.probabilities,
        updated_phi=req.ugh_request.state.snapshot.phi,
        updated_market_svp=req.ugh_request.state.omega.market_svp,
        dominant_state=LifecycleState.setup,
        transition_confidence=0.5,
    )

    def _fake_full_workflow(session, request):
        del session, request
        return FullWorkflowResult(
            projection=ProjectionWorkflowResult(
                run_id="proj-1",
                engine_result=projection_result,
                persisted_run=None,
            ),
            state=StateWorkflowResult(
                run_id="state-1",
                engine_result=state_result,
                persisted_run=None,
            ),
        )

    monkeypatch.setattr(forecasting, "run_full_workflow", _fake_full_workflow)

    result = run_daily_forecast_workflow(db_session, req)
    # All v2 variants share the projection result (same e_star, conviction)
    # under a fake full-workflow, so picking any UGH variant gives the same
    # magnitude. Use alpha as the canonical anchor.
    ugh = next(f for f in result.forecasts if f.strategy_kind == StrategyKind.ugh_v2_alpha)

    # e_star=-0.6, vol_scale=20.0, conviction=0.0 → factor=0.5
    # → -0.6 * 20.0 * 0.5 = -6.0 bp, direction=DOWN
    assert ugh.expected_close_change_bp == pytest.approx(-6.0)
    assert ugh.forecast_direction == ForecastDirection.down


def _high_fire_state_result(req: DailyForecastWorkflowRequest) -> StateEngineResult:
    """State result with a high fire probability (drives volatility expansion)."""
    probs = StateProbabilities(
        dormant=0.01, setup=0.01, fire=0.95, expansion=0.01,
        exhaustion=0.01, failure=0.01,
    )
    return StateEngineResult(
        evidence_scores=probs,
        updated_probabilities=probs,
        updated_phi=Phi(dominant_state=LifecycleState.fire, probabilities=probs),
        updated_market_svp=req.ugh_request.state.omega.market_svp,
        dominant_state=LifecycleState.fire,
        transition_confidence=0.5,
    )


def _run_ugh_alpha(db_session, monkeypatch, req, projection_result, state_result):
    from ugh_quantamental.fx_protocol import forecasting

    def _fake_full_workflow(session, request):
        del session, request
        return FullWorkflowResult(
            projection=ProjectionWorkflowResult(
                run_id="proj-1", engine_result=projection_result, persisted_run=None,
            ),
            state=StateWorkflowResult(
                run_id="state-1", engine_result=state_result, persisted_run=None,
            ),
        )

    monkeypatch.setattr(forecasting, "run_full_workflow", _fake_full_workflow)
    result = run_daily_forecast_workflow(db_session, req)
    return next(f for f in result.forecasts if f.strategy_kind == StrategyKind.ugh_v2_alpha)


class TestVolatilityExpansionMultiplier:
    def test_calm_signals_no_expansion(self) -> None:
        from ugh_quantamental.fx_protocol.forecasting import _volatility_expansion_multiplier
        cfg = ProjectionConfig()
        assert _volatility_expansion_multiplier(
            catalyst_strength=0.1, urgency=0.1, fire_probability=0.1, config=cfg,
        ) == pytest.approx(1.0)

    def test_high_signals_reach_toward_max(self) -> None:
        from ugh_quantamental.fx_protocol.forecasting import _volatility_expansion_multiplier
        cfg = ProjectionConfig()
        m = _volatility_expansion_multiplier(
            catalyst_strength=1.0, urgency=1.0, fire_probability=1.0, config=cfg,
        )
        assert m == pytest.approx(cfg.volatility_expansion_max)

    def test_monotonic_and_bounded(self) -> None:
        from ugh_quantamental.fx_protocol.forecasting import _volatility_expansion_multiplier
        cfg = ProjectionConfig()
        low = _volatility_expansion_multiplier(
            catalyst_strength=0.6, urgency=0.6, fire_probability=0.6, config=cfg,
        )
        high = _volatility_expansion_multiplier(
            catalyst_strength=0.9, urgency=0.9, fire_probability=0.9, config=cfg,
        )
        assert 1.0 <= low <= high <= cfg.volatility_expansion_max


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
@pytest.mark.parametrize("e_star", [0.9, -0.9])
def test_high_catalyst_magnitude_exceeds_trailing_mean(db_session, monkeypatch, e_star) -> None:
    """v2.5: high catalyst/urgency/fire lets |magnitude| exceed the trailing mean
    (20 bp here) — for both positive and negative e_star (sign preserved)."""
    req = _request()
    projection = _projection_result(e_star=e_star, conviction=1.0)
    projection = projection.model_copy(update={"urgency": 0.95})
    ugh = _run_ugh_alpha(db_session, monkeypatch, req, projection, _high_fire_state_result(req))

    assert abs(ugh.expected_close_change_bp) > 20.0  # trailing_mean_abs_close_change_bp
    expected_dir = ForecastDirection.up if e_star > 0 else ForecastDirection.down
    assert ugh.forecast_direction == expected_dir


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_calm_day_magnitude_unchanged(db_session, monkeypatch) -> None:
    """v2.5: low-signal (calm) days keep the pre-expansion magnitude."""
    req = _request()
    projection = _projection_result(e_star=0.6, conviction=1.0)
    projection = projection.model_copy(update={"urgency": 0.1})
    ugh = _run_ugh_alpha(db_session, monkeypatch, req, projection, _state_result(req))

    # mean(catalyst=0.6, urgency=0.1, fire=0.2) = 0.3 < floor(0.5) -> multiplier 1.0.
    # magnitude = e_star * 20 * (0.5 + 0.5*1.0) = 0.6 * 20 * 1.0 = 12.0 bp.
    assert ugh.expected_close_change_bp == pytest.approx(12.0)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_expansion_does_not_cross_flat_epsilon(db_session, monkeypatch) -> None:
    """v2.5 invariant: a below-epsilon FLAT forecast stays FLAT even with high
    catalyst/urgency/fire — direction/FLAT is decided pre-expansion."""
    req = _request()
    # e_star=0.2, conviction=0.0 -> pre-expansion 0.2*20*0.5 = 2.0 bp <= 3.0 floor.
    projection = _projection_result(e_star=0.2, conviction=0.0)
    projection = projection.model_copy(update={"urgency": 0.99})
    ugh = _run_ugh_alpha(db_session, monkeypatch, req, projection, _high_fire_state_result(req))

    assert ugh.forecast_direction == ForecastDirection.flat
    assert ugh.expected_close_change_bp == 0.0


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_idempotent_rerun_and_partial_batch_error(db_session, monkeypatch) -> None:
    from ugh_quantamental.fx_protocol import forecasting

    req = _request()

    projection_result = ProjectionEngineResult(
        u_score=0.4,
        alignment=0.8,
        e_raw=0.5,
        gravity_bias=0.1,
        e_star=15.0,
        mismatch_px=0.2,
        mismatch_sem=0.1,
        conviction=0.7,
        urgency=0.6,
        projection_snapshot=ProjectionSnapshot(
            projection_id="Will USDJPY close higher?",
            horizon_days=1,
            point_estimate=0.4,
            lower_bound=0.2,
            upper_bound=0.6,
            confidence=0.7,
        ),
    )
    state_result = StateEngineResult(
        evidence_scores=req.ugh_request.state.snapshot.phi.probabilities,
        updated_probabilities=req.ugh_request.state.snapshot.phi.probabilities,
        updated_phi=req.ugh_request.state.snapshot.phi,
        updated_market_svp=req.ugh_request.state.omega.market_svp,
        dominant_state=LifecycleState.setup,
        transition_confidence=0.7,
    )

    def _fake_full_workflow(session, request):
        del session, request
        return FullWorkflowResult(
            projection=ProjectionWorkflowResult("proj-1", projection_result, None),
            state=StateWorkflowResult("state-1", state_result, None),
        )

    monkeypatch.setattr(forecasting, "run_full_workflow", _fake_full_workflow)

    from ugh_quantamental.fx_protocol.models import EXPECTED_DAILY_BATCH_SIZE

    first = run_daily_forecast_workflow(db_session, req)
    second = run_daily_forecast_workflow(db_session, req)
    assert second.forecast_batch_id == first.forecast_batch_id
    assert len(second.forecasts) == EXPECTED_DAILY_BATCH_SIZE

    from ugh_quantamental.persistence.models import FxForecastRecord

    row = db_session.get(FxForecastRecord, first.forecasts[0].forecast_id)
    db_session.delete(row)
    db_session.flush()

    with pytest.raises(ValueError, match="partial forecast batch exists"):
        run_daily_forecast_workflow(db_session, req)
