"""Tests for DailyOutcomeWorkflowRequest and PersistedOutcomeEvaluationBatch models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EvaluationRecord,
    EventTag,
    ForecastDirection,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.outcome_models import (
    DailyOutcomeWorkflowRequest,
    PersistedOutcomeEvaluationBatch,
)

_JST = "Asia/Tokyo"


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="test_feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 13, 23, 0, 0, tzinfo=timezone.utc),
    )


def _valid_request(**kwargs) -> DailyOutcomeWorkflowRequest:
    base = dict(
        pair=CurrencyPair.USDJPY,
        window_start_jst=datetime(2026, 3, 13, 8, 0, 0),  # Friday
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),   # Monday (next bday)
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


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


def test_valid_request_constructed_cleanly() -> None:
    req = _valid_request()
    assert req.pair == CurrencyPair.USDJPY
    assert req.schema_version == "v1"
    assert req.event_tags == ()
    assert req.evaluated_at_utc is None


def test_request_with_event_tags() -> None:
    req = _valid_request(event_tags=(EventTag.fomc, EventTag.boj))
    assert EventTag.fomc in req.event_tags
    assert len(req.event_tags) == 2


def test_request_with_evaluated_at_utc() -> None:
    ts = datetime(2026, 3, 16, 9, 0, 0, tzinfo=timezone.utc)
    req = _valid_request(evaluated_at_utc=ts)
    assert req.evaluated_at_utc is not None


def test_window_start_normalized_to_jst() -> None:
    from zoneinfo import ZoneInfo
    req = _valid_request()
    assert req.window_start_jst.tzinfo == ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Window validation failures
# ---------------------------------------------------------------------------


def test_reject_non_business_day_window_start() -> None:
    """Saturday is not a business day."""
    with pytest.raises(ValidationError, match="business day"):
        _valid_request(
            window_start_jst=datetime(2026, 3, 14, 8, 0, 0),  # Saturday
            window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        )


def test_reject_wrong_window_end() -> None:
    """window_end must be the immediately-following business day 08:00."""
    with pytest.raises(ValidationError, match="next business-day"):
        _valid_request(
            window_start_jst=datetime(2026, 3, 13, 8, 0, 0),
            window_end_jst=datetime(2026, 3, 17, 8, 0, 0),  # two days later
        )


def test_reject_non_canonical_hour() -> None:
    """Window start must be exactly 08:00."""
    with pytest.raises(ValidationError, match="08:00:00"):
        _valid_request(
            window_start_jst=datetime(2026, 3, 13, 9, 0, 0),
            window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        )


def test_reject_non_business_day_window_end() -> None:
    """window_end must be on a business day."""
    with pytest.raises(ValidationError, match="business day"):
        _valid_request(
            window_start_jst=datetime(2026, 3, 13, 8, 0, 0),
            window_end_jst=datetime(2026, 3, 15, 8, 0, 0),  # Sunday
        )


# ---------------------------------------------------------------------------
# Price validation failures
# ---------------------------------------------------------------------------


def test_reject_non_finite_open() -> None:
    import math

    with pytest.raises(ValidationError, match="finite"):
        _valid_request(realized_open=math.nan)


def test_reject_non_finite_high() -> None:
    import math

    with pytest.raises(ValidationError, match="finite"):
        _valid_request(realized_high=math.inf)


def test_reject_zero_close() -> None:
    with pytest.raises(ValidationError, match="positive"):
        _valid_request(realized_close=0.0)


def test_reject_negative_low() -> None:
    with pytest.raises(ValidationError, match="positive"):
        _valid_request(realized_low=-1.0)


# ---------------------------------------------------------------------------
# PersistedOutcomeEvaluationBatch
# ---------------------------------------------------------------------------


def _make_outcome() -> OutcomeRecord:
    return OutcomeRecord(
        outcome_id="oc_test",
        pair=CurrencyPair.USDJPY,
        window_start_jst=datetime(2026, 3, 13, 8, 0, 0),
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        market_data_provenance=_provenance(),
        realized_open=150.0,
        realized_high=151.0,
        realized_low=149.5,
        realized_close=150.8,
        realized_direction=ForecastDirection.up,
        realized_close_change_bp=(150.8 - 150.0) / 150.0 * 10_000,
        realized_range_price=151.0 - 149.5,
        event_happened=False,
        event_tags=(),
        schema_version="v1",
        protocol_version="v1",
    )


def _make_eval(forecast_id: str, outcome_id: str, strategy_kind: StrategyKind) -> EvaluationRecord:
    kwargs: dict = dict(
        evaluation_id=f"ev_{forecast_id}_{outcome_id}_v1_abcd1234abcd1234",
        forecast_id=forecast_id,
        outcome_id=outcome_id,
        pair=CurrencyPair.USDJPY,
        strategy_kind=strategy_kind,
        direction_hit=True,
        close_error_bp=0.0,
        magnitude_error_bp=0.0,
        disconfirmers_hit=(),
        disconfirmer_explained=False,
        evaluated_at_utc=datetime(2026, 3, 16, 9, 0, 0, tzinfo=timezone.utc),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )
    if strategy_kind == StrategyKind.ugh:
        kwargs["range_hit"] = True
    return EvaluationRecord(**kwargs)


def test_persisted_batch_construction() -> None:
    outcome = _make_outcome()
    evals = tuple(
        _make_eval(f"fc_{i}", outcome.outcome_id, StrategyKind.baseline_random_walk)
        for i in range(4)
    )
    batch = PersistedOutcomeEvaluationBatch(outcome=outcome, evaluations=evals)
    assert batch.outcome.outcome_id == outcome.outcome_id
    assert len(batch.evaluations) == 4


def test_persisted_batch_rejects_extra_fields() -> None:
    outcome = _make_outcome()
    with pytest.raises(ValidationError):
        PersistedOutcomeEvaluationBatch(
            outcome=outcome, evaluations=(), unknown_field="bad"
        )
