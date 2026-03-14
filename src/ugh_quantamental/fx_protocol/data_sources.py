"""Market-data provider abstraction for the FX Daily Automation layer (v1).

Provides a structural Protocol and a minimal HTTP JSON implementation.
No provider-specific SDK dependency; uses only stdlib urllib.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EventTag,
    MarketDataProvenance,
    _to_jst,
)


class FxDataFetchError(Exception):
    """Raised when the market data provider cannot return a valid snapshot."""


@runtime_checkable
class FxMarketDataProvider(Protocol):
    """Structural contract for FX market data providers."""

    def fetch_snapshot(self, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
        """Fetch a market snapshot for the given canonical as_of_jst.

        Parameters
        ----------
        as_of_jst:
            Canonical 08:00 JST datetime for today's forecast window.

        Returns
        -------
        FxProtocolMarketSnapshot
            Fully typed and validated snapshot.

        Raises
        ------
        FxDataFetchError
            On network failure, parse error, or schema validation error.
        """
        ...


def _parse_event_tags(raw: list[str] | None) -> tuple[EventTag, ...]:
    """Parse a list of event tag strings into a tuple of ``EventTag`` values."""
    if not raw:
        return ()
    result = []
    for tag_str in raw:
        try:
            result.append(EventTag(tag_str))
        except ValueError as exc:
            raise FxDataFetchError(f"Unknown event tag {tag_str!r}") from exc
    return tuple(result)


def _parse_completed_window(raw: dict) -> FxCompletedWindow:
    """Parse one OHLC window dict into a ``FxCompletedWindow``."""
    try:
        return FxCompletedWindow(
            window_start_jst=_to_jst(datetime.fromisoformat(raw["window_start_jst"])),
            window_end_jst=_to_jst(datetime.fromisoformat(raw["window_end_jst"])),
            open_price=float(raw["open_price"]),
            high_price=float(raw["high_price"]),
            low_price=float(raw["low_price"]),
            close_price=float(raw["close_price"]),
            event_tags=_parse_event_tags(raw.get("event_tags")),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise FxDataFetchError(f"Failed to parse completed window: {exc}") from exc


def _parse_provenance(raw: dict) -> MarketDataProvenance:
    """Parse a provenance dict into a ``MarketDataProvenance``."""
    try:
        retrieved_at_raw = raw.get("retrieved_at_utc")
        if retrieved_at_raw is None:
            retrieved_at = datetime.now(timezone.utc)
        else:
            retrieved_at = datetime.fromisoformat(retrieved_at_raw)
        return MarketDataProvenance(
            vendor=raw["vendor"],
            feed_name=raw["feed_name"],
            price_type=raw["price_type"],
            resolution=raw["resolution"],
            timezone=raw["timezone"],
            retrieved_at_utc=retrieved_at,
            source_ref=raw.get("source_ref"),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise FxDataFetchError(f"Failed to parse provenance: {exc}") from exc


def _parse_snapshot(payload: dict, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
    """Parse the full JSON payload into an ``FxProtocolMarketSnapshot``."""
    try:
        pair = CurrencyPair(payload.get("pair", CurrencyPair.USDJPY.value))
        current_spot = float(payload["current_spot"])
        raw_windows = payload.get("completed_windows", [])
        completed_windows = tuple(
            _parse_completed_window(w) for w in raw_windows
        )
        provenance = _parse_provenance(payload["market_data_provenance"])
        # Always use the as_of_jst supplied by the caller (derived from the
        # protocol calendar).  Provider payloads may contain stale or mismatched
        # as_of_jst values; accepting them would silently shift the forecast
        # window and break the canonical JST window semantics.
        return FxProtocolMarketSnapshot(
            pair=pair,
            as_of_jst=as_of_jst,
            current_spot=current_spot,
            completed_windows=completed_windows,
            market_data_provenance=provenance,
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise FxDataFetchError(f"Failed to parse market snapshot: {exc}") from exc


class HttpJsonFxMarketDataProvider:
    """Minimal HTTP JSON market data provider using only stdlib urllib.

    Configuration via environment variables:
    - ``FX_DATA_URL``: base URL for the data endpoint (required)
    - ``FX_DATA_AUTH_TOKEN``: optional bearer token

    The endpoint is expected to return a JSON body conforming to the
    ``FxProtocolMarketSnapshot`` contract.

    In tests, stub this provider by subclassing or monkeypatching
    ``fetch_snapshot``; no real network calls are made in tests.
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        auth_token: str | None = None,
        timeout: int = 30,
    ) -> None:
        self._url = url or os.environ.get("FX_DATA_URL", "")
        self._auth_token = auth_token or os.environ.get("FX_DATA_AUTH_TOKEN")
        self._timeout = timeout

    def fetch_snapshot(self, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
        """Fetch and parse a market snapshot from the configured HTTP endpoint.

        Raises
        ------
        FxDataFetchError
            On missing URL configuration, network failure, non-200 status,
            invalid JSON, or schema validation failure.
        """
        if not self._url:
            raise FxDataFetchError(
                "FX_DATA_URL is not set; cannot fetch market snapshot"
            )

        headers = {"Accept": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        req = urllib.request.Request(self._url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = resp.status
                body = resp.read()
        except urllib.error.HTTPError as exc:
            raise FxDataFetchError(
                f"HTTP {exc.code} from {self._url}: {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise FxDataFetchError(
                f"Network error fetching {self._url}: {exc.reason}"
            ) from exc

        if status != 200:
            raise FxDataFetchError(f"HTTP {status} from {self._url}")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FxDataFetchError(
                f"Invalid JSON from {self._url}: {exc}"
            ) from exc

        return _parse_snapshot(payload, as_of_jst)
