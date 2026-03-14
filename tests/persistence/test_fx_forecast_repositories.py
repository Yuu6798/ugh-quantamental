"""Tests for FX forecast persistence repositories."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone

import pytest

from ugh_quantamental.fx_protocol.ids import make_forecast_batch_id, make_forecast_id
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    ForecastDirection,
    ForecastRecord,
    MarketDataProvenance,
    StrategyKind,
)

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


def _forecast(strategy_kind: StrategyKind) -> ForecastRecord:
    as_of = datetime(2026, 3, 13, 8, 0, 0)
    return ForecastRecord(
        forecast_id=make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", strategy_kind),
        forecast_batch_id=make_forecast_batch_id(CurrencyPair.USDJPY, as_of, "v1"),
        pair=CurrencyPair.USDJPY,
        strategy_kind=strategy_kind,
        as_of_jst=as_of,
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        locked_at_utc=datetime(2026, 3, 12, 22, 59, 59, tzinfo=timezone.utc),
        market_data_provenance=MarketDataProvenance(
            vendor="test_vendor",
            feed_name="test_feed",
            price_type="mid",
            resolution="1d",
            timezone="Asia/Tokyo",
            retrieved_at_utc=datetime(2026, 3, 12, 0, 0, 0, tzinfo=timezone.utc),
        ),
        forecast_direction=ForecastDirection.flat,
        expected_close_change_bp=0.0,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


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
def test_fx_forecast_batch_round_trip(db_session) -> None:
    forecasts = (
        _forecast(StrategyKind.baseline_random_walk),
        _forecast(StrategyKind.baseline_prev_day_direction),
    )
    batch_id = forecasts[0].forecast_batch_id

    from ugh_quantamental.persistence.repositories import FxForecastRepository

    saved = FxForecastRepository.save_fx_forecast_batch(
        db_session,
        forecast_batch_id=batch_id,
        forecasts=forecasts,
    )
    loaded = FxForecastRepository.load_fx_forecast_batch(db_session, batch_id)

    assert saved.forecast_batch_id == batch_id
    assert loaded is not None
    assert len(loaded.forecasts) == 2
    assert {f.forecast_id for f in loaded.forecasts} == {f.forecast_id for f in forecasts}


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_forecast_id_generation_unique_per_strategy() -> None:
    as_of = datetime(2026, 3, 13, 8, 0, 0)
    ids = {
        make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", StrategyKind.ugh),
        make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", StrategyKind.baseline_random_walk),
        make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", StrategyKind.baseline_prev_day_direction),
        make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", StrategyKind.baseline_simple_technical),
    }
    assert len(ids) == 4
