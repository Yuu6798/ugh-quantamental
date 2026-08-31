"""Tests for ``labeled_observations.collect_evaluated_forecast_rows``.

Covers the dedupe-by-forecast_id fix required by the outcome catch-up
self-review findings (FIX 1 amendment): a batch's forecast.csv can now
legitimately live under two history directories — its own start-date dir
(written the day the forecast was generated) and, for a window recovered
via outcome catch-up, the recovered window's end-date dir too (republished
there so that directory is self-contained for this collector). Each
forecast must still contribute exactly one row.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.labeled_observations import (
    collect_evaluated_forecast_rows,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc


def _build_windows(n: int) -> tuple[FxCompletedWindow, ...]:
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)  # Monday
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


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 14, 0, 0, 0, tzinfo=_UTC),
    )


def _snapshot_with_n_windows(n: int) -> FxProtocolMarketSnapshot:
    wins = _build_windows(n)
    as_of = wins[-1].window_end_jst
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of,
        current_spot=150.0,
        completed_windows=wins,
        market_data_provenance=_provenance(),
    )


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestCollectEvaluatedForecastRowsOverCatchupHistory:
    """Rebuild over a real catch-up-recovered history/ tree."""

    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def _run(self, session, n_windows: int, cfg: FxDailyAutomationConfig):
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _snapshot_with_n_windows(n_windows)
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)
        return snap, result

    def test_recovered_window_forecasts_counted_exactly_once(self) -> None:
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                # Day1: forecast for D1's window (7 forecasts). This also
                # publishes that batch's own forecast.csv under its own
                # start-date directory.
                _, r1 = self._run(session, 20, cfg)
                session.commit()
                d1_batch_id = r1.forecast_batch_id

                # Day2: missing entirely (gap).

                # Day3: recovers D1's window via catch-up, republishing that
                # SAME batch's forecast.csv under the recovered window's
                # end-date directory too (FIX 1 amendment) alongside its
                # outcome.csv / evaluation.csv.
                _, r3 = self._run(session, 22, cfg)
                session.commit()
                assert len(r3.catchup_windows) == 1
                cu = r3.catchup_windows[0]
                assert cu.forecast_batch_id == d1_batch_id

                # Confirm the batch's forecast.csv really is duplicated across
                # two directories (the scenario that would double-count
                # without the dedupe fix).
                start_dir = os.path.join(
                    tmpdir, "history", cu.window_start_jst.strftime("%Y%m%d"), d1_batch_id
                )
                end_dir = os.path.join(
                    tmpdir, "history", cu.window_end_jst.strftime("%Y%m%d"), d1_batch_id
                )
                assert os.path.isfile(os.path.join(start_dir, "forecast.csv"))
                assert os.path.isfile(os.path.join(end_dir, "forecast.csv"))
                assert os.path.isfile(os.path.join(end_dir, "outcome.csv"))
                assert os.path.isfile(os.path.join(end_dir, "evaluation.csv"))
                # The evaluation lives ONLY at the end-date dir (never at the
                # start-date one, which the pre-FIX-1 collision bug would
                # have overwritten).
                assert not os.path.exists(os.path.join(start_dir, "evaluation.csv"))

                rows = collect_evaluated_forecast_rows(os.path.join(tmpdir, "history"))
                d1_rows = [r for r in rows if r.get("forecast_batch_id") == d1_batch_id]

                # Exactly one row per forecast — not two, despite forecast.csv
                # existing in both directories.
                assert len(d1_rows) == 7
                forecast_ids = [r["forecast_id"] for r in d1_rows]
                assert len(set(forecast_ids)) == 7
                # The recovered window's evaluation data is present (not
                # silently dropped) on every row.
                for row in d1_rows:
                    assert row.get("direction_hit", "") != ""
        finally:
            session.close()
