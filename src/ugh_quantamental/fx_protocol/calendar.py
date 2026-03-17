"""Deterministic protocol calendar helpers for the FX Daily Protocol v1."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Canonical as-of hour in the protocol timezone.
_AS_OF_HOUR: int = 8

# ISO weekday values for Saturday and Sunday.
_WEEKEND: frozenset[int] = frozenset({5, 6})  # Monday=0 ... Sunday=6


def _to_local(dt: datetime, tz: str) -> datetime:
    """Convert *dt* to *tz*-aware datetime; naive inputs are assumed to carry that tz."""
    zone = ZoneInfo(tz)
    if dt.tzinfo is not None:
        return dt.astimezone(zone)
    return dt.replace(tzinfo=zone)


def is_protocol_business_day(dt: datetime, tz: str = "Asia/Tokyo") -> bool:
    """Return ``True`` iff the date of *dt* in *tz* falls on Monday–Friday.

    Phase 2 v1 business days are weekdays only.  Holidays are not excluded.

    Parameters
    ----------
    dt:
        Reference datetime.  Timezone-aware values are converted to *tz*;
        naive values are treated as already in *tz*.
    tz:
        IANA timezone name.  Defaults to ``"Asia/Tokyo"`` (JST).
    """
    local_dt = _to_local(dt, tz)
    return local_dt.weekday() not in _WEEKEND


def next_protocol_business_day(dt: datetime, tz: str = "Asia/Tokyo") -> datetime:
    """Return midnight of the next Monday–Friday business day after *dt* (in *tz*).

    "Next" means strictly after the date of *dt*: if *dt* is itself a business day
    the returned value is the following business day, not the same day.

    Parameters
    ----------
    dt:
        Reference datetime.  Timezone-aware values are converted to *tz*;
        naive values are treated as already in *tz*.
    tz:
        IANA timezone name.  Defaults to ``"Asia/Tokyo"`` (JST).

    Returns
    -------
    datetime
        Midnight (00:00:00) of the next business day in *tz*, timezone-aware.
    """
    local_dt = _to_local(dt, tz)
    # Start from the beginning of the day AFTER the current date.
    candidate = local_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    while candidate.weekday() in _WEEKEND:
        candidate += timedelta(days=1)
    return candidate


def current_as_of_jst(dt: datetime) -> datetime:
    """Return 08:00 JST on the date of *dt* converted to JST.

    This is the canonical ``as_of_jst`` timestamp for the forecast day
    whose calendar date matches *dt* in Asia/Tokyo time.

    Parameters
    ----------
    dt:
        Reference datetime.  Timezone-aware values are converted to JST;
        naive values are treated as already JST.

    Returns
    -------
    datetime
        A timezone-aware datetime at 08:00 JST on the same calendar date as *dt*.
    """
    local_dt = _to_local(dt, "Asia/Tokyo")
    return local_dt.replace(hour=_AS_OF_HOUR, minute=0, second=0, microsecond=0)


def next_as_of_jst(dt: datetime) -> datetime:
    """Return 08:00 JST on the next protocol business day after *dt* in JST.

    This is the canonical ``as_of_jst`` for the *next* forecast window relative
    to the window that starts on the date of *dt*.

    Parameters
    ----------
    dt:
        Reference datetime.  Timezone-aware values are converted to JST;
        naive values are treated as already JST.

    Returns
    -------
    datetime
        A timezone-aware datetime at 08:00 JST on the next business day.
    """
    next_day = next_protocol_business_day(dt, tz="Asia/Tokyo")
    return next_day.replace(hour=_AS_OF_HOUR, minute=0, second=0, microsecond=0)


def prev_as_of_jst(dt: datetime) -> datetime:
    """Return 08:00 JST on the previous protocol business day before *dt* in JST.

    "Previous" means strictly before the date of *dt*: if *dt* is itself a
    business day the returned value is the preceding business day, not the same day.
    Weekends are skipped (Saturday → Friday, Monday → Friday).

    Parameters
    ----------
    dt:
        Reference datetime.  Timezone-aware values are converted to JST;
        naive values are treated as already JST.

    Returns
    -------
    datetime
        A timezone-aware datetime at 08:00 JST on the previous business day.
    """
    local_dt = _to_local(dt, "Asia/Tokyo")
    candidate = local_dt.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    while candidate.weekday() in _WEEKEND:
        candidate -= timedelta(days=1)
    return candidate.replace(hour=_AS_OF_HOUR, minute=0, second=0, microsecond=0)
