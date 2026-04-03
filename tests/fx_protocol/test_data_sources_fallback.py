"""Tests for FallbackFxMarketDataProvider in data_sources.py."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.data_sources import (
    FallbackFxMarketDataProvider,
    FxDataFetchError,
)

_JST = ZoneInfo("Asia/Tokyo")
_AS_OF = datetime(2026, 4, 3, 8, 0, 0, tzinfo=_JST)


class _StubProvider:
    """Configurable stub that returns a fixed snapshot or raises."""

    def __init__(self, *, snapshot=None, error: str | None = None) -> None:
        self._snapshot = snapshot
        self._error = error
        self.call_count = 0

    def fetch_snapshot(self, as_of_jst: datetime):
        self.call_count += 1
        if self._error:
            raise FxDataFetchError(self._error)
        return self._snapshot


class TestFallbackProvider:
    """FallbackFxMarketDataProvider delegates correctly."""

    def test_primary_succeeds_no_fallback(self) -> None:
        primary = _StubProvider(snapshot="primary_result")
        fallback = _StubProvider(snapshot="fallback_result")
        provider = FallbackFxMarketDataProvider(primary=primary, fallback=fallback)

        result = provider.fetch_snapshot(_AS_OF)

        assert result == "primary_result"
        assert primary.call_count == 1
        assert fallback.call_count == 0

    def test_primary_fails_uses_fallback(self) -> None:
        primary = _StubProvider(error="rate limit exceeded")
        fallback = _StubProvider(snapshot="fallback_result")
        provider = FallbackFxMarketDataProvider(primary=primary, fallback=fallback)

        result = provider.fetch_snapshot(_AS_OF)

        assert result == "fallback_result"
        assert primary.call_count == 1
        assert fallback.call_count == 1

    def test_both_fail_raises_fallback_error(self) -> None:
        primary = _StubProvider(error="rate limit")
        fallback = _StubProvider(error="network error")
        provider = FallbackFxMarketDataProvider(primary=primary, fallback=fallback)

        with pytest.raises(FxDataFetchError, match="network error"):
            provider.fetch_snapshot(_AS_OF)

        assert primary.call_count == 1
        assert fallback.call_count == 1
