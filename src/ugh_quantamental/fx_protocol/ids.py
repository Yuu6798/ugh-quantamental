"""Deterministic ID-generation helpers for the FX Daily Protocol v1."""

from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.models import CurrencyPair, StrategyKind

# Canonical timezone for all ID-generation hashing.
_JST: ZoneInfo = ZoneInfo("Asia/Tokyo")

# Separator used between key components before hashing.
_SEP: str = "|"

# Number of hex characters retained from the SHA-256 digest.
_HASH_LENGTH: int = 16


def _digest(*parts: str) -> str:
    """Return the first *_HASH_LENGTH* hex characters of SHA-256(*parts* joined by ``|``)."""
    payload = _SEP.join(parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:_HASH_LENGTH]


def _fmt_dt(dt: datetime) -> str:
    """Normalize *dt* to JST then format as ``YYYYMMDDTHHmmSS``.

    All datetime inputs are converted to JST before formatting so that the same
    logical instant always produces the same string regardless of the caller's
    timezone representation (e.g. ``2026-03-10 08:00+09:00`` and
    ``2026-03-09 23:00+00:00`` both yield ``"20260310T080000"``).

    Naive datetimes are treated as already in JST.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(_JST)
    else:
        dt = dt.replace(tzinfo=_JST)
    return dt.strftime("%Y%m%dT%H%M%S")


def make_forecast_batch_id(
    pair: CurrencyPair,
    as_of_jst: datetime,
    protocol_version: str,
) -> str:
    """Return a deterministic forecast-batch ID.

    The ID encodes pair, as-of time, and protocol version so that it is
    human-readable and globally unique for valid (pair, as_of_jst, protocol_version)
    combinations.

    Format::

        fb_{pair}_{as_of_yyyymmddTHHMMSS}_{protocol_version}_{hash16}

    Parameters
    ----------
    pair:
        Currency pair (e.g. ``CurrencyPair.USDJPY``).
    as_of_jst:
        Canonical as-of datetime in JST (must be 08:00 JST on a business day).
    protocol_version:
        Protocol version string (e.g. ``"v1"``).
    """
    as_of_str = _fmt_dt(as_of_jst)
    hash_part = _digest(pair.value, as_of_str, protocol_version)
    return f"fb_{pair.value}_{as_of_str}_{protocol_version}_{hash_part}"


def make_forecast_id(
    pair: CurrencyPair,
    as_of_jst: datetime,
    protocol_version: str,
    strategy_kind: StrategyKind,
) -> str:
    """Return a deterministic forecast ID.

    One forecast ID is produced per ``(pair, as_of_jst, strategy_kind, protocol_version)``
    combination, ensuring no duplicate IDs within a batch.

    Format::

        fc_{pair}_{as_of_yyyymmddTHHMMSS}_{protocol_version}_{strategy}_{hash16}

    Parameters
    ----------
    pair:
        Currency pair.
    as_of_jst:
        Canonical as-of datetime in JST.
    protocol_version:
        Protocol version string.
    strategy_kind:
        Strategy used to produce this forecast.
    """
    as_of_str = _fmt_dt(as_of_jst)
    hash_part = _digest(pair.value, as_of_str, protocol_version, strategy_kind.value)
    return f"fc_{pair.value}_{as_of_str}_{protocol_version}_{strategy_kind.value}_{hash_part}"


def make_outcome_id(
    pair: CurrencyPair,
    window_start_jst: datetime,
    window_end_jst: datetime,
    schema_version: str,
) -> str:
    """Return a deterministic outcome ID.

    One outcome ID is produced per ``(pair, window_start_jst, window_end_jst, schema_version)``
    combination, making outcome records content-addressed and idempotent.

    Format::

        oc_{pair}_{start_yyyymmddTHHMMSS}_{end_yyyymmddTHHMMSS}_{schema_version}_{hash16}

    Parameters
    ----------
    pair:
        Currency pair.
    window_start_jst:
        Window start datetime in JST (equals ``as_of_jst`` of the corresponding forecast).
    window_end_jst:
        Window end datetime in JST (equals ``as_of_jst`` of the next business day).
    schema_version:
        Schema version string (e.g. ``"v1"``).
    """
    start_str = _fmt_dt(window_start_jst)
    end_str = _fmt_dt(window_end_jst)
    hash_part = _digest(pair.value, start_str, end_str, schema_version)
    return f"oc_{pair.value}_{start_str}_{end_str}_{schema_version}_{hash_part}"


def make_evaluation_id(forecast_id: str, schema_version: str) -> str:
    """Return a deterministic evaluation ID.

    One evaluation ID is produced per ``(forecast_id, schema_version)`` combination.
    Since ``forecast_id`` already encodes pair, as-of, strategy, and protocol version,
    no additional fields are needed.

    Format::

        ev_{forecast_id}_{schema_version}_{hash16}

    Parameters
    ----------
    forecast_id:
        The forecast ID produced by :func:`make_forecast_id`.
    schema_version:
        Schema version string.
    """
    hash_part = _digest(forecast_id, schema_version)
    return f"ev_{forecast_id}_{schema_version}_{hash_part}"
