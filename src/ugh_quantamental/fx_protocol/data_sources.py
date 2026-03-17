"""Market-data provider abstraction for the FX Daily Automation layer (v1).

Provides:
- ``FxMarketDataProvider``: structural protocol (unchanged)
- ``YahooFinanceFxMarketDataProvider``: default public provider (no auth required)
- ``AlphaVantageXMarketDataProvider``: Alpha Vantage FX_DAILY provider (free API key required)
- ``HttpJsonFxMarketDataProvider``: optional custom-endpoint provider (retained for
  users with private data feeds; requires ``FX_DATA_URL``)

No provider-specific SDK dependency; uses only stdlib urllib.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from typing import Protocol, runtime_checkable
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.calendar import is_protocol_business_day, next_as_of_jst
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

_JST = ZoneInfo("Asia/Tokyo")
logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Yahoo Finance public provider (default; no auth required)
# ---------------------------------------------------------------------------

_YF_BASE_URL = "https://query2.finance.yahoo.com/v8/finance/chart"
_YF_SYMBOL = "USDJPY=X"
_YF_INTERVAL = "1d"
_YF_RANGE = "60d"  # 60 calendar days → ~40 business-day bars; ensures >= 20 completed windows


def _yahoo_bar_to_window(
    ts: int,
    open_p: float,
    high_p: float,
    low_p: float,
    close_p: float,
) -> FxCompletedWindow | None:
    """Convert one Yahoo Finance daily bar into a protocol ``FxCompletedWindow``.

    Normalization rule (deterministic)
    -----------------------------------
    Yahoo Finance daily bars for ``USDJPY=X`` carry Unix-second UTC timestamps
    at midnight UTC of the trading date.  The protocol window is aligned to
    08:00 JST, so the mapping is:

    1. Convert the Unix timestamp to a UTC datetime, then to JST.
    2. Extract the JST *date* (UTC midnight = JST 09:00; same calendar date).
    3. Construct ``window_start_jst`` = 08:00 JST on that date.
    4. Derive ``window_end_jst`` = ``next_as_of_jst(window_start_jst)``
       (08:00 JST on the next protocol business day, skipping weekends).
    5. Discard bars whose JST date falls on Saturday or Sunday.
    6. If ``high_p < low_p`` (rare Yahoo Finance FX artefact), swap them.
    7. Clamp ``open_p`` and ``close_p`` to ``[low_p, high_p]`` to tolerate
       minor floating-point drift in the source data.

    Returns ``None`` for weekend bars, bars with invalid timestamps, or bars
    that fail ``FxCompletedWindow`` construction.
    """
    try:
        ts_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None

    ts_jst = ts_utc.astimezone(_JST)
    jst_date = ts_jst.date()

    window_start = datetime(
        jst_date.year, jst_date.month, jst_date.day, 8, 0, 0, tzinfo=_JST
    )
    if not is_protocol_business_day(window_start):
        return None  # skip weekend / non-business bars

    window_end = next_as_of_jst(window_start)

    # Guard against inverted high/low (very rare in FX source data).
    if high_p < low_p:
        high_p, low_p = low_p, high_p

    # Clamp open/close to [low, high] so the strict protocol validator accepts
    # otherwise-valid bars that have minor floating-point drift.
    open_p = max(low_p, min(high_p, open_p))
    close_p = max(low_p, min(high_p, close_p))

    try:
        return FxCompletedWindow(
            window_start_jst=window_start,
            window_end_jst=window_end,
            open_price=open_p,
            high_price=high_p,
            low_price=low_p,
            close_price=close_p,
        )
    except ValueError:
        return None


def _parse_yahoo_snapshot(payload: dict, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
    """Parse a Yahoo Finance v8/finance/chart response into an ``FxProtocolMarketSnapshot``.

    Parameters
    ----------
    payload:
        Parsed JSON from ``{_YF_BASE_URL}/{_YF_SYMBOL}?interval=1d&range=60d``.
    as_of_jst:
        Canonical 08:00 JST timestamp from the protocol calendar.  Only windows
        whose ``window_end_jst <= as_of_jst`` are included (completed windows).

    Raises
    ------
    FxDataFetchError
        On unexpected response shape, missing ``regularMarketPrice``, or fewer
        than 20 completed protocol windows.
    """
    try:
        result = payload["chart"]["result"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise FxDataFetchError(
            f"Unexpected Yahoo Finance response shape: {exc}"
        ) from exc

    # Current spot price from the response metadata.
    meta = result.get("meta") or {}
    raw_spot = meta.get("regularMarketPrice")
    if raw_spot is None:
        raise FxDataFetchError(
            "Yahoo Finance response missing 'regularMarketPrice' in meta"
        )
    try:
        current_spot = float(raw_spot)
    except (TypeError, ValueError) as exc:
        raise FxDataFetchError(f"Invalid regularMarketPrice: {exc}") from exc
    if current_spot <= 0:
        raise FxDataFetchError(
            f"regularMarketPrice must be positive; got {current_spot}"
        )

    timestamps = result.get("timestamp") or []
    quote_list = (result.get("indicators") or {}).get("quote") or [{}]
    quote = quote_list[0] if quote_list else {}
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []

    windows: list[FxCompletedWindow] = []
    for i, ts in enumerate(timestamps):
        if ts is None:
            continue
        try:
            open_p = opens[i] if i < len(opens) else None
            high_p = highs[i] if i < len(highs) else None
            low_p = lows[i] if i < len(lows) else None
            close_p = closes[i] if i < len(closes) else None
        except (IndexError, TypeError):
            continue

        if any(v is None for v in (open_p, high_p, low_p, close_p)):
            continue

        try:
            win = _yahoo_bar_to_window(
                int(ts),
                float(open_p),  # type: ignore[arg-type]
                float(high_p),  # type: ignore[arg-type]
                float(low_p),  # type: ignore[arg-type]
                float(close_p),  # type: ignore[arg-type]
            )
        except (TypeError, ValueError):
            continue

        if win is None:
            continue

        # Include only windows that have ended by as_of_jst (completed windows).
        if win.window_end_jst <= as_of_jst:
            windows.append(win)

    # Sort oldest → newest (Yahoo Finance is usually pre-sorted, but be explicit).
    windows.sort(key=lambda w: w.window_start_jst)

    if len(windows) < 20:
        raise FxDataFetchError(
            f"Insufficient completed protocol windows: need ≥ 20, got {len(windows)} "
            f"(as_of_jst={as_of_jst.isoformat()}). "
            "The fetch range may need to be increased or the data source is lagging."
        )

    provenance = MarketDataProvenance(
        vendor="yahoo_finance",
        feed_name=f"chart/{_YF_SYMBOL}",
        price_type="mid",
        resolution="1d",
        timezone="UTC",
        retrieved_at_utc=datetime.now(timezone.utc),
    )

    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of_jst,
        current_spot=current_spot,
        completed_windows=tuple(windows),
        market_data_provenance=provenance,
    )


class YahooFinanceFxMarketDataProvider:
    """USDJPY market data provider using the Yahoo Finance chart API.

    No API key or secret required.  Uses only stdlib ``urllib``.

    Endpoint::

        https://query2.finance.yahoo.com/v8/finance/chart/USDJPY=X
            ?interval=1d&range=60d

    Normalization (see ``_yahoo_bar_to_window`` for full rules):

    - Each daily bar timestamp (Unix UTC seconds) is converted to a JST date.
    - Weekend bars (JST Saturday / Sunday) are discarded.
    - Canonical protocol window: ``[08:00 JST date D, 08:00 JST next business day)``.
    - Only windows whose end ≤ ``as_of_jst`` are returned (completed windows).
    - ``current_spot`` is taken from ``meta.regularMarketPrice``.

    In tests, stub this class by monkeypatching ``fetch_snapshot`` or by
    patching ``urllib.request.urlopen``; no real network calls are made in tests.
    """

    def __init__(self, *, timeout: int = 30) -> None:
        self._timeout = timeout

    def fetch_snapshot(self, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
        """Fetch and parse a USDJPY snapshot from the Yahoo Finance chart API.

        Raises
        ------
        FxDataFetchError
            On network failure, non-200 response, invalid JSON, or fewer than
            20 completed protocol windows in the response.
        """
        url = (
            f"{_YF_BASE_URL}/{_YF_SYMBOL}"
            f"?interval={_YF_INTERVAL}&range={_YF_RANGE}"
        )
        headers = {
            "Accept": "application/json",
            # Yahoo Finance blocks requests without a recognisable User-Agent.
            "User-Agent": "Mozilla/5.0 (compatible; ugh-quantamental/1.0)",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = resp.status
                body = resp.read()
        except urllib.error.HTTPError as exc:
            raise FxDataFetchError(
                f"HTTP {exc.code} from Yahoo Finance: {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise FxDataFetchError(
                f"Network error fetching Yahoo Finance: {exc.reason}"
            ) from exc

        if status != 200:
            raise FxDataFetchError(f"HTTP {status} from Yahoo Finance")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FxDataFetchError(
                f"Invalid JSON from Yahoo Finance: {exc}"
            ) from exc

        return _parse_yahoo_snapshot(payload, as_of_jst)


# ---------------------------------------------------------------------------
# Alpha Vantage FX_DAILY provider (free API key required)
# ---------------------------------------------------------------------------

_AV_BASE_URL = "https://www.alphavantage.co/query"
_AV_FROM_SYMBOL = "USD"
_AV_TO_SYMBOL = "JPY"
_AV_OUTPUT_SIZE = "compact"  # last ~100 data points; ensures >= 20 completed windows


def _av_date_to_window(
    date_str: str,
    open_p: float,
    high_p: float,
    low_p: float,
    close_p: float,
) -> FxCompletedWindow | None:
    """Convert one Alpha Vantage ``FX_DAILY`` date entry into a protocol ``FxCompletedWindow``.

    Normalization rule (deterministic)
    -----------------------------------
    Alpha Vantage ``FX_DAILY`` dates are UTC calendar date strings (``YYYY-MM-DD``).
    The protocol window is aligned to 08:00 JST, so the mapping is:

    1. Parse the date string as a UTC calendar date.
    2. Construct ``window_start_jst`` = 08:00 JST on that date.
    3. Discard dates that fall on Saturday or Sunday (JST calendar).
    4. Derive ``window_end_jst`` = ``next_as_of_jst(window_start_jst)``
       (08:00 JST on the next protocol business day, skipping weekends).
    5. If ``high_p < low_p`` (rare data artefact), swap them.
    6. Clamp ``open_p`` and ``close_p`` to ``[low_p, high_p]`` to tolerate
       minor floating-point drift in the source data.

    Returns ``None`` for weekend dates, invalid date strings, or entries that
    fail ``FxCompletedWindow`` construction.
    """
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return None

    window_start = datetime(d.year, d.month, d.day, 8, 0, 0, tzinfo=_JST)
    if not is_protocol_business_day(window_start):
        return None

    window_end = next_as_of_jst(window_start)

    # Guard against inverted high/low (very rare in FX source data).
    if high_p < low_p:
        high_p, low_p = low_p, high_p

    # Clamp open/close to [low, high] so the strict protocol validator accepts
    # otherwise-valid bars that have minor floating-point drift.
    open_p = max(low_p, min(high_p, open_p))
    close_p = max(low_p, min(high_p, close_p))

    try:
        return FxCompletedWindow(
            window_start_jst=window_start,
            window_end_jst=window_end,
            open_price=open_p,
            high_price=high_p,
            low_price=low_p,
            close_price=close_p,
        )
    except ValueError:
        return None


def _parse_av_snapshot(payload: dict, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
    """Parse an Alpha Vantage ``FX_DAILY`` response into an ``FxProtocolMarketSnapshot``.

    Parameters
    ----------
    payload:
        Parsed JSON from ``{_AV_BASE_URL}?function=FX_DAILY&from_symbol=USD
        &to_symbol=JPY&outputsize=compact&apikey=...``.
    as_of_jst:
        Canonical 08:00 JST timestamp from the protocol calendar.  Only windows
        whose ``window_end_jst <= as_of_jst`` are included (completed windows).

    Raises
    ------
    FxDataFetchError
        On unexpected response shape, empty time series (e.g. invalid API key or
        rate limit), or fewer than 20 completed protocol windows.
    """
    try:
        time_series: dict = payload.get("Time Series FX (Daily)") or {}
    except (AttributeError, TypeError) as exc:
        raise FxDataFetchError(
            f"Unexpected Alpha Vantage response shape: {exc}"
        ) from exc

    if not time_series:
        # Alpha Vantage returns rate-limit or auth errors as a 200 with a Note/Information key.
        note = payload.get("Note") or payload.get("Information") or ""
        raise FxDataFetchError(
            f"Alpha Vantage returned no time-series data. "
            f"API message: {note!r}"
        )

    windows: list[FxCompletedWindow] = []
    for date_str, entry in time_series.items():
        try:
            open_p = float(entry["1. open"])
            high_p = float(entry["2. high"])
            low_p = float(entry["3. low"])
            close_p = float(entry["4. close"])
        except (KeyError, TypeError, ValueError):
            continue

        win = _av_date_to_window(date_str, open_p, high_p, low_p, close_p)
        if win is None:
            continue

        # Include only windows that have ended by as_of_jst (completed windows).
        if win.window_end_jst <= as_of_jst:
            windows.append(win)

    windows.sort(key=lambda w: w.window_start_jst)

    if len(windows) < 20:
        raise FxDataFetchError(
            f"Insufficient completed protocol windows: need ≥ 20, got {len(windows)} "
            f"(as_of_jst={as_of_jst.isoformat()}). "
            "The fetch range may need to be increased or the data source is lagging."
        )

    # current_spot: close of the newest *completed* window.
    # Using max(time_series.keys()) would introduce look-ahead contamination during
    # backdated runs when newer bars exist beyond as_of_jst.
    current_spot = windows[-1].close_price

    provenance = MarketDataProvenance(
        vendor="alpha_vantage",
        feed_name=f"FX_DAILY/{_AV_FROM_SYMBOL}{_AV_TO_SYMBOL}",
        price_type="mid",
        resolution="1d",
        timezone="UTC",
        retrieved_at_utc=datetime.now(timezone.utc),
    )

    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of_jst,
        current_spot=current_spot,
        completed_windows=tuple(windows),
        market_data_provenance=provenance,
    )


class AlphaVantageXMarketDataProvider:
    """USDJPY market data provider using the Alpha Vantage FX_DAILY API.

    Requires a free API key (register at https://www.alphavantage.co).
    Uses only stdlib ``urllib``.

    Endpoint::

        https://www.alphavantage.co/query
            ?function=FX_DAILY&from_symbol=USD&to_symbol=JPY&outputsize=compact&apikey={key}

    Configure via:

    - constructor parameter ``api_key``
    - environment variable ``ALPHAVANTAGE_API_KEY``

    Normalization (see ``_av_date_to_window`` for full rules):

    - Each daily entry date (``YYYY-MM-DD`` UTC) is mapped to a JST protocol window.
    - Weekend dates (Saturday / Sunday) are discarded.
    - Canonical protocol window: ``[08:00 JST date D, 08:00 JST next business day)``.
    - Only windows whose end ≤ ``as_of_jst`` are returned (completed windows).
    - ``current_spot`` is taken from the close price of the most recent entry.

    In tests, stub this class by monkeypatching ``fetch_snapshot`` or by
    patching ``urllib.request.urlopen``; no real network calls are made in tests.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        self._api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY", "")
        self._timeout = timeout

    def fetch_snapshot(self, as_of_jst: datetime) -> FxProtocolMarketSnapshot:
        """Fetch and parse a USDJPY snapshot from the Alpha Vantage FX_DAILY API.

        Raises
        ------
        FxDataFetchError
            On missing API key, network failure, non-200 response, invalid JSON,
            rate-limit response, or fewer than 20 completed protocol windows.
        """
        if not self._api_key:
            raise FxDataFetchError(
                "ALPHAVANTAGE_API_KEY is not set. "
                "Obtain a free key at https://www.alphavantage.co and set the "
                "ALPHAVANTAGE_API_KEY environment variable or pass api_key= to the constructor."
            )

        url = (
            f"{_AV_BASE_URL}"
            f"?function=FX_DAILY"
            f"&from_symbol={_AV_FROM_SYMBOL}"
            f"&to_symbol={_AV_TO_SYMBOL}"
            f"&outputsize={_AV_OUTPUT_SIZE}"
            f"&apikey={self._api_key}"
        )
        headers = {"Accept": "application/json"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = resp.status
                body = resp.read()
        except urllib.error.HTTPError as exc:
            raise FxDataFetchError(
                f"HTTP {exc.code} from Alpha Vantage: {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise FxDataFetchError(
                f"Network error fetching Alpha Vantage: {exc.reason}"
            ) from exc

        if status != 200:
            raise FxDataFetchError(f"HTTP {status} from Alpha Vantage")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            logger.debug("Alpha Vantage returned non-JSON body: %s", exc)
            raise FxDataFetchError(
                f"Invalid JSON from Alpha Vantage: {exc}"
            ) from exc

        return _parse_av_snapshot(payload, as_of_jst)


# ---------------------------------------------------------------------------
# Custom-endpoint provider (optional; retained for users with private feeds)
# ---------------------------------------------------------------------------


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
            raise FxDataFetchError(
                "market_data_provenance.retrieved_at_utc is required but missing; "
                "injecting wall-clock time would break deterministic replay."
            )
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
    """Parse a custom-endpoint JSON payload into an ``FxProtocolMarketSnapshot``."""
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
    """Optional custom-endpoint provider using stdlib urllib.

    Use this when a private or internal data feed is available.
    If ``FX_DATA_URL`` is not set, use ``YahooFinanceFxMarketDataProvider``
    (the default public provider) instead.

    Configuration via environment variables:
    - ``FX_DATA_URL``: base URL for the data endpoint (required for this provider)
    - ``FX_DATA_AUTH_TOKEN``: optional bearer token

    The endpoint must return a JSON body conforming to the
    ``FxProtocolMarketSnapshot`` contract.
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
                "FX_DATA_URL is not set; cannot fetch market snapshot. "
                "Use YahooFinanceFxMarketDataProvider for the public default."
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
