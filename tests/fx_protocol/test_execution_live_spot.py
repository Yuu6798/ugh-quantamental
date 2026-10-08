"""Tests for data_sources.fetch_live_spot_yahoo (FX Execution Layer v1, spec §6).

``urllib.request.urlopen`` is stubbed with ``monkeypatch`` the same way the
Yahoo provider tests in ``test_automation.py`` do; no real network calls.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from ugh_quantamental.fx_protocol.data_sources import FxDataFetchError, fetch_live_spot_yahoo

_YF_CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/USDJPY=X"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _payload(spot: object = 150.5) -> dict:
    """Minimal Yahoo Finance chart response carrying ``meta.regularMarketPrice``."""
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": spot,
                        "currency": "JPY",
                        "symbol": "USDJPY=X",
                    },
                    "timestamp": [],
                    "indicators": {"quote": [{}]},
                }
            ],
            "error": None,
        }
    }


def _mock_response(body: bytes, status: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = status
    mock_resp.read.return_value = body
    return mock_resp


def _stub_urlopen(monkeypatch: pytest.MonkeyPatch, response=None, *, side_effect=None) -> MagicMock:
    urlopen = MagicMock(return_value=response, side_effect=side_effect)
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return urlopen


def _stub_payload(monkeypatch: pytest.MonkeyPatch, payload: dict) -> MagicMock:
    return _stub_urlopen(monkeypatch, _mock_response(json.dumps(payload).encode()))


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestFetchLiveSpotYahooSuccess:
    def test_returns_spot_and_aware_utc_timestamp(self, monkeypatch) -> None:
        urlopen = _stub_payload(monkeypatch, _payload(150.5))

        before = datetime.now(timezone.utc)
        spot, retrieved_at = fetch_live_spot_yahoo()
        after = datetime.now(timezone.utc)

        assert spot == 150.5
        assert isinstance(spot, float)
        assert retrieved_at.tzinfo is not None
        assert retrieved_at.utcoffset() == timedelta(0)
        assert before <= retrieved_at <= after
        assert urlopen.call_count == 1

    def test_requests_usdjpy_chart_endpoint_with_timeout(self, monkeypatch) -> None:
        urlopen = _stub_payload(monkeypatch, _payload())

        fetch_live_spot_yahoo(timeout=7)

        (req,), kwargs = urlopen.call_args
        assert isinstance(req, urllib.request.Request)
        assert req.full_url.startswith(_YF_CHART_URL)
        assert "interval=1d" in req.full_url
        assert req.has_header("User-agent")
        assert kwargs["timeout"] == 7

    def test_default_timeout_is_30_seconds(self, monkeypatch) -> None:
        urlopen = _stub_payload(monkeypatch, _payload())

        fetch_live_spot_yahoo()

        assert urlopen.call_args.kwargs["timeout"] == 30

    def test_integer_spot_is_coerced_to_float(self, monkeypatch) -> None:
        _stub_payload(monkeypatch, _payload(150))

        spot, _ = fetch_live_spot_yahoo()

        assert spot == 150.0
        assert isinstance(spot, float)

    def test_numeric_string_spot_is_accepted(self, monkeypatch) -> None:
        _stub_payload(monkeypatch, _payload("149.875"))

        spot, _ = fetch_live_spot_yahoo()

        assert spot == 149.875


# ---------------------------------------------------------------------------
# Payload-shape failures → FxDataFetchError
# ---------------------------------------------------------------------------


class TestFetchLiveSpotYahooPayloadFailures:
    @pytest.mark.parametrize("result", [[], None], ids=["empty_list", "null"])
    def test_empty_result_raises(self, monkeypatch, result) -> None:
        payload = _payload()
        payload["chart"]["result"] = result
        _stub_payload(monkeypatch, payload)

        with pytest.raises(FxDataFetchError, match="no chart result"):
            fetch_live_spot_yahoo()

    def test_missing_regular_market_price_raises(self, monkeypatch) -> None:
        payload = _payload()
        del payload["chart"]["result"][0]["meta"]["regularMarketPrice"]
        _stub_payload(monkeypatch, payload)

        with pytest.raises(FxDataFetchError, match="regularMarketPrice"):
            fetch_live_spot_yahoo()

    def test_null_regular_market_price_raises(self, monkeypatch) -> None:
        _stub_payload(monkeypatch, _payload(None))

        with pytest.raises(FxDataFetchError, match="regularMarketPrice"):
            fetch_live_spot_yahoo()

    def test_missing_meta_raises(self, monkeypatch) -> None:
        payload = _payload()
        del payload["chart"]["result"][0]["meta"]
        _stub_payload(monkeypatch, payload)

        with pytest.raises(FxDataFetchError, match="regularMarketPrice"):
            fetch_live_spot_yahoo()

    @pytest.mark.parametrize("spot", [0, 0.0, -1.0, -150.5])
    def test_non_positive_spot_raises(self, monkeypatch, spot) -> None:
        _stub_payload(monkeypatch, _payload(spot))

        with pytest.raises(FxDataFetchError, match="positive"):
            fetch_live_spot_yahoo()

    @pytest.mark.parametrize(
        "spot", [float("nan"), float("inf"), float("-inf")], ids=["nan", "inf", "-inf"]
    )
    def test_non_finite_spot_raises(self, monkeypatch, spot) -> None:
        # json.dumps emits NaN / Infinity tokens, which json.loads parses back to floats.
        _stub_payload(monkeypatch, _payload(spot))

        with pytest.raises(FxDataFetchError, match="finite"):
            fetch_live_spot_yahoo()

    @pytest.mark.parametrize("spot", ["abc", True, [150.5]], ids=["text", "bool", "list"])
    def test_non_numeric_spot_raises(self, monkeypatch, spot) -> None:
        _stub_payload(monkeypatch, _payload(spot))

        with pytest.raises(FxDataFetchError, match="regularMarketPrice"):
            fetch_live_spot_yahoo()

    def test_chart_error_block_raises(self, monkeypatch) -> None:
        payload = {
            "chart": {
                "result": None,
                "error": {"code": "Not Found", "description": "No data found"},
            }
        }
        _stub_payload(monkeypatch, payload)

        with pytest.raises(FxDataFetchError, match="error payload"):
            fetch_live_spot_yahoo()

    def test_missing_chart_object_raises(self, monkeypatch) -> None:
        _stub_payload(monkeypatch, {"quote": {}})

        with pytest.raises(FxDataFetchError, match="'chart'"):
            fetch_live_spot_yahoo()

    def test_non_object_payload_raises(self, monkeypatch) -> None:
        _stub_urlopen(monkeypatch, _mock_response(b"[]"))

        with pytest.raises(FxDataFetchError, match="not a JSON object"):
            fetch_live_spot_yahoo()

    def test_non_object_result_entry_raises(self, monkeypatch) -> None:
        payload = _payload()
        payload["chart"]["result"] = ["oops"]
        _stub_payload(monkeypatch, payload)

        with pytest.raises(FxDataFetchError, match="not an object"):
            fetch_live_spot_yahoo()

    def test_invalid_json_raises(self, monkeypatch) -> None:
        _stub_urlopen(monkeypatch, _mock_response(b"NOT JSON AT ALL"))

        with pytest.raises(FxDataFetchError, match="JSON"):
            fetch_live_spot_yahoo()


# ---------------------------------------------------------------------------
# Transport failures → FxDataFetchError
# ---------------------------------------------------------------------------


class TestFetchLiveSpotYahooTransportFailures:
    def test_url_error_raises(self, monkeypatch) -> None:
        _stub_urlopen(monkeypatch, side_effect=urllib.error.URLError("connection refused"))

        with pytest.raises(FxDataFetchError, match="Network error") as excinfo:
            fetch_live_spot_yahoo()

        assert isinstance(excinfo.value.__cause__, urllib.error.URLError)

    def test_http_error_raises(self, monkeypatch) -> None:
        http_error = urllib.error.HTTPError(_YF_CHART_URL, 503, "Service Unavailable", {}, None)
        _stub_urlopen(monkeypatch, side_effect=http_error)

        with pytest.raises(FxDataFetchError, match="HTTP 503"):
            fetch_live_spot_yahoo()

    def test_socket_timeout_raises(self, monkeypatch) -> None:
        _stub_urlopen(monkeypatch, side_effect=TimeoutError("timed out"))

        with pytest.raises(FxDataFetchError, match="timed out"):
            fetch_live_spot_yahoo()

    def test_url_error_wrapping_timeout_raises(self, monkeypatch) -> None:
        _stub_urlopen(monkeypatch, side_effect=urllib.error.URLError(TimeoutError("timed out")))

        with pytest.raises(FxDataFetchError, match="timed out"):
            fetch_live_spot_yahoo()

    def test_truncated_read_raises(self, monkeypatch) -> None:
        import http.client

        response = _mock_response(b"")
        response.read.side_effect = http.client.IncompleteRead(b"{")
        _stub_urlopen(monkeypatch, response)

        with pytest.raises(FxDataFetchError, match="Transport error"):
            fetch_live_spot_yahoo()

    def test_non_200_status_raises(self, monkeypatch) -> None:
        _stub_urlopen(monkeypatch, _mock_response(b'{"error": "rate limited"}', status=429))

        with pytest.raises(FxDataFetchError, match="429"):
            fetch_live_spot_yahoo()

    def test_no_network_in_tests(self, monkeypatch) -> None:
        """Confirm the function never reaches the real network when urlopen is stubbed."""
        urlopen = _stub_urlopen(
            monkeypatch, side_effect=urllib.error.URLError("no network in tests")
        )

        with pytest.raises(FxDataFetchError, match="Network error"):
            fetch_live_spot_yahoo()

        assert urlopen.call_count == 1
