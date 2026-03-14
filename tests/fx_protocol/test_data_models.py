"""Tests for FxCompletedWindow and FxProtocolMarketSnapshot (data_models.py)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, EventTag, MarketDataProvenance

_JST = ZoneInfo("Asia/Tokyo")


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="test_feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
    )


def _window(
    start: datetime,
    end: datetime,
    open_p: float = 150.0,
    high_p: float = 151.0,
    low_p: float = 149.0,
    close_p: float = 150.5,
    event_tags: tuple[EventTag, ...] = (),
) -> FxCompletedWindow:
    return FxCompletedWindow(
        window_start_jst=start,
        window_end_jst=end,
        open_price=open_p,
        high_price=high_p,
        low_price=low_p,
        close_price=close_p,
        event_tags=event_tags,
    )


def _mon_window(year: int, month: int, day: int) -> FxCompletedWindow:
    """Build a Monday→Tuesday window."""
    start = datetime(year, month, day, 8, 0, 0, tzinfo=_JST)
    end = datetime(year, month, day + 1, 8, 0, 0, tzinfo=_JST)
    return _window(start, end)


# ---------------------------------------------------------------------------
# FxCompletedWindow
# ---------------------------------------------------------------------------


class TestFxCompletedWindow:
    def test_valid_window(self) -> None:
        win = _window(
            start=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),  # Monday
            end=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),   # Tuesday
        )
        assert win.open_price == 150.0

    def test_window_with_event_tags(self) -> None:
        win = _window(
            start=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
            end=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            event_tags=(EventTag.fomc,),
        )
        assert EventTag.fomc in win.event_tags

    def test_non_business_day_start_rejected(self) -> None:
        with pytest.raises(ValueError, match="business day"):
            _window(
                start=datetime(2026, 3, 7, 8, 0, 0, tzinfo=_JST),  # Saturday
                end=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),    # Monday
            )

    def test_wrong_hour_rejected(self) -> None:
        with pytest.raises(ValueError, match="08:00:00"):
            _window(
                start=datetime(2026, 3, 9, 9, 0, 0, tzinfo=_JST),  # wrong hour
                end=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            )

    def test_high_below_low_rejected(self) -> None:
        with pytest.raises(ValueError, match="high_price must be >= low_price"):
            FxCompletedWindow(
                window_start_jst=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
                window_end_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                open_price=150.0,
                high_price=148.0,
                low_price=149.0,
                close_price=150.0,
            )

    def test_open_outside_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="open_price must be within"):
            FxCompletedWindow(
                window_start_jst=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
                window_end_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                open_price=152.0,  # above high
                high_price=151.0,
                low_price=149.0,
                close_price=150.0,
            )

    def test_non_positive_price_rejected(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            FxCompletedWindow(
                window_start_jst=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
                window_end_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                open_price=0.0,
                high_price=1.0,
                low_price=0.0,
                close_price=0.5,
            )


# ---------------------------------------------------------------------------
# FxProtocolMarketSnapshot
# ---------------------------------------------------------------------------


def _build_20_windows() -> tuple[FxCompletedWindow, ...]:
    """Build 20 consecutive Mon→Tue windows starting from 2026-03-02."""
    windows = []
    # Build starting Mon 2026-03-02 and advancing by 1 week (7 days) per window.
    # Actually we need consecutive business-day windows.
    # Mon 2026-02-02 → Tue, Tue → Wed, ... skip weekends.
    # Use week of 2026-01-05 (Mon) to get 20 consecutive windows.
    from datetime import timedelta

    # Start: Monday 2026-01-05
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < 20:
        # Skip Fri→next Mon (iso weekday 5 = Friday, gaps to Monday)
        if start.isoweekday() == 6 or start.isoweekday() == 7:
            start += timedelta(days=1)
            continue
        # end is next business day
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        windows.append(FxCompletedWindow(
            window_start_jst=start,
            window_end_jst=end,
            open_price=150.0,
            high_price=151.0,
            low_price=149.0,
            close_price=150.5,
        ))
        start = end
        count += 1
    return tuple(windows)


class TestFxProtocolMarketSnapshot:
    def test_valid_snapshot(self) -> None:
        wins = _build_20_windows()
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) == 20

    def test_fewer_than_20_windows_rejected(self) -> None:
        wins = _build_20_windows()[:19]
        with pytest.raises(ValueError):
            FxProtocolMarketSnapshot(
                pair=CurrencyPair.USDJPY,
                as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                current_spot=150.0,
                completed_windows=wins,
                market_data_provenance=_provenance(),
            )

    def test_windows_must_be_ordered_oldest_newest(self) -> None:
        wins = _build_20_windows()
        # Reverse the list to make it newest→oldest.
        reversed_wins = wins[::-1]
        with pytest.raises(ValueError, match="oldest.*newest"):
            FxProtocolMarketSnapshot(
                pair=CurrencyPair.USDJPY,
                as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                current_spot=150.0,
                completed_windows=reversed_wins,
                market_data_provenance=_provenance(),
            )

    def test_non_positive_spot_rejected(self) -> None:
        wins = _build_20_windows()
        with pytest.raises(ValueError, match="positive"):
            FxProtocolMarketSnapshot(
                pair=CurrencyPair.USDJPY,
                as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                current_spot=0.0,
                completed_windows=wins,
                market_data_provenance=_provenance(),
            )

    def test_as_of_normalized_to_jst(self) -> None:
        wins = _build_20_windows()
        # Supply as_of_jst as UTC-aware datetime (equivalent of 08:00 JST).
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=datetime(2026, 3, 9, 23, 0, 0, tzinfo=timezone.utc),  # = 08:00 JST next day
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        assert snap.as_of_jst.tzinfo is not None
        assert snap.as_of_jst.tzname() in ("JST", "+09:00")
