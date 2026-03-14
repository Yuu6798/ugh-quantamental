"""Tests for deterministic daily forecast workflow generation."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone

import pytest

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
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
        build_prev_day_direction_forecast,
        build_random_walk_forecast,
        build_simple_technical_forecast,
        run_daily_forecast_workflow,
    )
else:
    build_prev_day_direction_forecast = None
    build_random_walk_forecast = None
    build_simple_technical_forecast = None
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


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_baseline_construction_rules_are_deterministic() -> None:
    request = _request()
    batch_id = make_forecast_batch_id(request.pair, request.as_of_jst, request.protocol_version)
    window_end = datetime(2026, 3, 16, 8, 0, 0)

    rw = build_random_walk_forecast(request, batch_id, window_end)
    assert rw.strategy_kind == StrategyKind.baseline_random_walk
    assert rw.forecast_direction == ForecastDirection.flat
    assert rw.expected_close_change_bp == 0.0
    assert rw.expected_range.low_price == pytest.approx(149.4)
    assert rw.expected_range.high_price == pytest.approx(150.6)

    pd = build_prev_day_direction_forecast(request, batch_id, window_end)
    assert pd.forecast_direction == ForecastDirection.up
    assert pd.expected_close_change_bp == 12.0

    st = build_simple_technical_forecast(request, batch_id, window_end)
    assert st.forecast_direction == ForecastDirection.up
    assert st.expected_close_change_bp == 20.0


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_daily_workflow_generates_exactly_four_with_shared_metadata(db_session, monkeypatch) -> None:
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

    assert len(result.forecasts) == 4
    batch_ids = {f.forecast_batch_id for f in result.forecasts}
    assert batch_ids == {result.forecast_batch_id}
    assert {f.pair for f in result.forecasts} == {CurrencyPair.USDJPY}
    assert {f.as_of_jst for f in result.forecasts} == {req.as_of_jst}
    assert len({f.forecast_id for f in result.forecasts}) == 4

    ugh = next(f for f in result.forecasts if f.strategy_kind == StrategyKind.ugh)
    assert ugh.primary_question == "Will USDJPY close higher?"
    assert ugh.q_strength == req.ugh_request.projection.question_features.q_strength
    assert ugh.grv_lock == req.ugh_request.projection.signal_features.grv_lock
    assert ugh.e_star == 15.0


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

    first = run_daily_forecast_workflow(db_session, req)
    second = run_daily_forecast_workflow(db_session, req)
    assert second.forecast_batch_id == first.forecast_batch_id
    assert len(second.forecasts) == 4

    from ugh_quantamental.persistence.models import FxForecastRecord

    row = db_session.get(FxForecastRecord, first.forecasts[0].forecast_id)
    db_session.delete(row)
    db_session.flush()

    with pytest.raises(ValueError, match="partial forecast batch exists"):
        run_daily_forecast_workflow(db_session, req)
