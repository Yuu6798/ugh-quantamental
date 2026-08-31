"""Regression test for the ``input_snapshot.json`` idempotent-retry invariant.

``scripts/run_fx_price_alert.py`` (FX-PRICE-ALERT) uses the last forecast
batch's ``input_snapshot.json`` ``current_spot`` as its move-alert baseline,
specifically *because* that file is documented (``automation.py`` step 7a)
to preserve the forecast-time spot across idempotent retries rather than
being rebuilt from whatever the market looks like at retry time. This test
pins that invariant: it fetches market data via a stub provider whose
``current_spot`` differs between the initial forecast run and a same-batch
idempotent retry, then asserts the persisted ``input_snapshot.json`` still
reports the *first* run's spot after the retry.

This is the only place FX-PRICE-ALERT's test suite touches ``fx_protocol`` —
the alert script itself stays import-free (see ``tests/ops/`` and
``docs/specs/fx_price_alert_v1.md``).
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
from ugh_quantamental.fx_protocol.data_models import FxCompletedWindow, FxProtocolMarketSnapshot
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc


def _build_windows(n: int) -> tuple[FxCompletedWindow, ...]:
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        windows.append(
            FxCompletedWindow(
                window_start_jst=start,
                window_end_jst=end,
                open_price=149.5,
                high_price=151.5,
                low_price=148.5,
                close_price=150.5,
            )
        )
        start = end
        count += 1
    return tuple(windows)


def _make_snapshot(current_spot: float) -> FxProtocolMarketSnapshot:
    wins = _build_windows(20)
    as_of = wins[-1].window_end_jst
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of,
        current_spot=current_spot,
        completed_windows=wins,
        market_data_provenance=MarketDataProvenance(
            vendor="test",
            feed_name="feed",
            price_type="mid",
            resolution="1d",
            timezone="Asia/Tokyo",
            retrieved_at_utc=datetime(2026, 3, 14, 0, 0, 0, tzinfo=_UTC),
        ),
    )


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestInputSnapshotIdempotentRetryInvariant:
    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def test_retry_spot_change_does_not_overwrite_persisted_input_snapshot(self) -> None:
        """AC (a) precondition: an idempotent retry with a *different* live
        spot than the original forecast run must not change the persisted
        ``input_snapshot.json`` ``current_spot`` — it must stay pinned to
        the spot the engine actually saw when the forecast was generated."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        original_snap = _make_snapshot(current_spot=150.000)
        retry_snap = _make_snapshot(current_spot=155.500)  # market moved before the retry
        assert original_snap.as_of_jst == retry_snap.as_of_jst  # same batch/day

        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.side_effect = [original_snap, retry_snap]
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with (
                patch(
                    "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                    return_value=original_snap.as_of_jst,
                ),
                patch(
                    "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                    return_value=True,
                ),
            ):
                r1 = run_fx_daily_protocol_once(cfg, provider, session)
                session.commit()
                # Idempotent retry: same as_of/batch, but the provider now
                # returns a different current_spot (market moved).
                r2 = run_fx_daily_protocol_once(cfg, provider, session)

            assert r1.forecast_created is True
            assert r2.forecast_created is False
            assert r1.forecast_batch_id == r2.forecast_batch_id

            assert r1.input_snapshot_path is not None
            assert r2.input_snapshot_path is not None

            with open(r1.input_snapshot_path, encoding="utf-8") as fh:
                snap1_data = json.load(fh)
            with open(r2.input_snapshot_path, encoding="utf-8") as fh:
                snap2_data = json.load(fh)

            assert snap1_data["current_spot"] == pytest.approx(150.000)
            # The invariant under test: the retry must NOT have rebuilt the
            # artifact from the retry-time snapshot's spot (155.500).
            assert snap2_data["current_spot"] == pytest.approx(150.000)
            assert snap2_data["current_spot"] == snap1_data["current_spot"]

        session.close()
