"""Tests for fx_protocol.calendar — deterministic protocol calendar helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.calendar import (
    current_as_of_jst,
    is_protocol_business_day,
    next_as_of_jst,
    next_protocol_business_day,
    prev_as_of_jst,
)

JST = ZoneInfo("Asia/Tokyo")
UTC = timezone.utc

# Known calendar dates (2026-03-09 = Monday, 2026-03-14 = Saturday)
_MON = datetime(2026, 3, 9, 12, 0, 0, tzinfo=JST)   # Monday
_TUE = datetime(2026, 3, 10, 8, 0, 0, tzinfo=JST)   # Tuesday
_WED = datetime(2026, 3, 11, 0, 0, 0, tzinfo=JST)   # Wednesday
_THU = datetime(2026, 3, 12, 15, 30, 0, tzinfo=JST) # Thursday
_FRI = datetime(2026, 3, 13, 23, 59, 0, tzinfo=JST) # Friday
_SAT = datetime(2026, 3, 14, 8, 0, 0, tzinfo=JST)   # Saturday
_SUN = datetime(2026, 3, 15, 8, 0, 0, tzinfo=JST)   # Sunday


# ---------------------------------------------------------------------------
# is_protocol_business_day
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dt", [_MON, _TUE, _WED, _THU, _FRI])
def test_weekday_is_business_day(dt: datetime) -> None:
    assert is_protocol_business_day(dt) is True


@pytest.mark.parametrize("dt", [_SAT, _SUN])
def test_weekend_is_not_business_day(dt: datetime) -> None:
    assert is_protocol_business_day(dt) is False


def test_naive_dt_treated_as_jst() -> None:
    # 2026-03-09 is Monday — naive datetime treated as JST
    naive_mon = datetime(2026, 3, 9, 12, 0, 0)
    assert is_protocol_business_day(naive_mon) is True


def test_utc_aware_dt_converts_correctly() -> None:
    # UTC 2026-03-09 23:00 = JST 2026-03-10 08:00 (Tuesday) — business day
    utc_dt = datetime(2026, 3, 9, 23, 0, 0, tzinfo=UTC)
    assert is_protocol_business_day(utc_dt) is True


def test_utc_saturday_converts_to_jst_saturday() -> None:
    # UTC 2026-03-14 00:00 = JST 2026-03-14 09:00 (Saturday)
    utc_dt = datetime(2026, 3, 14, 0, 0, 0, tzinfo=UTC)
    assert is_protocol_business_day(utc_dt) is False


# ---------------------------------------------------------------------------
# next_protocol_business_day
# ---------------------------------------------------------------------------


def test_next_business_day_from_monday_is_tuesday() -> None:
    result = next_protocol_business_day(_MON)
    assert result.weekday() == 1  # Tuesday


def test_next_business_day_from_friday_is_monday() -> None:
    result = next_protocol_business_day(_FRI)
    assert result.weekday() == 0  # Monday


def test_next_business_day_from_saturday_is_monday() -> None:
    result = next_protocol_business_day(_SAT)
    assert result.weekday() == 0  # Monday


def test_next_business_day_from_sunday_is_monday() -> None:
    result = next_protocol_business_day(_SUN)
    assert result.weekday() == 0  # Monday


def test_next_business_day_returns_midnight() -> None:
    result = next_protocol_business_day(_MON)
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0
    assert result.microsecond == 0


def test_next_business_day_is_strictly_after_input() -> None:
    """Even if input is already a business day, result must be the NEXT one."""
    # Tuesday input → result must be Wednesday
    result = next_protocol_business_day(_TUE)
    assert result.weekday() == 2  # Wednesday
    assert result.date() > _TUE.date()


def test_next_business_day_preserves_timezone() -> None:
    result = next_protocol_business_day(_MON)
    assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# current_as_of_jst
# ---------------------------------------------------------------------------


def test_current_as_of_jst_on_monday() -> None:
    result = current_as_of_jst(_MON)
    assert result.hour == 8
    assert result.minute == 0
    assert result.second == 0
    assert result.microsecond == 0


def test_current_as_of_jst_date_matches_input_date() -> None:
    result = current_as_of_jst(_THU)
    assert result.year == _THU.year
    assert result.month == _THU.month
    assert result.day == _THU.day


def test_current_as_of_jst_is_timezone_aware() -> None:
    result = current_as_of_jst(_MON)
    assert result.tzinfo is not None


def test_current_as_of_jst_from_utc_input() -> None:
    # UTC 2026-03-09 00:00 = JST 2026-03-09 09:00 (Monday)
    utc_dt = datetime(2026, 3, 9, 0, 0, 0, tzinfo=UTC)
    result = current_as_of_jst(utc_dt)
    # Result should be 08:00 JST on 2026-03-09
    assert result.hour == 8
    assert result.day == 9
    assert result.month == 3


def test_current_as_of_jst_naive_treated_as_jst() -> None:
    naive_dt = datetime(2026, 3, 11, 15, 30, 0)  # Wednesday afternoon
    result = current_as_of_jst(naive_dt)
    assert result.hour == 8
    assert result.day == 11


# ---------------------------------------------------------------------------
# next_as_of_jst
# ---------------------------------------------------------------------------


def test_next_as_of_jst_from_monday_is_tuesday_at_0800() -> None:
    result = next_as_of_jst(_MON)
    assert result.weekday() == 1  # Tuesday
    assert result.hour == 8
    assert result.minute == 0


def test_next_as_of_jst_from_friday_is_monday_at_0800() -> None:
    result = next_as_of_jst(_FRI)
    assert result.weekday() == 0  # Monday
    assert result.hour == 8


def test_next_as_of_jst_from_saturday_is_monday_at_0800() -> None:
    result = next_as_of_jst(_SAT)
    assert result.weekday() == 0  # Monday
    assert result.hour == 8


def test_next_as_of_jst_is_after_input() -> None:
    result = next_as_of_jst(_TUE)
    assert result > _TUE


def test_next_as_of_jst_timezone_aware() -> None:
    result = next_as_of_jst(_WED)
    assert result.tzinfo is not None


def test_current_and_next_as_of_are_one_business_day_apart() -> None:
    """next_as_of should equal next_protocol_business_day of current_as_of."""
    current = current_as_of_jst(_MON)
    expected_next = next_protocol_business_day(current).replace(hour=8)
    actual_next = next_as_of_jst(_MON)
    assert actual_next == expected_next


# ---------------------------------------------------------------------------
# prev_as_of_jst
# ---------------------------------------------------------------------------


def test_prev_as_of_jst_from_tuesday_is_monday_at_0800() -> None:
    result = prev_as_of_jst(_TUE)
    assert result == datetime(2026, 3, 9, 8, 0, 0, tzinfo=JST)  # Monday


def test_prev_as_of_jst_from_monday_is_friday_at_0800() -> None:
    result = prev_as_of_jst(_MON)
    assert result.weekday() == 4  # Friday
    assert result.hour == 8


def test_prev_as_of_jst_from_saturday_is_friday_at_0800() -> None:
    result = prev_as_of_jst(_SAT)
    assert result.weekday() == 4  # Friday
    assert result.hour == 8


def test_prev_as_of_jst_from_sunday_is_friday_at_0800() -> None:
    result = prev_as_of_jst(_SUN)
    assert result.weekday() == 4  # Friday
    assert result.hour == 8


def test_prev_as_of_jst_is_before_input() -> None:
    result = prev_as_of_jst(_WED)
    assert result < _WED


def test_prev_as_of_jst_timezone_aware() -> None:
    result = prev_as_of_jst(_THU)
    assert result.tzinfo is not None


def test_prev_and_next_as_of_jst_are_inverse() -> None:
    """prev_as_of_jst(next_as_of_jst(dt)) == current_as_of_jst(dt) for weekdays."""
    current = current_as_of_jst(_WED)
    assert prev_as_of_jst(next_as_of_jst(_WED)) == current
