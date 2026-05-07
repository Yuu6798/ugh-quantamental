"""Tests for outcome construction, evaluation generation, and disconfirmer audit."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone

import pytest

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    DisconfirmerRule,
    EventTag,
    ExpectedRange,
    ForecastDirection,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.outcome_models import DailyOutcomeWorkflowRequest
from ugh_quantamental.fx_protocol.outcomes import (
    build_evaluation_record,
    build_outcome_record,
    compute_disconfirmers_hit,
)

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

if HAS_SQLALCHEMY:
    from ugh_quantamental.fx_protocol.outcomes import run_daily_outcome_evaluation_workflow

_UTC = timezone.utc


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 16, 0, 0, 0, tzinfo=_UTC),
    )


def _outcome_request(**kwargs) -> DailyOutcomeWorkflowRequest:
    base = dict(
        pair=CurrencyPair.USDJPY,
        window_start_jst=datetime(2026, 3, 13, 8, 0, 0),
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        market_data_provenance=_provenance(),
        realized_open=150.0,
        realized_high=151.0,
        realized_low=149.5,
        realized_close=150.8,
        schema_version="v1",
        protocol_version="v1",
    )
    base.update(kwargs)
    return DailyOutcomeWorkflowRequest(**base)


def _outcome_up() -> OutcomeRecord:
    """Outcome where close > open (up direction)."""
    req = _outcome_request()
    return build_outcome_record(req)


def _outcome_down() -> OutcomeRecord:
    """Outcome where close < open (down direction)."""
    return build_outcome_record(
        _outcome_request(
            realized_open=150.0,
            realized_high=151.0,
            realized_low=148.0,
            realized_close=149.0,
        )
    )


def _outcome_flat() -> OutcomeRecord:
    """Outcome where close == open (flat direction)."""
    return build_outcome_record(
        _outcome_request(
            realized_open=150.0,
            realized_high=150.5,
            realized_low=149.5,
            realized_close=150.0,
        )
    )


# ---------------------------------------------------------------------------
# Forecast fixture helpers (minimal ForecastRecord construction)
# ---------------------------------------------------------------------------


def _make_ugh_forecast(
    *,
    direction: ForecastDirection = ForecastDirection.up,
    expected_close_change_bp: float = 53.0,
    expected_range: ExpectedRange | None = None,
    disconfirmers: tuple[DisconfirmerRule, ...] = (),
    dominant_state_value: str = "setup",
) -> object:
    """Build a minimal UGH ForecastRecord for testing."""
    from zoneinfo import ZoneInfo

    from ugh_quantamental.fx_protocol.ids import make_forecast_id
    from ugh_quantamental.fx_protocol.models import ForecastRecord
    from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
    from ugh_quantamental.schemas.market_svp import StateProbabilities

    _JST = ZoneInfo("Asia/Tokyo")
    probs = StateProbabilities(
        dormant=0.05, setup=0.5, fire=0.2, expansion=0.15, exhaustion=0.05, failure=0.05
    )
    pair = CurrencyPair.USDJPY
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)

    return ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of, "v1", StrategyKind.ugh),
        forecast_batch_id="fb_test",
        pair=pair,
        strategy_kind=StrategyKind.ugh,
        as_of_jst=as_of,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=_UTC),
        market_data_provenance=_provenance(),
        forecast_direction=direction,
        expected_close_change_bp=expected_close_change_bp,
        expected_range=expected_range or ExpectedRange(low_price=149.0, high_price=151.5),
        disconfirmers=disconfirmers,
        dominant_state=LifecycleState(dominant_state_value),
        state_probabilities=probs,
        q_dir=QuestionDirection.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.8,
        grv_raw=0.1,
        grv_lock=0.7,
        alignment=0.8,
        e_star=expected_close_change_bp,
        mismatch_px=0.2,
        mismatch_sem=0.1,
        conviction=0.7,
        urgency=0.6,
        input_snapshot_ref="ref/001",
        primary_question="Will USDJPY close higher?",
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _make_baseline_forecast(strategy_kind: StrategyKind) -> object:
    from zoneinfo import ZoneInfo

    from ugh_quantamental.fx_protocol.ids import make_forecast_id
    from ugh_quantamental.fx_protocol.models import ForecastRecord

    _JST = ZoneInfo("Asia/Tokyo")
    pair = CurrencyPair.USDJPY
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)

    if strategy_kind == StrategyKind.baseline_random_walk:
        direction = ForecastDirection.flat
        bp = 0.0
    else:
        direction = ForecastDirection.up
        bp = 12.0

    return ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of, "v1", strategy_kind),
        forecast_batch_id="fb_test",
        pair=pair,
        strategy_kind=strategy_kind,
        as_of_jst=as_of,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=_UTC),
        market_data_provenance=_provenance(),
        forecast_direction=direction,
        expected_close_change_bp=bp,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


# ---------------------------------------------------------------------------
# build_outcome_record
# ---------------------------------------------------------------------------


def test_outcome_direction_up() -> None:
    outcome = _outcome_up()
    assert outcome.realized_direction == ForecastDirection.up
    assert outcome.realized_close_change_bp > 0


def test_outcome_direction_down() -> None:
    outcome = _outcome_down()
    assert outcome.realized_direction == ForecastDirection.down
    assert outcome.realized_close_change_bp < 0


def test_outcome_direction_flat() -> None:
    outcome = _outcome_flat()
    assert outcome.realized_direction == ForecastDirection.flat
    assert outcome.realized_close_change_bp == 0.0


def test_outcome_derived_fields() -> None:
    req = _outcome_request()
    outcome = build_outcome_record(req)
    expected_bp = (150.8 - 150.0) / 150.0 * 10_000
    assert abs(outcome.realized_close_change_bp - expected_bp) < 1e-6
    assert abs(outcome.realized_range_price - (151.0 - 149.5)) < 1e-9


def test_outcome_event_happened_false_when_no_tags() -> None:
    outcome = build_outcome_record(_outcome_request())
    assert outcome.event_happened is False
    assert outcome.event_tags == ()


def test_outcome_event_happened_true_with_tags() -> None:
    outcome = build_outcome_record(_outcome_request(event_tags=(EventTag.fomc,)))
    assert outcome.event_happened is True
    assert EventTag.fomc in outcome.event_tags


def test_outcome_id_is_deterministic() -> None:
    o1 = build_outcome_record(_outcome_request())
    o2 = build_outcome_record(_outcome_request())
    assert o1.outcome_id == o2.outcome_id


# ---------------------------------------------------------------------------
# build_evaluation_record — UGH
# ---------------------------------------------------------------------------


def test_ugh_direction_hit_true() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(direction=ForecastDirection.up, expected_close_change_bp=53.0)
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.direction_hit is True


def test_ugh_direction_hit_false() -> None:
    outcome = _outcome_down()
    forecast = _make_ugh_forecast(direction=ForecastDirection.up, expected_close_change_bp=53.0)
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.direction_hit is False


def test_ugh_range_hit_true() -> None:
    outcome = _outcome_up()  # realized_close=150.8
    forecast = _make_ugh_forecast(
        direction=ForecastDirection.up,
        expected_close_change_bp=53.0,
        expected_range=ExpectedRange(low_price=149.0, high_price=152.0),
    )
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.range_hit is True


def test_ugh_range_hit_false() -> None:
    outcome = _outcome_up()  # realized_close=150.8
    forecast = _make_ugh_forecast(
        direction=ForecastDirection.up,
        expected_close_change_bp=53.0,
        expected_range=ExpectedRange(low_price=151.0, high_price=152.0),
    )
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.range_hit is False


def test_ugh_error_metrics_computed() -> None:
    outcome = _outcome_up()
    realized_bp = outcome.realized_close_change_bp
    forecast_bp = 30.0
    forecast = _make_ugh_forecast(
        direction=ForecastDirection.up,
        expected_close_change_bp=forecast_bp,
    )
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert abs(ev.close_error_bp - abs(forecast_bp - realized_bp)) < 1e-9
    assert abs(ev.magnitude_error_bp - abs(abs(forecast_bp) - abs(realized_bp))) < 1e-9


def test_ugh_mismatch_change_bp() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(
        direction=ForecastDirection.up,
        expected_close_change_bp=30.0,
    )
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    expected_mismatch = outcome.realized_close_change_bp - 30.0
    assert abs(ev.mismatch_change_bp - expected_mismatch) < 1e-9


def test_ugh_state_proxy_hit_when_match() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(dominant_state_value="setup")
    ev = build_evaluation_record(forecast, outcome, "setup", datetime.now(_UTC))
    assert ev.state_proxy_hit is True
    assert ev.actual_state_change is False
    assert ev.realized_state_proxy == "setup"


def test_ugh_state_proxy_hit_when_mismatch() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(dominant_state_value="setup")
    ev = build_evaluation_record(forecast, outcome, "fire", datetime.now(_UTC))
    assert ev.state_proxy_hit is False
    assert ev.actual_state_change is True
    assert ev.realized_state_proxy == "fire"


def test_ugh_state_proxy_none_when_no_next_batch() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast()
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.state_proxy_hit is None
    assert ev.actual_state_change is None
    assert ev.realized_state_proxy is None


# ---------------------------------------------------------------------------
# build_evaluation_record — baselines
# ---------------------------------------------------------------------------


def test_baseline_range_hit_is_none() -> None:
    for sk in (
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    ):
        forecast = _make_baseline_forecast(sk)
        outcome = _outcome_up()
        ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
        assert ev.range_hit is None, f"range_hit should be None for {sk}"


def test_baseline_ugh_only_fields_are_none() -> None:
    forecast = _make_baseline_forecast(StrategyKind.baseline_random_walk)
    outcome = _outcome_up()
    ev = build_evaluation_record(forecast, outcome, "setup", datetime.now(_UTC))
    assert ev.state_proxy_hit is None
    assert ev.mismatch_change_bp is None
    assert ev.realized_state_proxy is None
    assert ev.actual_state_change is None


# ---------------------------------------------------------------------------
# disconfirmer audit
# ---------------------------------------------------------------------------


def _rule(
    rule_id: str,
    audit_kind: str,
    operator: str,
    threshold_value,
    target_field: str = "close_change_bp",
) -> DisconfirmerRule:
    return DisconfirmerRule(
        rule_id=rule_id,
        label=f"rule {rule_id}",
        audit_kind=audit_kind,
        target_field=target_field,
        operator=operator,
        threshold_value=threshold_value,
        window_scope="daily",
    )


def test_disconfirmer_event_tag_hit() -> None:
    outcome = build_outcome_record(_outcome_request(event_tags=(EventTag.fomc,)))
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r1", "event_tag", "check", "fomc", target_field="event_tags"),
        )
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r1" in hit


def test_disconfirmer_event_tag_miss() -> None:
    outcome = build_outcome_record(_outcome_request(event_tags=()))
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r1", "event_tag", "check", "fomc", target_field="event_tags"),
        )
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r1" not in hit



def test_disconfirmer_event_tag_unsupported_operator_raises() -> None:
    outcome = build_outcome_record(_outcome_request(event_tags=(EventTag.fomc,)))
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r1_bad_op", "event_tag", "invalid_op", "fomc", target_field="event_tags"),
        )
    )
    with pytest.raises(ValueError, match="r1_bad_op"):
        compute_disconfirmers_hit(forecast, outcome, None)

def test_disconfirmer_close_change_bp_gt_hit() -> None:
    outcome = _outcome_up()  # bp > 0
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r2", "close_change_bp", "gt", -100.0),
        )
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r2" in hit


def test_disconfirmer_close_change_bp_lte_miss() -> None:
    outcome = _outcome_up()  # bp > 0
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r3", "close_change_bp", "lte", 0.0),
        )
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r3" not in hit


def test_disconfirmer_state_proxy_eq_hit() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r4", "state_proxy", "eq", "fire", target_field="realized_state_proxy"),
        )
    )
    hit = compute_disconfirmers_hit(forecast, outcome, "fire")
    assert "r4" in hit


def test_disconfirmer_state_proxy_none_does_not_fire() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r5", "state_proxy", "eq", "fire", target_field="realized_state_proxy"),
        )
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r5" not in hit


def test_disconfirmer_range_break_below_low_hit() -> None:
    outcome = _outcome_up()  # realized_close = 150.8
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r6", "range_break", "check", "below_expected_low"),
        ),
        expected_range=ExpectedRange(low_price=151.0, high_price=152.0),  # close below low
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r6" in hit


def test_disconfirmer_range_break_above_high_hit() -> None:
    outcome = _outcome_up()  # realized_close = 150.8
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r7", "range_break", "check", "above_expected_high"),
        ),
        expected_range=ExpectedRange(low_price=149.0, high_price=150.5),  # close above high
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r7" in hit


def test_disconfirmer_range_break_outside_range_miss() -> None:
    outcome = _outcome_up()  # realized_close = 150.8
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r8", "range_break", "check", "outside_expected_range"),
        ),
        expected_range=ExpectedRange(low_price=149.0, high_price=152.0),  # inside range
    )
    hit = compute_disconfirmers_hit(forecast, outcome, None)
    assert "r8" not in hit


def test_disconfirmer_unsupported_audit_kind_raises() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r9", "close_change_bp", "unknown_op", 0.0),
        )
    )
    with pytest.raises(ValueError, match="unsupported operator"):
        compute_disconfirmers_hit(forecast, outcome, None)



def test_disconfirmer_range_break_unsupported_operator_raises() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r10_bad_op", "range_break", "invalid_op", "below_expected_low"),
        ),
    )
    with pytest.raises(ValueError, match="r10_bad_op"):
        compute_disconfirmers_hit(forecast, outcome, None)

def test_disconfirmer_range_break_unsupported_threshold_raises() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(
        disconfirmers=(
            _rule("r10", "range_break", "check", "invalid_threshold"),
        ),
    )
    with pytest.raises(ValueError, match="unsupported threshold_value"):
        compute_disconfirmers_hit(forecast, outcome, None)


# ---------------------------------------------------------------------------
# disconfirmer_explained
# ---------------------------------------------------------------------------


def test_disconfirmer_explained_true_when_miss_and_fired() -> None:
    outcome = _outcome_down()  # realized_direction = down
    forecast = _make_ugh_forecast(
        direction=ForecastDirection.up,  # direction miss
        expected_close_change_bp=53.0,
        disconfirmers=(
            _rule("r11", "close_change_bp", "lt", 0.0),  # close_change_bp < 0 → fires for down
        ),
    )
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.direction_hit is False
    assert "r11" in ev.disconfirmers_hit
    assert ev.disconfirmer_explained is True


def test_disconfirmer_explained_false_when_hit() -> None:
    outcome = _outcome_up()
    forecast = _make_ugh_forecast(direction=ForecastDirection.up, expected_close_change_bp=53.0)
    ev = build_evaluation_record(forecast, outcome, None, datetime.now(_UTC))
    assert ev.direction_hit is True
    assert ev.disconfirmer_explained is False


# ---------------------------------------------------------------------------
# Workflow tests (SQLAlchemy-gated)
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():
    if not HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine()
    create_all_tables(engine)
    session = create_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()


def _seed_forecast_batch(session, as_of_jst, batch_id_override: str | None = None):
    """Seed a v2-shaped forecast batch (4 UGH variants + 3 baselines = 7).

    All 4 v2 UGH variants share the same UGH-engine-derived fields under this
    fixture; the only thing that differs across variants is ``strategy_kind``
    (and, transitively, ``forecast_id``). This keeps the v1 test assertions
    valid when they switch from selecting ``StrategyKind.ugh`` to selecting
    one of the v2 variants.
    """
    from zoneinfo import ZoneInfo

    from ugh_quantamental.fx_protocol.ids import make_forecast_batch_id
    from ugh_quantamental.fx_protocol.models import ForecastRecord
    from ugh_quantamental.persistence.repositories import FxForecastRepository
    from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
    from ugh_quantamental.schemas.market_svp import StateProbabilities

    _JST = ZoneInfo("Asia/Tokyo")
    pair = CurrencyPair.USDJPY
    prot = "v1"
    batch_id = batch_id_override or make_forecast_batch_id(pair, as_of_jst, prot)
    window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST) if as_of_jst.day == 13 else datetime(2026, 3, 17, 8, 0, 0, tzinfo=_JST)

    from ugh_quantamental.fx_protocol.ids import make_forecast_id

    probs = StateProbabilities(
        dormant=0.05, setup=0.5, fire=0.2, expansion=0.15, exhaustion=0.05, failure=0.05
    )

    base_rec = dict(
        forecast_batch_id=batch_id,
        pair=pair,
        as_of_jst=as_of_jst,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=timezone.utc),
        market_data_provenance=_provenance(),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )

    ugh_kwargs_common = dict(
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=53.0,
        expected_range=ExpectedRange(low_price=149.0, high_price=152.0),
        dominant_state=LifecycleState.setup,
        state_probabilities=probs,
        q_dir=QuestionDirection.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.8,
        grv_raw=0.1,
        grv_lock=0.7,
        alignment=0.8,
        e_star=53.0,
        mismatch_px=0.2,
        mismatch_sem=0.1,
        conviction=0.7,
        urgency=0.6,
        input_snapshot_ref="ref/001",
        primary_question="Will USDJPY close higher?",
    )

    ugh_variant_recs = tuple(
        ForecastRecord(
            forecast_id=make_forecast_id(pair, as_of_jst, prot, variant),
            strategy_kind=variant,
            **ugh_kwargs_common,
            **base_rec,
        )
        for variant in (
            StrategyKind.ugh_v2_alpha,
            StrategyKind.ugh_v2_beta,
            StrategyKind.ugh_v2_gamma,
            StrategyKind.ugh_v2_delta,
        )
    )

    rw_rec = ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of_jst, prot, StrategyKind.baseline_random_walk),
        strategy_kind=StrategyKind.baseline_random_walk,
        forecast_direction=ForecastDirection.flat,
        expected_close_change_bp=0.0,
        **base_rec,
    )
    pd_rec = ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of_jst, prot, StrategyKind.baseline_prev_day_direction),
        strategy_kind=StrategyKind.baseline_prev_day_direction,
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=12.0,
        **base_rec,
    )
    st_rec = ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of_jst, prot, StrategyKind.baseline_simple_technical),
        strategy_kind=StrategyKind.baseline_simple_technical,
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=20.0,
        **base_rec,
    )

    FxForecastRepository.save_fx_forecast_batch(
        session,
        forecast_batch_id=batch_id,
        forecasts=(*ugh_variant_recs, rw_rec, pd_rec, st_rec),
    )
    return batch_id


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_workflow_generates_outcome_and_seven_evaluations(db_session) -> None:
    from zoneinfo import ZoneInfo

    from ugh_quantamental.fx_protocol.models import EXPECTED_DAILY_BATCH_SIZE

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    assert result.outcome.realized_direction == ForecastDirection.up
    assert len(result.evaluations) == EXPECTED_DAILY_BATCH_SIZE


def test_all_evaluations_share_one_outcome(db_session) -> None:
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    outcome_ids = {ev.outcome_id for ev in result.evaluations}
    assert outcome_ids == {result.outcome.outcome_id}


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_ugh_evaluation_has_range_hit_set(db_session) -> None:
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    ugh_ev = next(
        ev for ev in result.evaluations if ev.strategy_kind == StrategyKind.ugh_v2_alpha
    )
    assert ugh_ev.range_hit is not None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_baseline_evaluations_have_range_hit_none(db_session) -> None:
    from zoneinfo import ZoneInfo

    from ugh_quantamental.fx_protocol.models import is_ugh_kind

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    for ev in result.evaluations:
        if not is_ugh_kind(ev.strategy_kind):
            assert ev.range_hit is None, f"baseline {ev.strategy_kind} should have range_hit=None"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_proxy_from_next_day_batch(db_session) -> None:
    """If next-day batch exists, UGH dominant_state is used as realized_state_proxy."""
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    as_of_day1 = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    as_of_day2 = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of_day1)
    _seed_forecast_batch(db_session, as_of_day2)

    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    ugh_ev = next(
        ev for ev in result.evaluations if ev.strategy_kind == StrategyKind.ugh_v2_alpha
    )
    # The next-day batch has dominant_state=setup, so realized_state_proxy should be "setup"
    assert ugh_ev.realized_state_proxy == "setup"
    assert ugh_ev.state_proxy_hit is not None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_proxy_none_when_next_batch_absent(db_session) -> None:
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    # No next-day batch seeded
    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    ugh_ev = next(
        ev for ev in result.evaluations if ev.strategy_kind == StrategyKind.ugh_v2_alpha
    )
    assert ugh_ev.realized_state_proxy is None
    assert ugh_ev.state_proxy_hit is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_idempotent_rerun_returns_same_outcome_and_evaluations(db_session) -> None:
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    req = _outcome_request()
    result1 = run_daily_outcome_evaluation_workflow(db_session, req)
    result2 = run_daily_outcome_evaluation_workflow(db_session, req)

    assert result1.outcome.outcome_id == result2.outcome.outcome_id
    eval_ids_1 = {ev.evaluation_id for ev in result1.evaluations}
    eval_ids_2 = {ev.evaluation_id for ev in result2.evaluations}
    assert eval_ids_1 == eval_ids_2


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_missing_forecast_batch_raises(db_session) -> None:
    req = _outcome_request()
    with pytest.raises(ValueError, match="No forecast batch found"):
        run_daily_outcome_evaluation_workflow(db_session, req)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_partial_evaluation_batch_raises(db_session) -> None:
    from zoneinfo import ZoneInfo

    from ugh_quantamental.persistence.models import FxEvaluationRecord

    _JST = ZoneInfo("Asia/Tokyo")
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    _seed_forecast_batch(db_session, as_of)

    req = _outcome_request()
    result = run_daily_outcome_evaluation_workflow(db_session, req)

    # Delete one evaluation to simulate a partial batch
    ev_to_delete = db_session.get(FxEvaluationRecord, result.evaluations[0].evaluation_id)
    db_session.delete(ev_to_delete)
    db_session.flush()

    with pytest.raises(ValueError, match="Partial evaluation batch"):
        run_daily_outcome_evaluation_workflow(db_session, req)
