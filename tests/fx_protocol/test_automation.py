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
        wins.append(
            {
                "window_start_jst": start.isoformat(),
                "window_end_jst": end.isoformat(),
                "open_price": 149.5,
                "high_price": 151.5,
                "low_price": 148.5,
                "close_price": 150.5,
                "event_tags": [],
            }
        )
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
        # theory_version stays v2; engine_version bumps when engine output
        # semantics change, so new daily runs label themselves correctly.
        assert cfg.theory_version == "v2"
        assert cfg.engine_version == "v2.7"
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
            "result": [
                {
                    "timestamp": timestamps,
                    "meta": {
                        "regularMarketPrice": 150.5,
                        "currency": "JPY",
                        "symbol": "USDJPY=X",
                    },
                    "indicators": {
                        "quote": [
                            {
                                "open": [149.5] * n,
                                "high": [151.5] * n,
                                "low": [148.5] * n,
                                "close": [150.5] * n,
                            }
                        ],
                    },
                }
            ],
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
        with (
            patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ),
            patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ),
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

        with (
            patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ),
            patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ),
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

        with (
            patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ),
            patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ),
            patch(
                "ugh_quantamental.fx_protocol.automation.previous_window_matches",
                return_value=False,
            ),
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

        with (
            patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ),
            patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=False,
            ),
        ):
            with pytest.raises(ValueError, match="business day"):
                run_fx_daily_protocol_once(cfg, provider, session)
        session.close()

    def _make_friday_snapshot(self) -> FxProtocolMarketSnapshot:
        """Snapshot whose newest completed window ends on a Friday 08:00 JST."""
        # 24 business-day steps from 2026-01-05 (Mon) land on 2026-02-06 (Fri).
        wins = _build_windows_raw(24)
        as_of = wins[-1].window_end_jst
        assert as_of.isoweekday() == 5, "fixture must end on a Friday"
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
                retrieved_at_utc=datetime(2026, 2, 6, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )

    @pytest.mark.parametrize("days_past_friday", [1, 2])
    def test_weekend_landing_carries_over_to_complete_friday(self, days_past_friday: int) -> None:
        """A late run that crosses midnight JST continues under the Friday as_of.

        This is the path that produces the weekly report: the Friday block in
        scripts/run_fx_daily_protocol.py is gated on
        ``automation_result.as_of_jst.isoweekday() == 5``, so the carried-over run
        must report the Friday, create nothing new, and not raise.

        Both weekend days carry over, because the fallback targets the previous
        *business* day rather than the previous calendar day.
        """
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_friday_snapshot()
        friday_as_of = snap.as_of_jst
        landing_as_of = friday_as_of + timedelta(days=days_past_friday)
        assert landing_as_of.isoweekday() in (6, 7)

        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
        )

        # Friday's own attempt succeeds and persists a complete batch.
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=friday_as_of,
        ):
            friday_result = run_fx_daily_protocol_once(cfg, provider, session)
        session.commit()
        assert friday_result.forecast_created is True

        # The delayed final retry now sees the weekend.  is_protocol_business_day
        # is left unpatched: the real calendar must classify the day itself.
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=landing_as_of,
        ):
            carried = run_fx_daily_protocol_once(cfg, provider, session)

        assert carried.as_of_jst == friday_as_of
        assert carried.as_of_jst.isoweekday() == 5
        assert carried.forecast_batch_id == friday_result.forecast_batch_id
        assert carried.forecast_created is False

        # No duplicate records: the batch still holds exactly one full day.
        from ugh_quantamental.fx_protocol.models import EXPECTED_DAILY_BATCH_SIZE
        from ugh_quantamental.persistence.repositories import FxForecastRepository

        batch = FxForecastRepository.load_fx_forecast_batch(session, carried.forecast_batch_id)
        assert len(batch.forecasts) == EXPECTED_DAILY_BATCH_SIZE
        session.close()

    def test_carry_over_refuses_to_slide_back_on_a_lagging_provider(self) -> None:
        """A regressed provider must not drag a carried-over run further back.

        The carry-over only fires when the Friday batch is complete, so the
        provider did return Friday-ending data earlier.  If it now reports a
        Thursday-ending window, taking the ordinary one-day fallback would
        republish Thursday into latest/ over good artifacts and drop out of the
        Friday weekly-report gate -- a regression, not a rescue.
        """
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_friday_snapshot()
        friday_as_of = snap.as_of_jst
        saturday_as_of = friday_as_of + timedelta(days=1)

        # A snapshot one business day behind: newest window ends Thursday.
        stale_wins = _build_windows_raw(23)
        stale = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=stale_wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=stale_wins,
            market_data_provenance=snap.market_data_provenance,
        )
        assert stale.as_of_jst == friday_as_of - timedelta(days=1)

        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
        )

        # Friday's own attempt sees fresh data and persists a complete batch.
        fresh_provider = self._make_provider(snap)
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=friday_as_of,
        ):
            run_fx_daily_protocol_once(cfg, fresh_provider, session)
        session.commit()

        # The weekend retry carries over to Friday, but the provider has regressed.
        stale_provider = self._make_provider(stale)
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=saturday_as_of,
        ):
            with pytest.raises(ValueError, match="Refusing to move the as_of backwards"):
                run_fx_daily_protocol_once(cfg, stale_provider, session)
        session.close()

    def test_carry_over_is_not_recorded_as_provider_lag(self) -> None:
        """A carried-over run must not append a false lag row to provider_health.csv.

        Provider lag is measured against the as_of the provider was actually
        queried with.  The carried-over run queries the Friday and gets current
        Friday data, so lag is 0 and no fallback adjustment was used; measuring
        against wall-clock "today" would mark every rescued run as lagging and
        feed that into the weekly and monthly rollups.
        """
        import csv
        import os
        import tempfile

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_friday_snapshot()
        friday_as_of = snap.as_of_jst
        saturday_as_of = friday_as_of + timedelta(days=1)
        provider = self._make_provider(snap)
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=friday_as_of,
            ):
                run_fx_daily_protocol_once(cfg, provider, session)
            session.commit()

            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=saturday_as_of,
            ):
                carried = run_fx_daily_protocol_once(cfg, provider, session)

            assert carried.as_of_jst == friday_as_of

            with open(os.path.join(tmpdir, "provider_health.csv"), newline="") as fh:
                rows = list(csv.DictReader(fh))
            assert rows, "provider_health.csv should have at least one row"
            assert all(r["snapshot_lag_business_days"] == "0" for r in rows)
            assert all(r["used_fallback_adjustment"].lower() == "false" for r in rows)
        session.close()

    def test_weekend_landing_still_raises_without_a_complete_friday(self) -> None:
        """Without a complete previous-day batch the run must keep failing.

        A missing batch is a real outage, not a delayed retry, so the carry-over
        must not mask it.
        """
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_friday_snapshot()
        landing_as_of = snap.as_of_jst + timedelta(days=1)
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
        )

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=landing_as_of,
        ):
            with pytest.raises(ValueError, match="no complete forecast batch"):
                run_fx_daily_protocol_once(cfg, provider, session)
        session.close()

    def test_pre_fixing_landing_carries_over_to_complete_previous_day(self) -> None:
        """A run that starts before today's 08:00 JST fixing carries over.

        A delayed Mon-Thu final retry lands at 00:xx JST on the next business
        day.  When the previous business day's batch is complete the run is
        carried over to it, so the provider is queried for the day whose data
        exists and provider_health.csv records lag 0 / no fallback -- not the
        false lag=1 / fallback=True rows the ordinary one-day fallback left
        behind (17 of 59 runs in 2026-09).
        """
        import csv
        import os
        import tempfile

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

        snap = self._make_snapshot_no_previous_window()
        day_as_of = snap.as_of_jst
        # 00:30 JST on the next business day: before that day's 08:00 fixing.
        pre_fixing_now = next_as_of_jst(day_as_of) - timedelta(hours=7, minutes=30)
        provider = self._make_provider(snap)
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            # The day's own attempt (12:00 JST) persists a complete batch.
            run_fx_daily_protocol_once(
                cfg, provider, session, now_utc=day_as_of + timedelta(hours=4)
            )
            session.commit()

            carried = run_fx_daily_protocol_once(cfg, provider, session, now_utc=pre_fixing_now)

            assert carried.as_of_jst == day_as_of
            assert carried.forecast_created is False
            # The provider was asked for the carried-over day, never for "today".
            provider.fetch_snapshot.assert_called_with(day_as_of)

            with open(os.path.join(tmpdir, "provider_health.csv"), newline="") as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 2
            assert all(r["snapshot_lag_business_days"] == "0" for r in rows)
            assert all(r["used_fallback_adjustment"].lower() == "false" for r in rows)
            assert rows[-1]["run_status"] == "idempotent_skip"
        session.close()

    def test_pre_fixing_carry_over_refuses_to_slide_back(self) -> None:
        """After a pre-fixing carry-over a regressed provider must fail, not fall back."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst, prev_as_of_jst

        # 21 windows so the stale variant below still meets the 20-window minimum.
        fresh_wins = _build_windows_raw(21)
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=fresh_wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=fresh_wins,
            market_data_provenance=self._make_snapshot_no_previous_window().market_data_provenance,
        )
        day_as_of = snap.as_of_jst
        pre_fixing_now = next_as_of_jst(day_as_of) - timedelta(hours=7, minutes=30)

        # A snapshot one business day behind: newest window ends the day before.
        stale_wins = _build_windows_raw(20)
        stale = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=stale_wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=stale_wins,
            market_data_provenance=snap.market_data_provenance,
        )
        assert stale.as_of_jst == prev_as_of_jst(day_as_of)

        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
        )
        run_fx_daily_protocol_once(
            cfg, self._make_provider(snap), session, now_utc=day_as_of + timedelta(hours=4)
        )
        session.commit()

        with pytest.raises(ValueError, match="Refusing to move the as_of backwards"):
            run_fx_daily_protocol_once(
                cfg, self._make_provider(stale), session, now_utc=pre_fixing_now
            )
        session.close()

    def test_pre_fixing_without_batch_keeps_the_fallback_rescue(self) -> None:
        """No batch for the previous day: the run is not carried over.

        The ordinary one-day provider fallback then does what it always did --
        walks as_of_jst back and creates the missing forecast -- so the rescue
        path for a day whose every attempt failed is unchanged.
        """
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

        snap = self._make_snapshot_no_previous_window()
        day_as_of = snap.as_of_jst
        pre_fixing_now = next_as_of_jst(day_as_of) - timedelta(hours=7, minutes=30)

        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.side_effect = [snap, snap]
        session = self._make_session()
        cfg = FxDailyAutomationConfig(run_outcome_evaluation=False)

        result = run_fx_daily_protocol_once(cfg, provider, session, now_utc=pre_fixing_now)

        assert result.as_of_jst == day_as_of
        assert result.forecast_created is True
        # Initial fetch for "today" + the fallback re-fetch, exactly as before.
        assert provider.fetch_snapshot.call_count == 2
        session.close()

    def test_pre_fixing_with_partial_batch_still_fails_on_the_partial_guard(self) -> None:
        """A partial previous-day batch is not complete, so no carry-over happens;
        the fallback path then hits the existing partial-batch guard and fails.
        The corruption guard must not be weakened into a rescue."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst
        from ugh_quantamental.persistence.models import FxForecastRecord

        snap = self._make_snapshot_no_previous_window()
        day_as_of = snap.as_of_jst
        pre_fixing_now = next_as_of_jst(day_as_of) - timedelta(hours=7, minutes=30)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(run_outcome_evaluation=False)

        first = run_fx_daily_protocol_once(
            cfg, self._make_provider(snap), session, now_utc=day_as_of + timedelta(hours=4)
        )
        assert first.forecast_created is True
        # Drop one row: the batch now exists but is partial.
        row = (
            session.query(FxForecastRecord)
            .filter(FxForecastRecord.forecast_batch_id == first.forecast_batch_id)
            .first()
        )
        session.delete(row)
        session.commit()

        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.side_effect = [snap, snap]
        with pytest.raises(ValueError, match="partial forecast batch exists"):
            run_fx_daily_protocol_once(cfg, provider, session, now_utc=pre_fixing_now)
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
        adjusted_as_of = snap_day1.as_of_jst  # day D
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

        assert os.path.normpath(sqlite_path) == os.path.normpath("/repo/data/protocol.db")

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


# ---------------------------------------------------------------------------
# FX Execution Layer v1 — automation Steps 3b / 4c / 5b / 6b (brief FX-EXEC-LAYER)
# ---------------------------------------------------------------------------

_LIVE_SPOT_PRICE = 150.25
_LIVE_SPOT_RETRIEVED_AT = datetime(2026, 2, 2, 9, 0, 0, tzinfo=timezone.utc)
_EXECUTION_BOOK_COUNT = 6
# OHLC every ``_build_windows_raw`` window carries: the realized window closes up.
_WINDOW_OPEN = 149.5
_WINDOW_CLOSE = 150.5


class TestExecutionLayerModelFields:
    """Config / result field additions (spec §7); importable without SQLAlchemy."""

    def test_config_default_enables_the_layer(self) -> None:
        assert FxDailyAutomationConfig().run_execution_layer is True
        assert FxDailyAutomationConfig(run_execution_layer=False).run_execution_layer is False

    def test_result_defaults(self) -> None:
        result = FxDailyAutomationResult(as_of_jst=datetime(2026, 2, 2, 8, 0, 0, tzinfo=_JST))
        assert result.execution_csv_path is None
        assert result.execution_evaluation_csv_path is None
        assert result.execution_decisions_recorded == 0
        assert result.execution_evaluations_recorded == 0


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestExecutionLayerAutomation:
    """End-to-end wiring of the execution layer into ``run_fx_daily_protocol_once``.

    Day indexing follows ``_build_windows_raw``: a snapshot with ``n`` windows
    runs on business day ``bd[n]`` (``bd[0]`` = Monday 2026-01-05), so ``n=20``
    is 2026-02-02 and ``n=21`` the next business day.  ``now_utc`` is placed
    well after that day's 08:00 JST fixing, so the run clock resolves to the
    snapshot's own ``as_of_jst`` without patching the calendar.  The live spot
    is stubbed in ``automation``'s namespace by the ``live_spot`` fixture (the
    package-level autouse guard already refuses the real fetch).
    """

    _make_session = TestRunFxDailyProtocolOnce._make_session
    _make_provider = TestRunFxDailyProtocolOnce._make_provider

    @pytest.fixture
    def live_spot(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        mock = MagicMock(return_value=(_LIVE_SPOT_PRICE, _LIVE_SPOT_RETRIEVED_AT))
        monkeypatch.setattr("ugh_quantamental.fx_protocol.automation.fetch_live_spot_yahoo", mock)
        return mock

    @staticmethod
    def _snapshot_for_day(n_windows: int) -> FxProtocolMarketSnapshot:
        wins = _build_windows_raw(n_windows)
        return FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=MarketDataProvenance(
                vendor="test",
                feed_name="feed",
                price_type="mid",
                resolution="1d",
                timezone="Asia/Tokyo",
                retrieved_at_utc=datetime(2026, 2, 2, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )

    @staticmethod
    def _config(tmp_path, **overrides) -> FxDailyAutomationConfig:
        fields: dict[str, object] = {
            "run_outcome_evaluation": True,
            "run_forecast_generation": True,
            "write_csv_exports": True,
            "csv_output_dir": str(tmp_path),
        }
        fields.update(overrides)
        return FxDailyAutomationConfig(**fields)

    @staticmethod
    def _run_clock(as_of_jst: datetime, hours_after_fixing: int = 10) -> datetime:
        """Aware-UTC run clock *hours_after_fixing* hours past the day's 08:00 JST fixing."""
        return (as_of_jst + timedelta(hours=hours_after_fixing)).astimezone(timezone.utc)

    def _run(
        self,
        session,
        cfg: FxDailyAutomationConfig,
        n_windows: int,
        *,
        now_utc: datetime | None = None,
        hours_after_fixing: int = 10,
    ):
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._snapshot_for_day(n_windows)
        if now_utc is None:
            now_utc = self._run_clock(snap.as_of_jst, hours_after_fixing)
        result = run_fx_daily_protocol_once(
            cfg, self._make_provider(snap), session, now_utc=now_utc
        )
        return snap, result

    @staticmethod
    def _batch_dir(tmp_path, as_of_jst: datetime, forecast_batch_id: str):
        return tmp_path / "history" / as_of_jst.strftime("%Y%m%d") / forecast_batch_id

    # (a) ------------------------------------------------------------------
    def test_a_run_creating_the_batch_records_six_live_decisions(self, tmp_path, live_spot) -> None:
        from ugh_quantamental.fx_protocol.execution_exports import load_execution_decisions_csv
        from ugh_quantamental.fx_protocol.execution_models import EXECUTION_BOOK_ORDER

        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap, result = self._run(session, cfg, 20)

            assert result.forecast_created is True
            assert result.execution_decisions_recorded == _EXECUTION_BOOK_COUNT
            assert result.execution_csv_path == str(
                tmp_path / "execution" / "USDJPY_20260202_execution.csv"
            )
            history_file = (
                self._batch_dir(tmp_path, snap.as_of_jst, result.forecast_batch_id)
                / "execution.csv"
            )
            assert history_file.is_file()
            decisions = load_execution_decisions_csv(str(history_file))
            assert len(decisions) == _EXECUTION_BOOK_COUNT
            assert [d.book_id for d in decisions] == list(EXECUTION_BOOK_ORDER)
            for d in decisions:
                assert d.entry_status == "live"
                assert d.entry_price_live == _LIVE_SPOT_PRICE
                assert d.entry_time_utc == _LIVE_SPOT_RETRIEVED_AT
                assert d.entry_vendor == "yahoo_finance"
                assert d.entry_feed == "chart/USDJPY=X"
                assert d.forecast_batch_id == result.forecast_batch_id
                assert d.as_of_jst == snap.as_of_jst
            # latest/ mirrors the archived decisions; the batch dir is the one
            # the forecast archive uses.
            latest_file = tmp_path / "latest" / "execution.csv"
            assert latest_file.read_bytes() == history_file.read_bytes()
            assert (history_file.parent / "forecast.csv").is_file()
            live_spot.assert_called_once_with()
            # Today's window is still open: nothing to evaluate yet.
            assert result.execution_evaluations_recorded == 0
            assert result.execution_evaluation_csv_path is None
            assert not (history_file.parent / "execution_evaluation.csv").exists()
        finally:
            session.close()

    # (b) ------------------------------------------------------------------
    def test_b_same_day_rerun_keeps_archive_and_skips_live_spot(self, tmp_path, live_spot) -> None:
        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap, r1 = self._run(session, cfg, 20)
            session.commit()
            history_file = (
                self._batch_dir(tmp_path, snap.as_of_jst, r1.forecast_batch_id) / "execution.csv"
            )
            latest_file = tmp_path / "latest" / "execution.csv"
            before = history_file.read_bytes()
            before_mtime = history_file.stat().st_mtime_ns
            latest_before = latest_file.read_bytes()
            assert live_spot.call_count == 1

            _, r2 = self._run(session, cfg, 20, hours_after_fixing=12)

            assert r2.forecast_created is False
            assert r2.forecast_batch_id == r1.forecast_batch_id
            assert live_spot.call_count == 1
            assert history_file.read_bytes() == before
            assert history_file.stat().st_mtime_ns == before_mtime
            assert latest_file.read_bytes() == latest_before
            assert r2.execution_decisions_recorded == 0
            assert r2.execution_csv_path is None
        finally:
            session.close()

    # (b2) -----------------------------------------------------------------
    def test_b2_missing_archive_is_recovered_by_the_next_run(self, tmp_path, live_spot) -> None:
        from ugh_quantamental.fx_protocol.execution_exports import load_execution_decisions_csv

        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap, r1 = self._run(session, cfg, 20)
            session.commit()
            history_file = (
                self._batch_dir(tmp_path, snap.as_of_jst, r1.forecast_batch_id) / "execution.csv"
            )
            history_file.unlink()

            _, r2 = self._run(session, cfg, 20, hours_after_fixing=12)

            assert r2.forecast_created is False
            assert r2.execution_decisions_recorded == _EXECUTION_BOOK_COUNT
            assert r2.execution_csv_path is not None
            assert live_spot.call_count == 2
            decisions = load_execution_decisions_csv(str(history_file))
            assert len(decisions) == _EXECUTION_BOOK_COUNT
            assert all(d.entry_status == "live" for d in decisions)
        finally:
            session.close()

    # (b3) -----------------------------------------------------------------
    @pytest.mark.parametrize("minutes_after_window_end", [0, 90])
    def test_b3_closed_window_records_no_decision_and_no_live_spot(
        self, tmp_path, live_spot, caplog, minutes_after_window_end: int
    ) -> None:
        from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

        session = self._make_session()
        try:
            # Day bd[20]: decisions recorded normally (one live fetch).
            cfg_on = self._config(tmp_path)
            snap1, r1 = self._run(session, cfg_on, 20)
            session.commit()
            assert live_spot.call_count == 1

            # Day bd[21]: batch created with the layer off, so no execution.csv
            # exists for it; bd[20]'s outcome is recorded by Step 4.
            cfg_off = self._config(tmp_path, run_execution_layer=False)
            snap2, r2 = self._run(session, cfg_off, 21)
            session.commit()
            assert r2.outcome_recorded is True
            batch2_dir = self._batch_dir(tmp_path, snap2.as_of_jst, r2.forecast_batch_id)
            assert not (batch2_dir / "execution.csv").exists()

            # A run whose clock is at/after bd[21]'s window end (bd[22] 08:00 JST)
            # while the provider's newest window still ends at bd[21]: the
            # one-day fallback rewrites as_of back to bd[21], whose batch exists
            # but carries no decisions.  The window is closed, so none are made.
            window_end = next_as_of_jst(snap2.as_of_jst)
            now_utc = (window_end + timedelta(minutes=minutes_after_window_end)).astimezone(
                timezone.utc
            )
            with caplog.at_level("WARNING", logger="ugh_quantamental.fx_protocol.automation"):
                _, r3 = self._run(session, cfg_on, 21, now_utc=now_utc)

            assert r3.as_of_jst == snap2.as_of_jst
            assert r3.forecast_batch_id == r2.forecast_batch_id
            assert r3.forecast_created is False
            assert r3.outcome_recorded is True  # Step 4 (idempotent) is unaffected
            assert r3.execution_decisions_recorded == 0
            assert r3.execution_csv_path is None
            assert live_spot.call_count == 1
            assert not (batch2_dir / "execution.csv").exists()
            assert any("already closed" in rec.getMessage() for rec in caplog.records)
            # The archive scan still evaluates bd[20]'s decisions, whose outcome
            # was persisted on bd[21] while the layer was off.
            assert r3.execution_evaluations_recorded == _EXECUTION_BOOK_COUNT
            assert (
                self._batch_dir(tmp_path, snap1.as_of_jst, r1.forecast_batch_id)
                / "execution_evaluation.csv"
            ).is_file()
        finally:
            session.close()

    # (c) ------------------------------------------------------------------
    def test_c_next_day_run_evaluates_the_previous_window(self, tmp_path, live_spot) -> None:
        from ugh_quantamental.fx_protocol.execution_exports import load_execution_evaluations_csv
        from ugh_quantamental.fx_protocol.execution_models import EXECUTION_BOOK_ORDER, BookId
        from ugh_quantamental.fx_protocol.ids import make_outcome_id

        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap1, r1 = self._run(session, cfg, 20)
            session.commit()
            snap2, r2 = self._run(session, cfg, 21)
            session.commit()

            assert r2.outcome_recorded is True
            assert r2.outcome_id == make_outcome_id(
                CurrencyPair.USDJPY, snap1.as_of_jst, snap2.as_of_jst, cfg.schema_version
            )
            assert r2.execution_decisions_recorded == _EXECUTION_BOOK_COUNT  # bd[21]'s own
            assert r2.execution_evaluations_recorded == _EXECUTION_BOOK_COUNT
            # Staging file is dated by the EVALUATED window's as_of, not today's.
            assert r2.execution_evaluation_csv_path == str(
                tmp_path / "execution" / "USDJPY_20260202_execution_evaluation.csv"
            )
            prev_dir = self._batch_dir(tmp_path, snap1.as_of_jst, r1.forecast_batch_id)
            evaluations = load_execution_evaluations_csv(str(prev_dir / "execution_evaluation.csv"))
            assert len(evaluations) == _EXECUTION_BOOK_COUNT
            assert [e.book_id for e in evaluations] == list(EXECUTION_BOOK_ORDER)
            expected_clock = self._run_clock(snap2.as_of_jst)
            for ev in evaluations:
                assert ev.outcome_id == r2.outcome_id
                assert ev.forecast_batch_id == r1.forecast_batch_id
                assert ev.as_of_jst == snap1.as_of_jst
                assert ev.window_end_jst == snap2.as_of_jst
                assert ev.realized_open == _WINDOW_OPEN
                assert ev.realized_close == _WINDOW_CLOSE
                assert ev.entry_status == "live"
                assert ev.entry_price_live == _LIVE_SPOT_PRICE
                assert ev.evaluated_at_utc == expected_clock
                if ev.side == 0:
                    assert ev.hit is None
                else:
                    assert ev.hit == (ev.side * (_WINDOW_CLOSE - _WINDOW_OPEN) > 0)
                    assert ev.pnl_live_bp == pytest.approx(
                        ev.side * (_WINDOW_CLOSE - _LIVE_SPOT_PRICE) / _LIVE_SPOT_PRICE * 1e4
                    )
            # bench_long is always long and the window closed up: a hit.
            assert evaluations[-1].book_id == BookId.bench_long
            assert evaluations[-1].hit is True
            # Evaluations are filed in the evaluated window's batch dir, not today's.
            today_dir = self._batch_dir(tmp_path, snap2.as_of_jst, r2.forecast_batch_id)
            assert (today_dir / "execution.csv").is_file()
            assert not (today_dir / "execution_evaluation.csv").exists()
        finally:
            session.close()

    # (c2) -----------------------------------------------------------------
    def test_c2_archive_scan_rewrites_deleted_evaluation_beyond_the_catchup_bound(
        self, tmp_path, live_spot
    ) -> None:
        from ugh_quantamental.fx_protocol.execution_exports import load_execution_evaluations_csv

        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap1, r1 = self._run(session, cfg, 20)
            session.commit()
            _, r2 = self._run(session, cfg, 21)
            session.commit()
            eval_file = (
                self._batch_dir(tmp_path, snap1.as_of_jst, r1.forecast_batch_id)
                / "execution_evaluation.csv"
            )
            assert eval_file.is_file()
            eval_file.unlink()

            later_day = 20 + cfg.outcome_catchup_days + 3
            _, r3 = self._run(session, cfg, later_day)

            # bd[20]'s window is outside the catch-up bound, and today's
            # preceding window has no batch: Steps 4 / 4b do nothing.
            assert r3.catchup_windows == ()
            assert r3.outcome_recorded is False
            # The archive scan has no bound: the outcome is in the DB, so the
            # evaluation is rewritten.  bd[21]'s decisions stay pending (no
            # outcome for its window) and are skipped silently.
            assert r3.execution_evaluations_recorded == _EXECUTION_BOOK_COUNT
            assert r3.execution_evaluation_csv_path is not None
            evaluations = load_execution_evaluations_csv(str(eval_file))
            assert len(evaluations) == _EXECUTION_BOOK_COUNT
            assert {e.outcome_id for e in evaluations} == {r2.outcome_id}
            assert {e.forecast_batch_id for e in evaluations} == {r1.forecast_batch_id}
        finally:
            session.close()

    # (c3) -----------------------------------------------------------------
    def test_c3_complete_evaluation_is_not_reevaluated(self, tmp_path, live_spot) -> None:
        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap1, r1 = self._run(session, cfg, 20)
            session.commit()
            _, r2 = self._run(session, cfg, 21)
            session.commit()
            eval_file = (
                self._batch_dir(tmp_path, snap1.as_of_jst, r1.forecast_batch_id)
                / "execution_evaluation.csv"
            )
            before = eval_file.read_bytes()
            before_mtime = eval_file.stat().st_mtime_ns

            # Same-day rerun with a later clock: a re-evaluation would change
            # evaluated_at_utc, hence the bytes.
            _, r3 = self._run(session, cfg, 21, hours_after_fixing=12)

            assert r3.outcome_recorded is True
            assert r3.execution_evaluations_recorded == 0
            assert r3.execution_evaluation_csv_path is None
            assert r3.execution_decisions_recorded == 0  # bd[21]'s decisions already archived
            assert eval_file.read_bytes() == before
            assert eval_file.stat().st_mtime_ns == before_mtime
        finally:
            session.close()

    # (c4) -----------------------------------------------------------------
    def test_c4_header_only_archive_is_rebuilt(self, tmp_path, live_spot) -> None:
        from ugh_quantamental.fx_protocol.execution_exports import (
            EXECUTION_FIELDNAMES,
            load_execution_decisions_csv,
        )

        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap, r1 = self._run(session, cfg, 20)
            session.commit()
            history_file = (
                self._batch_dir(tmp_path, snap.as_of_jst, r1.forecast_batch_id) / "execution.csv"
            )
            history_file.write_text(",".join(EXECUTION_FIELDNAMES) + "\r\n", encoding="utf-8")
            assert live_spot.call_count == 1

            _, r2 = self._run(session, cfg, 20, hours_after_fixing=12)

            assert r2.execution_decisions_recorded == _EXECUTION_BOOK_COUNT
            assert r2.execution_csv_path is not None
            assert live_spot.call_count == 2
            decisions = load_execution_decisions_csv(str(history_file))
            assert len(decisions) == _EXECUTION_BOOK_COUNT
        finally:
            session.close()

    # (d) ------------------------------------------------------------------
    def test_d_live_spot_failure_records_live_unavailable(self, tmp_path, live_spot) -> None:
        import csv

        from ugh_quantamental.fx_protocol.execution_exports import load_execution_decisions_csv

        live_spot.side_effect = FxDataFetchError("yahoo down")
        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap, result = self._run(session, cfg, 20)

            assert result.forecast_created is True
            assert result.execution_decisions_recorded == _EXECUTION_BOOK_COUNT
            assert result.execution_csv_path is not None
            assert live_spot.call_count == 1
            history_file = (
                self._batch_dir(tmp_path, snap.as_of_jst, result.forecast_batch_id)
                / "execution.csv"
            )
            decisions = load_execution_decisions_csv(str(history_file))
            assert len(decisions) == _EXECUTION_BOOK_COUNT
            for d in decisions:
                assert d.entry_status == "live_unavailable"
                assert d.entry_price_live is None
                assert d.entry_vendor is None
                assert d.entry_feed is None
                assert d.entry_time_utc == self._run_clock(snap.as_of_jst)
            with open(history_file, newline="", encoding="utf-8") as fh:
                raw_rows = list(csv.DictReader(fh))
            assert [row["entry_price_live"] for row in raw_rows] == [""] * _EXECUTION_BOOK_COUNT
            assert (tmp_path / "latest" / "execution.csv").is_file()
        finally:
            session.close()

    # (e) ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "overrides",
        [{"run_execution_layer": False}, {"write_csv_exports": False}],
        ids=["layer_off", "csv_exports_off"],
    )
    def test_e_disabled_layer_writes_nothing(self, tmp_path, live_spot, overrides: dict) -> None:
        session = self._make_session()
        try:
            cfg = self._config(tmp_path, **overrides)
            _, r1 = self._run(session, cfg, 20)
            session.commit()
            _, r2 = self._run(session, cfg, 21)
            session.commit()

            assert r1.forecast_created is True
            assert r2.outcome_recorded is True
            for result in (r1, r2):
                assert result.execution_csv_path is None
                assert result.execution_evaluation_csv_path is None
                assert result.execution_decisions_recorded == 0
                assert result.execution_evaluations_recorded == 0
            assert live_spot.call_count == 0
            assert not (tmp_path / "latest" / "execution.csv").exists()
            assert not (tmp_path / "execution").exists()
            assert list(tmp_path.glob("history/*/*/execution*.csv")) == []
        finally:
            session.close()

    # (f) ------------------------------------------------------------------
    def test_f_decision_failure_is_isolated_from_the_run(self, tmp_path, live_spot) -> None:
        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            with patch(
                "ugh_quantamental.fx_protocol.automation.build_execution_decisions",
                side_effect=RuntimeError("decision rule exploded"),
            ):
                snap, result = self._run(session, cfg, 20)

            assert result.forecast_created is True
            assert result.forecast_batch_id is not None
            assert result.forecast_csv_path is not None
            assert result.manifest_path is not None
            assert result.execution_decisions_recorded == 0
            assert result.execution_csv_path is None
            batch_dir = self._batch_dir(tmp_path, snap.as_of_jst, result.forecast_batch_id)
            assert (batch_dir / "forecast.csv").is_file()
            assert not (batch_dir / "execution.csv").exists()
            assert not (tmp_path / "latest" / "execution.csv").exists()
        finally:
            session.close()

    def test_f_evaluation_failure_is_isolated_and_retried_next_run(
        self, tmp_path, live_spot
    ) -> None:
        session = self._make_session()
        try:
            cfg = self._config(tmp_path)
            snap1, r1 = self._run(session, cfg, 20)
            session.commit()
            eval_file = (
                self._batch_dir(tmp_path, snap1.as_of_jst, r1.forecast_batch_id)
                / "execution_evaluation.csv"
            )

            with patch(
                "ugh_quantamental.fx_protocol.automation.evaluate_execution_decisions",
                side_effect=RuntimeError("evaluation exploded"),
            ):
                _, r2 = self._run(session, cfg, 21)
            session.commit()

            assert r2.outcome_recorded is True
            assert r2.evaluation_count == 7
            assert r2.execution_evaluations_recorded == 0
            assert r2.execution_evaluation_csv_path is None
            assert r2.execution_decisions_recorded == _EXECUTION_BOOK_COUNT  # 3b independent of 4c
            assert not eval_file.exists()

            # The next run's archive scan retries the evaluation (outcome in the DB).
            _, r3 = self._run(session, cfg, 21, hours_after_fixing=12)
            assert r3.execution_evaluations_recorded == _EXECUTION_BOOK_COUNT
            assert eval_file.is_file()
        finally:
            session.close()
