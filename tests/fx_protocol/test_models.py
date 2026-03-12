"""Tests for fx_protocol.models — enumerations, support models, and record contracts."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    DisconfirmerRule,
    EvaluationRecord,
    EventTag,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
from ugh_quantamental.schemas.market_svp import StateProbabilities

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

_UTC = timezone.utc
_NOW = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_UTC)
_AS_OF = datetime(2026, 3, 10, 8, 0, 0)
_WINDOW_END = datetime(2026, 3, 11, 8, 0, 0)


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test_vendor",
        feed_name="test_feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=_NOW,
    )


def _state_probs() -> StateProbabilities:
    return StateProbabilities(
        dormant=0.0,
        setup=0.0,
        fire=1.0,
        expansion=0.0,
        exhaustion=0.0,
        failure=0.0,
    )


def _expected_range() -> ExpectedRange:
    return ExpectedRange(low_price=149.0, high_price=151.0)


def _disconfirmer() -> DisconfirmerRule:
    return DisconfirmerRule(
        rule_id="dc_01",
        label="FOMC event disconfirmer",
        audit_kind="event_tag",
        target_field="event_tags",
        operator="contains",
        threshold_value="fomc",
        window_scope="current",
    )


def _ugh_forecast(**overrides) -> ForecastRecord:
    base = dict(
        forecast_id="fc_test_001",
        forecast_batch_id="fb_test_001",
        pair=CurrencyPair.USDJPY,
        strategy_kind=StrategyKind.ugh,
        as_of_jst=_AS_OF,
        window_end_jst=_WINDOW_END,
        locked_at_utc=_NOW,
        market_data_provenance=_provenance(),
        input_snapshot_ref="ssv_snap_001",
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=30.0,
        expected_range=_expected_range(),
        primary_question="Will USDJPY close higher?",
        disconfirmers=(_disconfirmer(),),
        dominant_state=LifecycleState.fire,
        state_probabilities=_state_probs(),
        q_dir=QuestionDirection.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.8,
        grv_raw=0.2,
        grv_lock=0.3,
        alignment=0.5,
        e_star=0.4,
        mismatch_px=0.1,
        mismatch_sem=0.05,
        conviction=0.6,
        urgency=0.7,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )
    base.update(overrides)
    return ForecastRecord(**base)


def _baseline_forecast(strategy_kind: StrategyKind, **overrides) -> ForecastRecord:
    base = dict(
        forecast_id="fc_baseline_001",
        forecast_batch_id="fb_baseline_001",
        pair=CurrencyPair.USDJPY,
        strategy_kind=strategy_kind,
        as_of_jst=_AS_OF,
        window_end_jst=_WINDOW_END,
        locked_at_utc=_NOW,
        market_data_provenance=_provenance(),
        forecast_direction=ForecastDirection.flat,
        expected_close_change_bp=0.0,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )
    base.update(overrides)
    return ForecastRecord(**base)


def _outcome(**overrides) -> OutcomeRecord:
    base = dict(
        outcome_id="oc_test_001",
        pair=CurrencyPair.USDJPY,
        window_start_jst=_AS_OF,
        window_end_jst=_WINDOW_END,
        market_data_provenance=_provenance(),
        realized_open=149.5,
        realized_high=150.8,
        realized_low=149.2,
        realized_close=150.5,
        realized_direction=ForecastDirection.up,
        realized_close_change_bp=67.0,
        realized_range_price=1.6,
        event_happened=False,
        event_tags=(),
        schema_version="v1",
        protocol_version="v1",
    )
    base.update(overrides)
    return OutcomeRecord(**base)


def _evaluation(**overrides) -> EvaluationRecord:
    base = dict(
        evaluation_id="ev_test_001",
        forecast_id="fc_test_001",
        outcome_id="oc_test_001",
        pair=CurrencyPair.USDJPY,
        strategy_kind=StrategyKind.ugh,
        direction_hit=True,
        evaluated_at_utc=_NOW,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )
    base.update(overrides)
    return EvaluationRecord(**base)


# ---------------------------------------------------------------------------
# Enumeration tests
# ---------------------------------------------------------------------------


def test_currency_pair_usdjpy_exists() -> None:
    assert CurrencyPair.USDJPY == CurrencyPair("USDJPY")


def test_strategy_kind_all_values() -> None:
    expected = {"ugh", "baseline_random_walk", "baseline_prev_day_direction", "baseline_simple_technical"}
    assert {s.value for s in StrategyKind} == expected


def test_forecast_direction_all_values() -> None:
    assert {d.value for d in ForecastDirection} == {"up", "down", "flat"}


def test_event_tag_all_values() -> None:
    expected = {
        "fomc", "boj", "cpi_us", "nfp_us", "jp_holiday", "us_holiday",
        "month_end", "quarter_end", "other_macro", "unscheduled_event",
    }
    assert {t.value for t in EventTag} == expected


# ---------------------------------------------------------------------------
# ExpectedRange tests
# ---------------------------------------------------------------------------


def test_expected_range_valid() -> None:
    r = ExpectedRange(low_price=149.0, high_price=151.0)
    assert r.low_price == 149.0
    assert r.high_price == 151.0


def test_expected_range_equal_bounds_is_valid() -> None:
    r = ExpectedRange(low_price=150.0, high_price=150.0)
    assert r.low_price == r.high_price


def test_expected_range_ordering_violated() -> None:
    with pytest.raises(ValidationError, match="low_price must be <= high_price"):
        ExpectedRange(low_price=151.0, high_price=149.0)


@pytest.mark.parametrize("bad_value", [float("inf"), float("-inf"), float("nan")])
def test_expected_range_non_finite_low(bad_value: float) -> None:
    with pytest.raises(ValidationError, match="finite"):
        ExpectedRange(low_price=bad_value, high_price=151.0)


@pytest.mark.parametrize("bad_value", [float("inf"), float("-inf"), float("nan")])
def test_expected_range_non_finite_high(bad_value: float) -> None:
    with pytest.raises(ValidationError, match="finite"):
        ExpectedRange(low_price=149.0, high_price=bad_value)


# ---------------------------------------------------------------------------
# MarketDataProvenance tests
# ---------------------------------------------------------------------------


def test_market_data_provenance_valid() -> None:
    p = _provenance()
    assert p.vendor == "test_vendor"
    assert p.price_type == "mid"
    assert p.source_ref is None


def test_market_data_provenance_with_source_ref() -> None:
    p = MarketDataProvenance(
        vendor="v",
        feed_name="f",
        price_type="mid",
        resolution="1d",
        timezone="UTC",
        retrieved_at_utc=_NOW,
        source_ref="ref_abc",
    )
    assert p.source_ref == "ref_abc"


def test_market_data_provenance_rejects_non_mid() -> None:
    with pytest.raises(ValidationError):
        MarketDataProvenance(  # type: ignore[call-arg]
            vendor="v",
            feed_name="f",
            price_type="ask",  # invalid
            resolution="1d",
            timezone="UTC",
            retrieved_at_utc=_NOW,
        )


# ---------------------------------------------------------------------------
# DisconfirmerRule tests
# ---------------------------------------------------------------------------


def test_disconfirmer_rule_valid() -> None:
    d = _disconfirmer()
    assert d.rule_id == "dc_01"
    assert d.audit_kind == "event_tag"
    assert d.threshold_value == "fomc"


def test_disconfirmer_rule_none_threshold() -> None:
    d = DisconfirmerRule(
        rule_id="dc_02",
        label="range break",
        audit_kind="range_break",
        target_field="realized_range_price",
        operator="gt",
        threshold_value=None,
        window_scope="current",
    )
    assert d.threshold_value is None


# ---------------------------------------------------------------------------
# ForecastRecord — UGH strategy
# ---------------------------------------------------------------------------


def test_forecast_record_ugh_valid() -> None:
    rec = _ugh_forecast()
    assert rec.strategy_kind == StrategyKind.ugh
    assert rec.dominant_state == LifecycleState.fire
    assert rec.conviction == 0.6


def test_forecast_record_ugh_frozen() -> None:
    rec = _ugh_forecast()
    with pytest.raises(Exception):
        rec.conviction = 0.9  # type: ignore[misc]


def test_forecast_record_ugh_missing_ugh_field_raises() -> None:
    with pytest.raises(ValidationError, match="ugh.*requires non-null"):
        _ugh_forecast(dominant_state=None)


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_forecast_record_ugh_each_ugh_field_required(field: str) -> None:
    """Setting any single UGH field to None must raise a ValidationError."""
    with pytest.raises(ValidationError):
        _ugh_forecast(**{field: None})


# ---------------------------------------------------------------------------
# ForecastRecord — baseline strategies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "strategy_kind",
    [
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    ],
)
def test_forecast_record_baseline_ugh_fields_nullable(strategy_kind: StrategyKind) -> None:
    rec = _baseline_forecast(strategy_kind)
    assert rec.dominant_state is None
    assert rec.state_probabilities is None
    assert rec.q_dir is None
    assert rec.expected_range is None
    assert rec.input_snapshot_ref is None
    assert rec.primary_question is None


@pytest.mark.parametrize(
    "strategy_kind",
    [
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    ],
)
def test_forecast_record_baseline_disconfirmers_empty_allowed(strategy_kind: StrategyKind) -> None:
    rec = _baseline_forecast(strategy_kind)
    assert rec.disconfirmers == ()


@pytest.mark.parametrize(
    "strategy_kind",
    [
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    ],
)
def test_forecast_record_baseline_requires_direction(strategy_kind: StrategyKind) -> None:
    with pytest.raises((ValidationError, TypeError)):
        _baseline_forecast(strategy_kind, forecast_direction=None)  # type: ignore[arg-type]


def test_forecast_record_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        _ugh_forecast(unknown_field="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# OutcomeRecord tests
# ---------------------------------------------------------------------------


def test_outcome_record_valid() -> None:
    rec = _outcome()
    assert rec.pair == CurrencyPair.USDJPY
    assert rec.realized_direction == ForecastDirection.up


def test_outcome_record_does_not_have_realized_state_proxy() -> None:
    rec = _outcome()
    assert not hasattr(rec, "realized_state_proxy")


def test_outcome_record_does_not_have_actual_state_change() -> None:
    rec = _outcome()
    assert not hasattr(rec, "actual_state_change")


def test_outcome_record_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        _outcome(realized_state_proxy="fire")  # type: ignore[call-arg]


def test_outcome_record_extra_state_field_rejected() -> None:
    with pytest.raises(ValidationError):
        _outcome(actual_state_change=True)  # type: ignore[call-arg]


@pytest.mark.parametrize("bad_value", [float("inf"), float("-inf"), float("nan")])
def test_outcome_record_non_finite_price_raises(bad_value: float) -> None:
    with pytest.raises(ValidationError, match="finite"):
        _outcome(realized_close=bad_value)


@pytest.mark.parametrize("field", ["realized_open", "realized_high", "realized_low", "realized_close"])
def test_outcome_record_negative_price_raises(field: str) -> None:
    with pytest.raises(ValidationError, match="positive"):
        _outcome(**{field: -1.0})


def test_outcome_record_zero_price_raises() -> None:
    with pytest.raises(ValidationError, match="positive"):
        _outcome(realized_close=0.0)


def test_outcome_record_high_lt_low_raises() -> None:
    with pytest.raises(ValidationError, match="realized_high must be >= realized_low"):
        _outcome(realized_high=148.0, realized_low=151.0)


def test_outcome_record_open_above_high_raises() -> None:
    with pytest.raises(ValidationError, match="realized_open must be within"):
        _outcome(realized_open=152.0, realized_high=150.8, realized_low=149.2, realized_close=150.0)


def test_outcome_record_close_below_low_raises() -> None:
    with pytest.raises(ValidationError, match="realized_close must be within"):
        _outcome(realized_open=150.0, realized_high=150.8, realized_low=149.2, realized_close=148.0)


def test_outcome_record_event_tags() -> None:
    rec = _outcome(event_happened=True, event_tags=(EventTag.fomc, EventTag.us_holiday))
    assert EventTag.fomc in rec.event_tags


# ---------------------------------------------------------------------------
# EvaluationRecord tests
# ---------------------------------------------------------------------------


def test_evaluation_record_valid() -> None:
    rec = _evaluation()
    assert rec.direction_hit is True
    assert rec.range_hit is None


def test_evaluation_record_has_realized_state_proxy() -> None:
    rec = _evaluation(realized_state_proxy="fire")
    assert rec.realized_state_proxy == "fire"


def test_evaluation_record_has_actual_state_change() -> None:
    rec = _evaluation(actual_state_change=True)
    assert rec.actual_state_change is True


def test_evaluation_record_no_aggregated_metrics() -> None:
    rec = _evaluation()
    for field_name in ("mae", "rmse", "mase", "smape"):
        assert not hasattr(rec, field_name)


def test_evaluation_record_disconfirmers_hit_empty() -> None:
    rec = _evaluation()
    assert rec.disconfirmers_hit == ()


def test_evaluation_record_disconfirmers_hit_with_ids() -> None:
    rec = _evaluation(disconfirmers_hit=("dc_01", "dc_02"), disconfirmer_explained=True)
    assert "dc_01" in rec.disconfirmers_hit
    assert rec.disconfirmer_explained is True


def test_evaluation_record_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        _evaluation(mae=0.5)  # type: ignore[call-arg]


def test_evaluation_record_range_hit_true() -> None:
    rec = _evaluation(range_hit=True, close_error_bp=10.0)
    assert rec.range_hit is True
    assert rec.close_error_bp == 10.0
