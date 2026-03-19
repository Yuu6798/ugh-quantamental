"""Tests for AlphaVantageXMarketDataProvider and related helpers in data_sources.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.data_models import FxCompletedWindow
from ugh_quantamental.fx_protocol.data_sources import (
    AlphaVantageXMarketDataProvider,
    FxDataFetchError,
    FxMarketDataProvider,
    _av_date_to_window,
    _parse_av_snapshot,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair

_JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _build_av_payload(n_bars: int, as_of_jst: datetime) -> dict:
    """Build a mock Alpha Vantage FX_DAILY response with n_bars business-day entries.

    The newest entry's window_end_jst == as_of_jst (freshness constraint).
    Alpha Vantage uses YYYY-MM-DD UTC date strings.
    """
    bar_dates = []
    current = as_of_jst - timedelta(days=1)
    while len(bar_dates) < n_bars:
        if current.weekday() not in {5, 6}:  # Monday=0 … Friday=4
            bar_dates.append(current.date())
        current -= timedelta(days=1)
    # bar_dates[0] is newest (as_of_jst - 1 business day), bar_dates[-1] is oldest.

    time_series = {}
    for d in bar_dates:
        time_series[d.isoformat()] = {
            "1. open": "149.5000",
            "2. high": "151.5000",
            "3. low": "148.5000",
            "4. close": "150.5000",
        }

    latest_date = bar_dates[0].isoformat()
    return {
        "Meta Data": {
            "1. Information": "Forex Daily Prices (open, high, low, close)",
            "2. From Symbol": "USD",
            "3. To Symbol": "JPY",
            "4. Output Size": "Compact",
            "5. Last Refreshed": latest_date,
            "6. Time Zone": "UTC",
        },
        "Time Series FX (Daily)": time_series,
    }


# ---------------------------------------------------------------------------
# _av_date_to_window unit tests
# ---------------------------------------------------------------------------


class TestAvDateToWindow:
    """Unit tests for the _av_date_to_window helper."""

    _AS_OF = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)  # Tuesday

    def test_valid_weekday_returns_window(self) -> None:
        win = _av_date_to_window("2026-03-09", 149.5, 151.5, 148.5, 150.5)
        assert win is not None
        assert isinstance(win, FxCompletedWindow)
        assert win.window_start_jst == datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST)
        assert win.window_end_jst == self._AS_OF

    def test_saturday_returns_none(self) -> None:
        assert _av_date_to_window("2026-03-07", 149.5, 151.5, 148.5, 150.5) is None

    def test_sunday_returns_none(self) -> None:
        assert _av_date_to_window("2026-03-08", 149.5, 151.5, 148.5, 150.5) is None

    def test_invalid_date_string_returns_none(self) -> None:
        assert _av_date_to_window("not-a-date", 149.5, 151.5, 148.5, 150.5) is None

    def test_inverted_high_low_swapped(self) -> None:
        # high < low should be swapped, not rejected.
        win = _av_date_to_window("2026-03-09", 150.0, 148.5, 151.5, 150.0)
        assert win is not None
        assert win.high_price >= win.low_price

    def test_open_clamped_to_range(self) -> None:
        # open slightly below low due to float drift — should be clamped.
        win = _av_date_to_window("2026-03-09", 148.49, 151.5, 148.5, 150.0)
        assert win is not None
        assert win.open_price >= win.low_price

    def test_close_clamped_to_range(self) -> None:
        win = _av_date_to_window("2026-03-09", 150.0, 151.5, 148.5, 151.51)
        assert win is not None
        assert win.close_price <= win.high_price

    def test_ohlc_values_stored_correctly(self) -> None:
        win = _av_date_to_window("2026-03-09", 149.5, 151.5, 148.5, 150.5)
        assert win is not None
        assert win.open_price == 149.5
        assert win.high_price == 151.5
        assert win.low_price == 148.5
        assert win.close_price == 150.5


# ---------------------------------------------------------------------------
# _parse_av_snapshot unit tests
# ---------------------------------------------------------------------------


class TestParseAvSnapshot:
    """Tests for the _parse_av_snapshot helper."""

    _AS_OF = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)  # Tuesday

    def test_parses_valid_payload(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        snap = _parse_av_snapshot(payload, self._AS_OF)
        assert snap.pair == CurrencyPair.USDJPY
        assert snap.current_spot == 150.5
        assert len(snap.completed_windows) >= 20

    def test_newest_window_ends_at_as_of_jst(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        snap = _parse_av_snapshot(payload, self._AS_OF)
        assert snap.completed_windows[-1].window_end_jst == self._AS_OF

    def test_windows_ordered_oldest_to_newest(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        snap = _parse_av_snapshot(payload, self._AS_OF)
        starts = [w.window_start_jst for w in snap.completed_windows]
        assert starts == sorted(starts)

    def test_future_windows_excluded(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        # Inject a future date entry.
        payload["Time Series FX (Daily)"]["2099-12-31"] = {
            "1. open": "149.5",
            "2. high": "151.5",
            "3. low": "148.5",
            "4. close": "150.5",
        }
        snap = _parse_av_snapshot(payload, self._AS_OF)
        for win in snap.completed_windows:
            assert win.window_end_jst <= self._AS_OF

    def test_weekend_dates_excluded(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        # Inject a Saturday entry.
        payload["Time Series FX (Daily)"]["2026-03-07"] = {
            "1. open": "149.5",
            "2. high": "151.5",
            "3. low": "148.5",
            "4. close": "150.5",
        }
        snap = _parse_av_snapshot(payload, self._AS_OF)
        for win in snap.completed_windows:
            assert win.window_start_jst.weekday() < 5

    def test_insufficient_windows_raises(self) -> None:
        payload = _build_av_payload(5, self._AS_OF)
        with pytest.raises(FxDataFetchError, match="Insufficient"):
            _parse_av_snapshot(payload, self._AS_OF)

    def test_empty_time_series_raises(self) -> None:
        with pytest.raises(FxDataFetchError, match="no time-series data"):
            _parse_av_snapshot({}, self._AS_OF)

    def test_rate_limit_note_included_in_error(self) -> None:
        payload = {"Note": "Thank you for using Alpha Vantage! Our standard API rate limit is..."}
        with pytest.raises(FxDataFetchError, match="Alpha Vantage"):
            _parse_av_snapshot(payload, self._AS_OF)

    def test_invalid_key_information_included_in_error(self) -> None:
        payload = {"Information": "The demo API key is for demo purposes only."}
        with pytest.raises(FxDataFetchError, match="Alpha Vantage"):
            _parse_av_snapshot(payload, self._AS_OF)

    def test_provenance_vendor_is_alpha_vantage(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        snap = _parse_av_snapshot(payload, self._AS_OF)
        assert snap.market_data_provenance.vendor == "alpha_vantage"

    def test_current_spot_from_newest_completed_window_close(self) -> None:
        """current_spot must equal the close of the newest *completed* window."""
        payload = _build_av_payload(22, self._AS_OF)
        # Override the newest completed date's close to a distinct value within [low, high]
        # so the clamping in _av_date_to_window does not alter it.
        # _build_av_payload uses low=148.5, high=151.5; choose a value in that range.
        latest_date = max(payload["Time Series FX (Daily)"].keys())
        payload["Time Series FX (Daily)"][latest_date]["4. close"] = "149.9876"
        snap = _parse_av_snapshot(payload, self._AS_OF)
        assert snap.current_spot == pytest.approx(149.9876)

    def test_current_spot_not_contaminated_by_future_bars(self) -> None:
        """Bars beyond as_of_jst must not influence current_spot (no look-ahead)."""
        payload = _build_av_payload(22, self._AS_OF)
        # Newest completed bar has close 150.5.  Inject a future bar with a very
        # different close; current_spot must still reflect the completed data only.
        payload["Time Series FX (Daily)"]["2099-12-31"] = {
            "1. open": "999.0",
            "2. high": "999.5",
            "3. low": "998.5",
            "4. close": "999.0",
        }
        snap = _parse_av_snapshot(payload, self._AS_OF)
        assert snap.current_spot == pytest.approx(150.5)
        # And the future window must not appear in completed_windows.
        for win in snap.completed_windows:
            assert win.window_end_jst <= self._AS_OF


# ---------------------------------------------------------------------------
# AlphaVantageXMarketDataProvider integration tests
# ---------------------------------------------------------------------------


class TestAlphaVantageXMarketDataProvider:
    """Tests for AlphaVantageXMarketDataProvider — no real network calls."""

    _AS_OF = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)  # Tuesday

    def _make_provider(self, api_key: str = "test_key_abc") -> AlphaVantageXMarketDataProvider:
        return AlphaVantageXMarketDataProvider(
            api_key=api_key, max_retries=0, retry_base_delay=0.0,
        )

    def _mock_urlopen(self, payload: dict) -> MagicMock:
        body = json.dumps(payload).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = body
        return mock_resp

    def test_successful_fetch_returns_valid_snapshot(self) -> None:
        payload = _build_av_payload(22, self._AS_OF)
        provider = self._make_provider()
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            snap = provider.fetch_snapshot(self._AS_OF)

        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) >= 20
        assert snap.current_spot == 150.5
        assert snap.completed_windows[-1].window_end_jst == self._AS_OF

    def test_missing_api_key_raises_before_network(self) -> None:
        provider = AlphaVantageXMarketDataProvider(api_key="")
        with pytest.raises(FxDataFetchError, match="ALPHAVANTAGE_API_KEY"):
            provider.fetch_snapshot(self._AS_OF)

    def test_api_key_read_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "env_key_xyz")
        provider = AlphaVantageXMarketDataProvider()
        assert provider._api_key == "env_key_xyz"

    def test_constructor_key_takes_precedence_over_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "env_key")
        provider = AlphaVantageXMarketDataProvider(api_key="constructor_key")
        assert provider._api_key == "constructor_key"

    def test_network_error_raises(self) -> None:
        import urllib.error

        provider = self._make_provider()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(FxDataFetchError, match="Network error"):
                provider.fetch_snapshot(self._AS_OF)

    def test_http_error_raises(self) -> None:
        import urllib.error

        provider = self._make_provider()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                url="https://www.alphavantage.co/query",
                code=429,
                msg="Too Many Requests",
                hdrs=None,  # type: ignore[arg-type]
                fp=None,
            ),
        ):
            with pytest.raises(FxDataFetchError, match="429"):
                provider.fetch_snapshot(self._AS_OF)

    def test_non_200_status_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 503
        mock_resp.read.return_value = b"Service Unavailable"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="503"):
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
        payload = _build_av_payload(5, self._AS_OF)
        provider = self._make_provider()
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="Insufficient"):
                provider.fetch_snapshot(self._AS_OF)

    def test_rate_limit_response_raises(self) -> None:
        payload = {"Note": "Thank you for using Alpha Vantage! Our standard API rate limit..."}
        provider = self._make_provider()
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="no time-series data"):
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

    def test_invalid_json_logs_debug(self, caplog) -> None:
        """Regression: json.JSONDecodeError at data_sources.py:553-555 must emit logger.debug.

        When the Alpha Vantage response body is not valid JSON, the provider raises
        ``FxDataFetchError`` AND emits a ``logger.debug`` message.  This test verifies
        both behaviours to guard against a recurrence of the bot-applied syntax failure
        at those lines.
        """
        import logging

        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = b"<html>not json</html>"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with caplog.at_level(logging.DEBUG, logger="ugh_quantamental.fx_protocol.data_sources"):
                with pytest.raises(FxDataFetchError, match="Invalid JSON"):
                    provider.fetch_snapshot(self._AS_OF)

        assert any("non-JSON" in record.message for record in caplog.records)

    def test_rate_limit_retries_then_succeeds(self) -> None:
        """Provider retries on rate-limit and succeeds when data arrives."""
        rate_limit_payload = {
            "Note": "Thank you for using Alpha Vantage! Our standard API rate limit...",
        }
        valid_payload = _build_av_payload(22, self._AS_OF)

        provider = AlphaVantageXMarketDataProvider(
            api_key="test_key_abc", max_retries=2, retry_base_delay=0.0,
        )
        rate_resp = self._mock_urlopen(rate_limit_payload)
        valid_resp = self._mock_urlopen(valid_payload)

        with patch("urllib.request.urlopen", side_effect=[rate_resp, valid_resp]):
            snap = provider.fetch_snapshot(self._AS_OF)

        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) >= 20

    def test_rate_limit_retries_exhausted_raises(self) -> None:
        """Provider raises after exhausting all retries on rate-limit responses."""
        rate_limit_payload = {
            "Note": "Thank you for using Alpha Vantage! Our standard API rate limit...",
        }

        provider = AlphaVantageXMarketDataProvider(
            api_key="test_key_abc", max_retries=2, retry_base_delay=0.0,
        )
        responses = [self._mock_urlopen(rate_limit_payload) for _ in range(3)]

        with patch("urllib.request.urlopen", side_effect=responses):
            with pytest.raises(FxDataFetchError, match="no time-series data"):
                provider.fetch_snapshot(self._AS_OF)
