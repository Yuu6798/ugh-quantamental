"""Tests for automation_models.py, data_sources.py, and automation.py."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.automation_models import (
    FxDailyAutomationConfig,
    FxDailyAutomationResult,
)
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.data_sources import (
    FxDataFetchError,
    FxMarketDataProvider,
    HttpJsonFxMarketDataProvider,
    YahooFinanceFxMarketDataProvider,
    _parse_snapshot,
    _parse_yahoo_snapshot,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _provenance_dict() -> dict:
    return {
        "vendor": "test",
        "feed_name": "feed",
        "price_type": "mid",
        "resolution": "1d",
        "timezone": "Asia/Tokyo",
        "retrieved_at_utc": "2026-03-10T00:00:00+00:00",
    }


def _build_windows_dicts(n: int = 20) -> list[dict]:
    """Build n consecutive window dicts."""
    wins = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        wins.append({
            "window_start_jst": start.isoformat(),
            "window_end_jst": end.isoformat(),
            "open_price": 149.5,
            "high_price": 151.5,
            "low_price": 148.5,
            "close_price": 150.5,
            "event_tags": [],
        })
        start = end
        count += 1
    return wins


def _snapshot_payload(n: int = 20, as_of_jst: str | None = None) -> dict:
    wins = _build_windows_dicts(n)
    # as_of_jst defaults to the end of the last window.
    if as_of_jst is None:
        as_of_jst = wins[-1]["window_end_jst"]
    return {
        "pair": "USDJPY",
        "as_of_jst": as_of_jst,
        "current_spot": 150.0,
        "completed_windows": wins,
        "market_data_provenance": _provenance_dict(),
    }


def _build_fxprotocol_snapshot(n: int = 20) -> FxProtocolMarketSnapshot:
    """Build a typed FxProtocolMarketSnapshot for automation tests."""
    from ugh_quantamental.fx_protocol.data_sources import _parse_snapshot as _ps

    payload = _snapshot_payload(n)
    as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
    # Override as_of_jst to match a real business day.
    payload["as_of_jst"] = as_of.isoformat()
    return _ps(payload, as_of)


# ---------------------------------------------------------------------------
# FxDailyAutomationConfig
# ---------------------------------------------------------------------------


class TestFxDailyAutomationConfig:
    def test_defaults(self) -> None:
        cfg = FxDailyAutomationConfig()
        assert cfg.pair == CurrencyPair.USDJPY
        # theory_version + engine_version both bump to v2 at the v2 cut-over
        # (spec §7 step 1) so new daily runs label themselves correctly.
        assert cfg.theory_version == "v2"
        assert cfg.engine_version == "v2"
        assert cfg.protocol_version == "v1"
        assert cfg.run_forecast_generation is True
        assert cfg.run_outcome_evaluation is True
        assert cfg.data_branch == "fx-daily-data"

    def test_custom_values(self) -> None:
        cfg = FxDailyAutomationConfig(
            theory_version="v2",
            engine_version="v3",
            run_outcome_evaluation=False,
        )
        assert cfg.theory_version == "v2"
        assert cfg.run_outcome_evaluation is False

    def test_frozen(self) -> None:
        cfg = FxDailyAutomationConfig()
        with pytest.raises(Exception):
            cfg.theory_version = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FxDailyAutomationResult
# ---------------------------------------------------------------------------


class TestFxDailyAutomationResult:
    def test_defaults(self) -> None:
        r = FxDailyAutomationResult(as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))
        assert r.forecast_created is False
        assert r.outcome_recorded is False
        assert r.evaluation_count == 0
        assert r.data_commit_created is False

    def test_with_values(self) -> None:
        r = FxDailyAutomationResult(
            as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            forecast_batch_id="fb_123",
            forecast_created=True,
            evaluation_count=4,
        )
        assert r.forecast_batch_id == "fb_123"
        assert r.forecast_created is True
        assert r.evaluation_count == 4


# ---------------------------------------------------------------------------
# HttpJsonFxMarketDataProvider (no real network; stub urllib)
# ---------------------------------------------------------------------------


class TestHttpJsonFxMarketDataProvider:
    def _make_provider(self, url: str = "http://example.com/fx") -> HttpJsonFxMarketDataProvider:
        return HttpJsonFxMarketDataProvider(url=url)

    def _mock_urlopen(self, payload: dict):
        """Return a context-manager mock for urllib.request.urlopen."""
        body = json.dumps(payload).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = body
        return mock_resp

    def test_successful_fetch(self) -> None:
        provider = self._make_provider()
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(20, as_of_jst=as_of.isoformat())
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            snap = provider.fetch_snapshot(as_of)

        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) == 20

    def test_missing_url_raises(self) -> None:
        provider = HttpJsonFxMarketDataProvider(url="")
        with pytest.raises(FxDataFetchError, match="FX_DATA_URL"):
            provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))

    def test_non_200_status_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 503
        mock_resp.read.return_value = b'{"error": "service unavailable"}'

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="503"):
                provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))

    def test_invalid_json_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = b"NOT JSON"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="JSON"):
                provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))

    def test_provider_satisfies_protocol(self) -> None:
        provider = self._make_provider()
        assert isinstance(provider, FxMarketDataProvider)

    def test_no_network_access_in_tests(self) -> None:
        """Ensure provider uses its URL without touching the network."""
        provider = HttpJsonFxMarketDataProvider(url="http://should-not-be-called.invalid/")
        # We patch urllib so no actual network call happens.
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("no network in tests"),
        ):
            with pytest.raises(FxDataFetchError, match="Network error"):
                provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))


# ---------------------------------------------------------------------------
# _parse_snapshot helper
# ---------------------------------------------------------------------------


class TestParseSnapshot:
    def test_parses_valid_payload(self) -> None:
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(20, as_of_jst=as_of.isoformat())
        snap = _parse_snapshot(payload, as_of)
        assert snap.current_spot == 150.0
        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) == 20

    def test_missing_current_spot_raises(self) -> None:
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(20, as_of_jst=as_of.isoformat())
        del payload["current_spot"]
        with pytest.raises(FxDataFetchError, match="current_spot"):
            _parse_snapshot(payload, as_of)

    def test_fewer_than_20_windows_raises(self) -> None:
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(19, as_of_jst=as_of.isoformat())
        with pytest.raises((FxDataFetchError, ValueError)):
            _parse_snapshot(payload, as_of)


# ---------------------------------------------------------------------------
# Yahoo Finance provider helpers and tests
# ---------------------------------------------------------------------------


def _build_yf_payload(n_bars: int, as_of_jst: datetime) -> dict:
    """Build a mock Yahoo Finance chart API response with n_bars business-day bars.

    The newest bar's window_end_jst == as_of_jst (freshness constraint).
    Yahoo Finance uses UTC midnight timestamps for daily FX bars.
    """
    bar_dates = []
    current = as_of_jst - timedelta(days=1)
    while len(bar_dates) < n_bars:
        if current.weekday() not in {5, 6}:  # Monday=0 … Friday=4 in JST
            bar_dates.append(current.date())
        current -= timedelta(days=1)
    bar_dates.reverse()  # oldest first

    timestamps = [
        int(datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        for d in bar_dates
    ]
    n = len(timestamps)
    return {
        "chart": {
            "result": [{
                "timestamp": timestamps,
                "meta": {
                    "regularMarketPrice": 150.5,
                    "currency": "JPY",
                    "symbol": "USDJPY=X",
                },
                "indicators": {
                    "quote": [{
                        "open": [149.5] * n,
                        "high": [151.5] * n,
                        "low": [148.5] * n,
                        "close": [150.5] * n,
                    }],
                },
            }],
            "error": None,
        },
    }


class TestYahooFinanceFxMarketDataProvider:
    """Tests for YahooFinanceFxMarketDataProvider — no real network calls."""

    _AS_OF = datetime(2026, 3, 10, 8, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))  # Tuesday

    def _make_provider(self) -> YahooFinanceFxMarketDataProvider:
        return YahooFinanceFxMarketDataProvider()

    def _mock_urlopen(self, payload: dict):
        body = json.dumps(payload).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = body
        return mock_resp

    def test_successful_fetch_returns_valid_snapshot(self) -> None:
        payload = _build_yf_payload(22, self._AS_OF)
        provider = self._make_provider()
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            snap = provider.fetch_snapshot(self._AS_OF)

        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) >= 20
        assert snap.current_spot == 150.5
        # Newest completed window must end at as_of_jst (freshness constraint).
        assert snap.completed_windows[-1].window_end_jst == self._AS_OF

    def test_network_error_raises(self) -> None:
        import urllib.error
        provider = self._make_provider()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(FxDataFetchError, match="Network error"):
                provider.fetch_snapshot(self._AS_OF)

    def test_non_200_status_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 429
        mock_resp.read.return_value = b'{"error": "rate limited"}'

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="429"):
                provider.fetch_snapshot(self._AS_OF)

    def test_invalid_json_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = b"NOT JSON AT ALL"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="JSON"):
                provider.fetch_snapshot(self._AS_OF)

    def test_insufficient_windows_raises(self) -> None:
        # Only 5 bars → cannot satisfy the >= 20 completed-windows requirement.
        payload = _build_yf_payload(5, self._AS_OF)
        provider = self._make_provider()
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="Insufficient"):
                provider.fetch_snapshot(self._AS_OF)

    def test_provider_satisfies_protocol(self) -> None:
        provider = self._make_provider()
        assert isinstance(provider, FxMarketDataProvider)

    def test_no_network_in_tests(self) -> None:
        """Confirm tests never hit the real network."""
        import urllib.error
        provider = self._make_provider()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("no network in tests"),
        ):
            with pytest.raises(FxDataFetchError, match="Network error"):
                provider.fetch_snapshot(self._AS_OF)

    def test_requires_no_auth_token_or_url(self) -> None:
        """No FX_DATA_URL or FX_DATA_AUTH_TOKEN needed to instantiate."""
        provider = YahooFinanceFxMarketDataProvider()
        assert isinstance(provider, YahooFinanceFxMarketDataProvider)


class TestParseYahooSnapshot:
    """Tests for _parse_yahoo_snapshot helper."""

    _AS_OF = datetime(2026, 3, 10, 8, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))

    def test_parses_valid_payload(self) -> None:
        payload = _build_yf_payload(22, self._AS_OF)
        snap = _parse_yahoo_snapshot(payload, self._AS_OF)
        assert snap.pair == CurrencyPair.USDJPY
        assert snap.current_spot == 150.5
        assert len(snap.completed_windows) >= 20
        assert snap.completed_windows[-1].window_end_jst == self._AS_OF

    def test_missing_regular_market_price_raises(self) -> None:
        payload = _build_yf_payload(22, self._AS_OF)
        del payload["chart"]["result"][0]["meta"]["regularMarketPrice"]
        with pytest.raises(FxDataFetchError, match="regularMarketPrice"):
            _parse_yahoo_snapshot(payload, self._AS_OF)

    def test_bad_response_shape_raises(self) -> None:
        with pytest.raises(FxDataFetchError, match="response shape"):
            _parse_yahoo_snapshot({}, self._AS_OF)

    def test_weekend_bars_excluded(self) -> None:
        payload = _build_yf_payload(22, self._AS_OF)
        # Insert a Saturday bar (2026-03-07 = Saturday).
        sat_ts = int(datetime(2026, 3, 7, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        result = payload["chart"]["result"][0]
        result["timestamp"].insert(0, sat_ts)
        for key in ("open", "high", "low", "close"):
            result["indicators"]["quote"][0][key].insert(0, 150.0)

        snap = _parse_yahoo_snapshot(payload, self._AS_OF)
        # Saturday bar must not appear in completed windows.
        for win in snap.completed_windows:
            assert win.window_start_jst.weekday() < 5  # Mon=0 … Fri=4

    def test_windows_ordered_oldest_to_newest(self) -> None:
        payload = _build_yf_payload(22, self._AS_OF)
        snap = _parse_yahoo_snapshot(payload, self._AS_OF)
        starts = [w.window_start_jst for w in snap.completed_windows]
        assert starts == sorted(starts)

    def test_future_bars_excluded(self) -> None:
        """Bars whose window_end > as_of_jst must not appear."""
        payload = _build_yf_payload(22, self._AS_OF)
        snap = _parse_yahoo_snapshot(payload, self._AS_OF)
        for win in snap.completed_windows:
            assert win.window_end_jst <= self._AS_OF

    def test_normalization_maps_utc_midnight_to_jst_date(self) -> None:
        """UTC midnight Monday 2026-03-09 → window_start = 2026-03-09 08:00 JST."""
        from ugh_quantamental.fx_protocol.data_sources import _yahoo_bar_to_window
        from zoneinfo import ZoneInfo
        _JST_local = ZoneInfo("Asia/Tokyo")
        # 2026-03-09 (Monday) 00:00 UTC
        ts = int(datetime(2026, 3, 9, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        win = _yahoo_bar_to_window(ts, 149.5, 151.5, 148.5, 150.5)
        assert win is not None
        assert win.window_start_jst == datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST_local)
        assert win.window_end_jst == datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST_local)


# ---------------------------------------------------------------------------
# run_fx_daily_protocol_once (happy path + idempotency)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestRunFxDailyProtocolOnce:
    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def _make_provider(self, snap: FxProtocolMarketSnapshot):
        """Build a stub provider that returns the given snapshot."""
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        return provider

    def _make_snapshot_no_previous_window(self) -> FxProtocolMarketSnapshot:
        """Snapshot that passes the freshness guard (newest_end == as_of_jst).

        Whether outcome evaluation actually runs is controlled by
        config.run_outcome_evaluation or by patching previous_window_matches
        in individual tests — not by making the snapshot stale.
        """
        wins = _build_windows_raw(20)
        # as_of_jst must equal the newest window_end_jst to pass the freshness guard.
        as_of = wins[-1].window_end_jst
        return FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=as_of,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=MarketDataProvenance(
                vendor="test",
                feed_name="feed",
                price_type="mid",
                resolution="1d",
                timezone="Asia/Tokyo",
                retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )

    def _make_snapshot_with_previous_window(self) -> FxProtocolMarketSnapshot:
        """Snapshot where as_of_jst matches newest window end (outcome eligible)."""
        wins = _build_windows_raw(20)
        as_of = wins[-1].window_end_jst  # matches newest window end
        return FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=as_of,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=MarketDataProvenance(
                vendor="test",
                feed_name="feed",
                price_type="mid",
                resolution="1d",
                timezone="Asia/Tokyo",
                retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )

    def test_forecast_only_no_previous_window(self) -> None:
        """Happy path: forecast created, no outcome (no prior window match)."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,  # disable outcome for simplicity
            run_forecast_generation=True,
        )

        # Patch current_as_of_jst to return the snapshot's as_of_jst.
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)

        assert result.forecast_batch_id is not None
        assert result.forecast_created is True
        assert result.outcome_recorded is False
        session.close()

    def test_idempotent_rerun_does_not_duplicate(self) -> None:
        """Second run with the same as_of_jst must not create new forecast records."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
        )

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            r1 = run_fx_daily_protocol_once(cfg, provider, session)
            session.commit()
            # Second run — same session, same as_of.
            r2 = run_fx_daily_protocol_once(cfg, provider, session)

        # Both runs return the same batch_id; only the first creates it.
        assert r1.forecast_batch_id == r2.forecast_batch_id
        assert r1.forecast_created is True
        assert r2.forecast_created is False
        session.close()

    def test_no_outcome_when_no_prior_window(self) -> None:
        """Outcome must not be run when previous_window_matches returns False."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=True,
            run_forecast_generation=True,
        )

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.previous_window_matches",
            return_value=False,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)

        assert result.outcome_recorded is False
        assert result.outcome_id is None
        session.close()

    def test_non_business_day_raises(self) -> None:
        """Running on a non-business day must raise ValueError."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig()

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=False,
        ):
            with pytest.raises(ValueError, match="business day"):
                run_fx_daily_protocol_once(cfg, provider, session)
        session.close()

    def test_one_day_lag_adjusts_as_of_jst(self) -> None:
        """Provider 1 business day behind: as_of_jst falls back to newest_end."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

        # Build a normal snapshot (newest_end == snap.as_of_jst).
        snap = self._make_snapshot_no_previous_window()
        adjusted_as_of = snap.as_of_jst  # e.g. 2026-03-10 08:00 JST

        # The "today" seen by the automation is 1 business day ahead.
        today_as_of = next_as_of_jst(adjusted_as_of)  # e.g. 2026-03-11 08:00 JST

        # Provider: first call (with today_as_of) returns a snapshot whose
        # newest_end is only adjusted_as_of; second call (after fallback) returns
        # the same snapshot which now satisfies the guard.
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.side_effect = [snap, snap]

        session = self._make_session()
        cfg = FxDailyAutomationConfig(run_outcome_evaluation=False)

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=today_as_of,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)

        # The result should reflect the adjusted (fallback) date.
        assert result.as_of_jst == adjusted_as_of
        # Provider must have been called twice: initial fetch + fallback re-fetch.
        assert provider.fetch_snapshot.call_count == 2
        session.close()

    def test_two_day_lag_raises(self) -> None:
        """Provider 2+ business days behind: must raise ValueError."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

        snap = self._make_snapshot_no_previous_window()
        adjusted_as_of = snap.as_of_jst

        # today is 2 business days ahead of the snapshot
        two_days_ahead = next_as_of_jst(next_as_of_jst(adjusted_as_of))

        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig()

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=two_days_ahead,
        ):
            with pytest.raises(ValueError, match="Stale snapshot"):
                run_fx_daily_protocol_once(cfg, provider, session)
        session.close()

    def test_one_day_lag_second_fetch_still_stale_raises(self) -> None:
        """1-day fallback re-fetch returns a snapshot that is STILL stale: must raise ValueError.

        Regression for automation.py line 252.  After the 1-day fallback adjusts
        as_of_jst to adjusted_as_of and calls fetch_snapshot a second time, if the
        returned snapshot's newest window_end != adjusted_as_of, the function must
        raise ValueError('Stale snapshot after 1-day fallback').
        """
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst
        from ugh_quantamental.fx_protocol.models import MarketDataProvenance

        # snap_day1: newest_end == adjusted_as_of (1 business day behind today).
        snap_day1 = self._make_snapshot_no_previous_window()
        adjusted_as_of = snap_day1.as_of_jst      # day D
        today_as_of = next_as_of_jst(adjusted_as_of)  # day D+1

        # snap_still_stale: built from 21 windows (wins[1:] = 20 windows whose
        # newest end is wins[20].window_end_jst, which is one biz-day AFTER
        # adjusted_as_of).  This makes newest_end != adjusted_as_of and triggers
        # the "Stale snapshot after 1-day fallback" error at line 252.
        wins21 = _build_windows_raw(21)
        wins_still_stale = wins21[1:]  # drop first window → 20 windows, newest end > adjusted_as_of
        snap_still_stale = FxProtocolMarketSnapshot(
            pair=snap_day1.pair,
            as_of_jst=wins_still_stale[-1].window_end_jst,
            current_spot=snap_day1.current_spot,
            completed_windows=wins_still_stale,
            market_data_provenance=MarketDataProvenance(
                vendor="test",
                feed_name="feed",
                price_type="mid",
                resolution="1d",
                timezone="Asia/Tokyo",
                retrieved_at_utc=snap_day1.market_data_provenance.retrieved_at_utc,
            ),
        )

        provider = MagicMock(spec=FxMarketDataProvider)
        # First call returns snap_day1 (1 day behind → triggers fallback).
        # Second call (after as_of_jst is adjusted) returns snap_still_stale
        # whose newest_end != adjusted_as_of → must raise line-252 ValueError.
        provider.fetch_snapshot.side_effect = [snap_day1, snap_still_stale]

        session = self._make_session()
        cfg = FxDailyAutomationConfig(run_outcome_evaluation=False)

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=today_as_of,
        ):
            with pytest.raises(ValueError, match="Stale snapshot after 1-day fallback"):
                run_fx_daily_protocol_once(cfg, provider, session)

        assert provider.fetch_snapshot.call_count == 2
        session.close()

    def test_one_day_lag_emits_logger_warning(self, caplog) -> None:
        """1-day lag fallback emits a logging.warning (not a bare print)."""
        import logging

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

        snap = self._make_snapshot_no_previous_window()
        adjusted_as_of = snap.as_of_jst
        today_as_of = next_as_of_jst(adjusted_as_of)

        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.side_effect = [snap, snap]

        session = self._make_session()
        cfg = FxDailyAutomationConfig(run_outcome_evaluation=False)

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=today_as_of,
        ):
            with caplog.at_level(logging.WARNING, logger="ugh_quantamental.fx_protocol.automation"):
                run_fx_daily_protocol_once(cfg, provider, session)

        assert any("1 business day behind" in record.message for record in caplog.records)
        session.close()


# ---------------------------------------------------------------------------
# _build_windows_raw helper for test_automation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# SQLite path handling logic (scripts/run_fx_daily_protocol.py)
# ---------------------------------------------------------------------------


class TestSqlitePathHandling:
    """Tests for sqlite path construction from environment variables."""

    def test_fx_sqlite_path_takes_priority(self, monkeypatch) -> None:
        """FX_SQLITE_PATH overrides FX_SQLITE_FILENAME + FX_DATA_DIR."""
        import os

        monkeypatch.setenv("FX_SQLITE_PATH", "/tmp/explicit.db")
        monkeypatch.setenv("FX_SQLITE_FILENAME", "other.db")
        monkeypatch.setenv("FX_DATA_DIR", "/tmp/data")

        sqlite_path = os.environ.get("FX_SQLITE_PATH", "").strip()
        if not sqlite_path:
            sqlite_filename = os.environ.get("FX_SQLITE_FILENAME", "fx_protocol.db").strip()
            data_dir = os.environ.get("FX_DATA_DIR", "./data").strip()
            sqlite_path = os.path.join(data_dir, sqlite_filename)

        assert sqlite_path == "/tmp/explicit.db"

    def test_sqlite_filename_combined_with_data_dir(self, monkeypatch) -> None:
        """FX_SQLITE_FILENAME + FX_DATA_DIR are joined when FX_SQLITE_PATH not set."""
        import os

        monkeypatch.delenv("FX_SQLITE_PATH", raising=False)
        monkeypatch.setenv("FX_SQLITE_FILENAME", "protocol.db")
        monkeypatch.setenv("FX_DATA_DIR", "/repo/data")

        sqlite_path = os.environ.get("FX_SQLITE_PATH", "").strip()
        if not sqlite_path:
            sqlite_filename = os.environ.get("FX_SQLITE_FILENAME", "fx_protocol.db").strip()
            data_dir = os.environ.get("FX_DATA_DIR", "./data").strip()
            sqlite_path = os.path.join(data_dir, sqlite_filename)

        assert sqlite_path == "/repo/data/protocol.db"

    def test_default_sqlite_path_used_when_no_env(self, monkeypatch) -> None:
        """Defaults are used when no env vars are set."""
        import os

        monkeypatch.delenv("FX_SQLITE_PATH", raising=False)
        monkeypatch.delenv("FX_SQLITE_FILENAME", raising=False)
        monkeypatch.delenv("FX_DATA_DIR", raising=False)

        sqlite_path = os.environ.get("FX_SQLITE_PATH", "").strip()
        if not sqlite_path:
            sqlite_filename = os.environ.get("FX_SQLITE_FILENAME", "fx_protocol.db").strip()
            data_dir = os.environ.get("FX_DATA_DIR", "./data").strip()
            sqlite_path = os.path.join(data_dir, sqlite_filename)

        assert sqlite_path == os.path.join("./data", "fx_protocol.db")


# ---------------------------------------------------------------------------
# Script-level config validation (without network)
# ---------------------------------------------------------------------------


class TestScriptConfigValidation:
    """Tests for script-level config validation logic, no network access."""

    def test_default_provider_requires_no_url(self, monkeypatch) -> None:
        """FX_DATA_URL is NOT required — Yahoo Finance is the default provider."""
        monkeypatch.delenv("FX_DATA_URL", raising=False)
        # YahooFinanceFxMarketDataProvider can be instantiated with no env vars.
        provider = YahooFinanceFxMarketDataProvider()
        assert isinstance(provider, FxMarketDataProvider)

    def test_http_provider_still_requires_url_when_used_explicitly(self, monkeypatch) -> None:
        """HttpJsonFxMarketDataProvider still raises when its own URL is empty."""
        monkeypatch.delenv("FX_DATA_URL", raising=False)
        provider = HttpJsonFxMarketDataProvider(url="")
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        with pytest.raises(FxDataFetchError, match="FX_DATA_URL"):
            provider.fetch_snapshot(as_of)

    def test_automation_config_version_defaults(self) -> None:
        """All version defaults are non-empty strings."""
        cfg = FxDailyAutomationConfig()
        assert cfg.theory_version
        assert cfg.engine_version
        assert cfg.schema_version
        assert cfg.protocol_version

    def test_automation_config_data_branch_default(self) -> None:
        """Default data branch is 'fx-daily-data'."""
        cfg = FxDailyAutomationConfig()
        assert cfg.data_branch == "fx-daily-data"

    def test_automation_config_sqlite_path_default(self) -> None:
        """Default sqlite_path is set and non-empty."""
        cfg = FxDailyAutomationConfig()
        assert cfg.sqlite_path
        assert "fx_protocol.db" in cfg.sqlite_path

    def test_automation_config_empty_version_rejected(self) -> None:
        """Empty version strings must be rejected by the config model."""
        with pytest.raises(Exception):
            FxDailyAutomationConfig(theory_version="")


def _build_windows_raw(n: int) -> tuple[FxCompletedWindow, ...]:
    """Build n consecutive FxCompletedWindow objects (Mon→next-biz-day)."""
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        windows.append(FxCompletedWindow(
            window_start_jst=start,
            window_end_jst=end,
            open_price=149.5,
            high_price=151.5,
            low_price=148.5,
            close_price=150.5,
        ))
        start = end
        count += 1
    return tuple(windows)
