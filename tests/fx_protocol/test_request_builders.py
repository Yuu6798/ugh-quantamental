"""Tests for request_builders.py."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance
from ugh_quantamental.fx_protocol.request_builders import (
    build_baseline_context,
    build_daily_outcome_request,
    previous_window_matches,
)

_JST = ZoneInfo("Asia/Tokyo")


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
    )


def _build_windows(n: int, base_close: float = 150.0) -> tuple[FxCompletedWindow, ...]:
    """Build n consecutive Mon→next-business-day windows."""
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)  # Monday
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        close = base_close + count * 0.1  # slightly increasing closes
        # open is always exactly the midpoint of [low, high] so it passes validation.
        low = close - 1.0
        high = close + 1.0
        windows.append(FxCompletedWindow(
            window_start_jst=start,
            window_end_jst=end,
            open_price=close,  # open == close is valid (flat day)
            high_price=high,
            low_price=low,
            close_price=close,
        ))
        start = end
        count += 1
    return tuple(windows)


def _snapshot(
    n_windows: int = 20,
    current_spot: float = 150.0,
    as_of_offset_days: int = 0,
) -> FxProtocolMarketSnapshot:
    wins = _build_windows(n_windows)
    as_of = wins[-1].window_end_jst if as_of_offset_days == 0 else wins[-1].window_end_jst + timedelta(
        days=as_of_offset_days
    )
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of,
        current_spot=current_spot,
        completed_windows=wins,
        market_data_provenance=_provenance(),
    )


# ---------------------------------------------------------------------------
# build_baseline_context
# ---------------------------------------------------------------------------


class TestBuildBaselineContext:
    def test_basic_derivation(self) -> None:
        snap = _snapshot(20, current_spot=150.0)
        ctx = build_baseline_context(snap)
        assert ctx.current_spot == 150.0
        assert ctx.warmup_window_count == 20
        assert ctx.sma5 is not None
        assert ctx.sma20 is not None
        assert ctx.trailing_mean_range_price > 0
        assert ctx.trailing_mean_abs_close_change_bp >= 0

    def test_previous_close_change_bp_from_newest_window(self) -> None:
        wins = _build_windows(20)
        newest = wins[-1]
        expected_bp = (newest.close_price - newest.open_price) / newest.open_price * 10_000
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=newest.window_end_jst,
            current_spot=newest.close_price,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        ctx = build_baseline_context(snap)
        assert abs(ctx.previous_close_change_bp - expected_bp) < 1e-6

    def test_sma5_uses_last_5_windows(self) -> None:
        wins = _build_windows(20)
        last5_closes = [w.close_price for w in wins[-5:]]
        expected_sma5 = sum(last5_closes) / 5
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        ctx = build_baseline_context(snap)
        assert abs(ctx.sma5 - expected_sma5) < 1e-9

    def test_sma20_uses_last_20_windows(self) -> None:
        wins = _build_windows(25)
        trailing = wins[-20:]
        expected_sma20 = sum(w.close_price for w in trailing) / 20
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        ctx = build_baseline_context(snap)
        assert abs(ctx.sma20 - expected_sma20) < 1e-9

    def test_fewer_than_20_windows_raises(self) -> None:
        # FxProtocolMarketSnapshot enforces min_length=20; we verify this here.
        wins = _build_windows(19)
        with pytest.raises(ValueError):
            FxProtocolMarketSnapshot(
                pair=CurrencyPair.USDJPY,
                as_of_jst=wins[-1].window_end_jst,
                current_spot=150.0,
                completed_windows=wins,
                market_data_provenance=_provenance(),
            )

    def test_warmup_window_count_equals_window_count(self) -> None:
        wins = _build_windows(25)
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        ctx = build_baseline_context(snap)
        assert ctx.warmup_window_count == 25


# ---------------------------------------------------------------------------
# build_daily_outcome_request
# ---------------------------------------------------------------------------


class TestBuildDailyOutcomeRequest:
    def test_uses_newest_window(self) -> None:
        snap = _snapshot(20)
        newest = snap.completed_windows[-1]
        req = build_daily_outcome_request(snap, schema_version="v1", protocol_version="v1")
        assert req.window_start_jst == newest.window_start_jst
        assert req.window_end_jst == newest.window_end_jst
        assert req.realized_open == newest.open_price
        assert req.realized_close == newest.close_price

    def test_schema_protocol_version_passed(self) -> None:
        snap = _snapshot(20)
        req = build_daily_outcome_request(
            snap, schema_version="v2", protocol_version="v3"
        )
        assert req.schema_version == "v2"
        assert req.protocol_version == "v3"


# ---------------------------------------------------------------------------
# previous_window_matches
# ---------------------------------------------------------------------------


class TestBuildDailyForecastRequest:
    """Tests for build_daily_forecast_request."""

    def _make_ugh_request(self) -> object:
        """Build a minimal placeholder FullWorkflowRequest."""
        from ugh_quantamental.fx_protocol.automation import _make_default_ugh_request

        return _make_default_ugh_request("test-ref")

    def test_returns_forecast_workflow_request(self) -> None:
        from ugh_quantamental.fx_protocol.forecast_models import DailyForecastWorkflowRequest
        from ugh_quantamental.fx_protocol.request_builders import build_daily_forecast_request

        snap = _snapshot(20)
        req = build_daily_forecast_request(
            snap,
            ugh_request=self._make_ugh_request(),
            input_snapshot_ref="test-ref",
            theory_version="v1",
            engine_version="v1",
            schema_version="v1",
            protocol_version="v1",
        )
        assert isinstance(req, DailyForecastWorkflowRequest)
        assert req.pair == snap.pair
        assert req.as_of_jst == snap.as_of_jst

    def test_version_fields_passed_through(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import build_daily_forecast_request

        snap = _snapshot(20)
        req = build_daily_forecast_request(
            snap,
            ugh_request=self._make_ugh_request(),
            input_snapshot_ref="ref-x",
            theory_version="t2",
            engine_version="e3",
            schema_version="s4",
            protocol_version="p5",
        )
        assert req.theory_version == "t2"
        assert req.engine_version == "e3"
        assert req.schema_version == "s4"
        assert req.protocol_version == "p5"
        assert req.input_snapshot_ref == "ref-x"

    def test_baseline_context_derived(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import build_daily_forecast_request

        snap = _snapshot(25)
        req = build_daily_forecast_request(
            snap,
            ugh_request=self._make_ugh_request(),
            input_snapshot_ref="r",
            theory_version="v1",
            engine_version="v1",
            schema_version="v1",
            protocol_version="v1",
        )
        # BaselineContext must be populated.
        assert req.baseline_context.warmup_window_count == 25
        assert req.baseline_context.sma20 > 0
        assert req.baseline_context.sma5 > 0


class TestPreviousWindowMatches:
    def test_matches_when_newest_end_equals_as_of(self) -> None:
        wins = _build_windows(20)
        # as_of_jst == wins[-1].window_end_jst → matches
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=wins[-1].window_end_jst,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        assert previous_window_matches(snap) is True

    def test_no_match_when_as_of_is_future(self) -> None:
        wins = _build_windows(20)
        # as_of_jst is 1 day after the newest window end — no match
        future_as_of = wins[-1].window_end_jst + timedelta(days=7)
        snap = FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=future_as_of,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=_provenance(),
        )
        assert previous_window_matches(snap) is False
