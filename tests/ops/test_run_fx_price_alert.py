"""Unit tests for ``scripts/run_fx_price_alert.py``'s pure decision logic.

``run_fx_price_alert`` is intentionally independent of ``ugh_quantamental``
(stdlib only) so it keeps working even if ``fx_protocol`` is broken — see
``docs/specs/fx_price_alert_v1.md``. It is loaded here by file path (it is a
script, not a package module) rather than imported normally, and none of
these tests touch the network or the filesystem beyond the module load
itself.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_fx_price_alert.py"
_spec = importlib.util.spec_from_file_location("run_fx_price_alert", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
fxa = importlib.util.module_from_spec(_spec)
sys.modules["run_fx_price_alert"] = fxa
_spec.loader.exec_module(fxa)

JST = fxa.JST


def _jst(y, m, d, hh=9, mm=0, ss=0) -> datetime:
    return datetime(y, m, d, hh, mm, ss, tzinfo=JST)


def _bar(low: float, high: float, *, open_=None, close=None, ts=0) -> "fxa.Bar":
    return fxa.Bar(
        ts_utc=ts,
        open=open_ if open_ is not None else low,
        high=high,
        low=low,
        close=close if close is not None else high,
    )


def _forecast(as_of: date, spot: float, batch_id: str | None = "fb_test") -> "fxa.ForecastMeta":
    return fxa.ForecastMeta(as_of_jst=as_of, current_spot=spot, forecast_batch_id=batch_id)


# ---------------------------------------------------------------------------
# parse_lines_env
# ---------------------------------------------------------------------------


class TestParseLinesEnv:
    def test_default_when_unset(self) -> None:
        lines = fxa.parse_lines_env(None)
        assert [line.raw for line in lines] == ["161.50"]
        assert lines[0].value == pytest.approx(161.50)

    def test_default_when_blank(self) -> None:
        lines = fxa.parse_lines_env("   ")
        assert [line.raw for line in lines] == ["161.50"]

    def test_custom_single_line(self) -> None:
        lines = fxa.parse_lines_env("160.00")
        assert [line.raw for line in lines] == ["160.00"]
        assert lines[0].value == pytest.approx(160.00)

    def test_custom_multiple_lines_with_whitespace(self) -> None:
        lines = fxa.parse_lines_env(" 161.50 , 163.00 ,, 159.75 ")
        assert [line.raw for line in lines] == ["161.50", "163.00", "159.75"]

    def test_line_key_uses_raw_token(self) -> None:
        lines = fxa.parse_lines_env("161.5")
        assert lines[0].key == "line:161.5"


# ---------------------------------------------------------------------------
# Business-day / cutoff rules (simplified JST-weekend design)
# ---------------------------------------------------------------------------


class TestBusinessDayRules:
    def test_weekday_is_business_day(self) -> None:
        assert fxa.is_business_day_jst(date(2026, 8, 31)) is True  # Monday

    def test_saturday_is_not_business_day(self) -> None:
        assert fxa.is_business_day_jst(date(2026, 8, 29)) is False  # Saturday

    def test_sunday_is_not_business_day(self) -> None:
        assert fxa.is_business_day_jst(date(2026, 8, 30)) is False  # Sunday

    def test_target_date_on_business_day_is_today(self) -> None:
        now = _jst(2026, 8, 28, 10, 0)  # Friday
        assert fxa.target_business_date_jst(now) == date(2026, 8, 28)

    def test_target_date_on_saturday_is_friday(self) -> None:
        now = _jst(2026, 8, 29, 10, 0)  # Saturday
        assert fxa.target_business_date_jst(now) == date(2026, 8, 28)

    def test_target_date_on_sunday_is_friday(self) -> None:
        now = _jst(2026, 8, 30, 10, 0)  # Sunday
        assert fxa.target_business_date_jst(now) == date(2026, 8, 28)

    def test_cutoff_not_reached_just_before_22_00_jst(self) -> None:
        now = _jst(2026, 8, 28, 21, 59, 59)  # Friday
        assert fxa.gap_cutoff_reached(now) is False

    def test_cutoff_reached_exactly_at_22_00_jst(self) -> None:
        now = _jst(2026, 8, 28, 22, 0, 0)  # Friday
        assert fxa.gap_cutoff_reached(now) is True

    def test_cutoff_reached_just_after_22_00_jst(self) -> None:
        now = _jst(2026, 8, 28, 22, 0, 1)  # Friday
        assert fxa.gap_cutoff_reached(now) is True

    def test_cutoff_always_reached_on_weekend(self) -> None:
        now = _jst(2026, 8, 29, 6, 0, 0)  # Saturday morning
        assert fxa.gap_cutoff_reached(now) is True


# ---------------------------------------------------------------------------
# evaluate_move (AC a)
# ---------------------------------------------------------------------------


class TestEvaluateMove:
    """FIX 10: threshold_bp is TRUE basis points of the baseline spot
    (|diff| / baseline * 10_000), matching FX_ALERT_MOVE_BP's name — not
    1/100-yen "pips" (|diff| * 100, a fixed-point count independent of the
    baseline's magnitude)."""

    def test_below_threshold_inactive(self) -> None:
        # diff=0.30 @ baseline 150.30 -> ~19.96 bp < 60 bp.
        active, _ = fxa.evaluate_move(150.00, 150.30, threshold_bp=60.0)
        assert active is False

    def test_at_threshold_active(self) -> None:
        # diff=0.90 @ baseline 150.00 -> exactly 60.0 bp.
        active, _ = fxa.evaluate_move(150.90, 150.00, threshold_bp=60.0)
        assert active is True

    def test_above_threshold_active(self) -> None:
        # diff=3.21 @ baseline 150.00 -> 214.0 bp >= 60 bp.
        active, _ = fxa.evaluate_move(153.21, 150.00, threshold_bp=60.0)
        assert active is True

    def test_direction_agnostic(self) -> None:
        # diff=-1.00 @ baseline 150.00 -> ~66.67 bp >= 60 bp regardless of sign.
        active, _ = fxa.evaluate_move(149.00, 150.00, threshold_bp=60.0)
        assert active is True

    def test_baseline_is_never_a_completed_ohlc_close(self) -> None:
        """The baseline argument is documented as forecast current_spot, not
        a rebuilt OHLC close — this test pins the formula's contract: it is
        a plain live_spot-vs-baseline diff (in true bp) with no OHLC
        awareness at all."""
        active, detail = fxa.evaluate_move(151.00, 150.00, threshold_bp=60.0)
        assert active is True
        assert "150.00" in detail
        assert "151.00" in detail

    def test_bp_formula_is_relative_to_baseline_not_fixed_pip_count(self) -> None:
        """A 0.90 move is >= threshold near baseline 150 but NOT near a much
        larger baseline (e.g. 900) -- true bp scales with the baseline,
        unlike a fixed 1/100-yen pip count which would treat both cases
        identically."""
        near_150, _ = fxa.evaluate_move(150.90, 150.00, threshold_bp=60.0)
        assert near_150 is True
        near_900, _ = fxa.evaluate_move(900.90, 900.00, threshold_bp=60.0)
        assert near_900 is False

    def test_zero_baseline_does_not_raise(self) -> None:
        """Defensive: a zero baseline (never expected for USDJPY spot, but
        guarded rather than left to raise ZeroDivisionError) is inactive."""
        active, _ = fxa.evaluate_move(1.00, 0.0, threshold_bp=60.0)
        assert active is False


# ---------------------------------------------------------------------------
# evaluate_line_cross (AC b)
# ---------------------------------------------------------------------------


class TestEvaluateLineCross:
    def test_bar_spans_line_is_active(self) -> None:
        bar = _bar(low=161.00, high=162.00)
        line = fxa.MonitoredLine(raw="161.50", value=161.50)
        assert fxa.evaluate_line_cross(bar, line) is True

    def test_bar_entirely_above_line_is_inactive(self) -> None:
        bar = _bar(low=162.00, high=163.00)
        line = fxa.MonitoredLine(raw="161.50", value=161.50)
        assert fxa.evaluate_line_cross(bar, line) is False

    def test_bar_entirely_below_line_is_inactive(self) -> None:
        bar = _bar(low=159.00, high=160.00)
        line = fxa.MonitoredLine(raw="161.50", value=161.50)
        assert fxa.evaluate_line_cross(bar, line) is False

    def test_line_exactly_at_bar_boundary_is_active(self) -> None:
        bar = _bar(low=161.50, high=162.50)
        line = fxa.MonitoredLine(raw="161.50", value=161.50)
        assert fxa.evaluate_line_cross(bar, line) is True


# ---------------------------------------------------------------------------
# evaluate_data_gap (AC c) — schedule-aware cutoff
# ---------------------------------------------------------------------------


class TestEvaluateDataGap:
    def test_no_gap_when_todays_forecast_present(self) -> None:
        now = _jst(2026, 8, 28, 23, 0)  # Friday, after cutoff
        forecast = _forecast(date(2026, 8, 28), 150.0)
        active, target, cutoff = fxa.evaluate_data_gap(now, forecast)
        assert active is False
        assert target == date(2026, 8, 28)
        assert cutoff is True

    def test_gap_when_forecast_missing_after_cutoff(self) -> None:
        now = _jst(2026, 8, 28, 22, 0)  # Friday, at cutoff
        forecast = _forecast(date(2026, 8, 27), 150.0)  # yesterday's, stale
        active, _, _ = fxa.evaluate_data_gap(now, forecast)
        assert active is True

    def test_no_gap_before_cutoff_even_if_missing(self) -> None:
        now = _jst(2026, 8, 28, 21, 59, 59)  # Friday, just before cutoff
        forecast = _forecast(date(2026, 8, 27), 150.0)
        active, _, cutoff = fxa.evaluate_data_gap(now, forecast)
        assert cutoff is False
        assert active is False

    def test_no_forecast_at_all_after_cutoff_is_gap(self) -> None:
        now = _jst(2026, 8, 28, 22, 0, 1)
        active, _, _ = fxa.evaluate_data_gap(now, None)
        assert active is True

    def test_weekend_checks_friday_not_age_in_business_days(self) -> None:
        """Regression for the 8/28 incident: a Friday run miss must be
        detectable all through the weekend by checking 'is Friday's forecast
        present', not by an 'older than 1 business day' age threshold (which
        would not trip until Monday)."""
        now = _jst(2026, 8, 30, 12, 0)  # Sunday
        forecast = _forecast(date(2026, 8, 27), 150.0)  # last good: Thursday
        active, target, cutoff = fxa.evaluate_data_gap(now, forecast)
        assert target == date(2026, 8, 28)  # Friday
        assert cutoff is True
        assert active is True  # Thursday's forecast does not satisfy Friday's slot

    def test_weekend_with_fridays_forecast_present_is_not_a_gap(self) -> None:
        now = _jst(2026, 8, 30, 12, 0)  # Sunday
        forecast = _forecast(date(2026, 8, 28), 150.0)  # Friday's forecast exists
        active, _, _ = fxa.evaluate_data_gap(now, forecast)
        assert active is False

    # -- FIX 8: sticky gap must not clear on target-date rollover alone ----

    def test_monday_morning_stays_active_no_false_clear(self) -> None:
        """Friday missing -> active all through the weekend -> Monday 09:00
        JST (before Monday's own 22:00 cutoff, and before Monday's own run
        has had a chance to complete) must STILL be active — target-date
        rollover (Friday -> Monday) and cutoff resetting must never, by
        themselves, produce a clear transition."""
        forecast = _forecast(date(2026, 8, 27), 150.0)  # last good: Thursday

        # Sunday: already active (established by the existing weekend test).
        sunday = _jst(2026, 8, 30, 12, 0)
        active_sun, _, _ = fxa.evaluate_data_gap(sunday, forecast, was_active=False)
        assert active_sun is True

        # Monday 09:00: was_active carries the alert's own prior-run state
        # forward (True) -- must stay active, not clear.
        monday_morning = _jst(2026, 8, 31, 9, 0)  # Monday
        active_mon, target_mon, cutoff_mon = fxa.evaluate_data_gap(
            monday_morning, forecast, was_active=True
        )
        assert target_mon == date(2026, 8, 31)  # rolled forward to Monday
        assert cutoff_mon is False  # Monday's own 22:00 cutoff not yet reached
        assert active_mon is True  # still active despite both of the above

    def test_monday_morning_without_was_active_does_not_yet_fire(self) -> None:
        """The was_active=False (fresh-detection) path is unchanged: before
        Monday's own cutoff, a run that has never seen this alert active
        correctly waits rather than firing immediately."""
        forecast = _forecast(date(2026, 8, 27), 150.0)
        monday_morning = _jst(2026, 8, 31, 9, 0)
        active, _, cutoff = fxa.evaluate_data_gap(
            monday_morning, forecast, was_active=False
        )
        assert cutoff is False
        assert active is False

    def test_true_clear_when_mondays_forecast_appears(self) -> None:
        """The genuine clear: once a forecast whose as_of_jst is no longer
        behind today's target actually exists, the sticky alert clears."""
        forecast = _forecast(date(2026, 8, 31), 150.0)  # Monday's own forecast
        monday = _jst(2026, 8, 31, 9, 0)
        active, target, _ = fxa.evaluate_data_gap(monday, forecast, was_active=True)
        assert target == date(2026, 8, 31)
        assert active is False

    def test_evaluate_alerts_end_to_end_monday_morning_no_false_clear(self) -> None:
        """End-to-end through evaluate_alerts (which supplies was_active from
        prev_state): Friday missing -> Sunday poll fires -> Monday 09:00 poll
        must not report a clear."""
        stale_forecast = _forecast(date(2026, 8, 27), 150.0)

        sunday = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=stale_forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 30, 12, 0),
            prev_state={},
        )
        assert [a.key for a in sunday.fired] == ["gap"]
        assert sunday.state["gap"] is True

        monday_morning = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=stale_forecast,  # still Thursday's -- Monday's run hasn't happened yet
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 31, 9, 0),
            prev_state=sunday.state,
        )
        assert monday_morning.cleared_keys == ()
        assert monday_morning.fired == ()
        assert monday_morning.state["gap"] is True

        # The true clear, once Monday's own forecast appears.
        monday_forecast = _forecast(date(2026, 8, 31), 150.0)
        monday_after_run = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=monday_forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 31, 9, 5),
            prev_state=monday_morning.state,
        )
        assert monday_after_run.cleared_keys == ("gap",)
        assert monday_after_run.state["gap"] is False


# ---------------------------------------------------------------------------
# state marker encode/parse round trip
# ---------------------------------------------------------------------------


class TestStateMarker:
    def test_round_trip(self) -> None:
        state = {"move": True, "line:161.50": False, "gap": True}
        marker = fxa.encode_state_marker(state)
        parsed = fxa.parse_alert_state([marker])
        assert parsed == state

    def test_empty_comments_yields_empty_state(self) -> None:
        assert fxa.parse_alert_state([]) == {}

    def test_comments_without_marker_yield_empty_state(self) -> None:
        assert fxa.parse_alert_state(["hello", "world, no marker here"]) == {}

    def test_most_recent_marker_wins(self) -> None:
        older = fxa.encode_state_marker({"move": True})
        newer = fxa.encode_state_marker({"move": False, "gap": True})
        parsed = fxa.parse_alert_state([older, newer])
        assert parsed == {"move": False, "gap": True}

    def test_marker_embedded_in_prose_is_still_found(self) -> None:
        body = "Some human comment.\n\n" + fxa.encode_state_marker({"move": True})
        assert fxa.parse_alert_state([body]) == {"move": True}

    def test_malformed_marker_is_ignored(self) -> None:
        body = f"{fxa._STATE_MARKER_PREFIX}not-json{fxa._STATE_MARKER_SUFFIX}"
        assert fxa.parse_alert_state([body]) == {}


# ---------------------------------------------------------------------------
# evaluate_alerts — full suppression / re-arm state machine
# ---------------------------------------------------------------------------


class TestEvaluateAlertsSuppression:
    def _snapshot_bars(self) -> tuple:
        return (_bar(low=150.00, high=150.50),)

    def test_first_breach_fires(self) -> None:
        forecast = _forecast(date(2026, 8, 28), 150.00)
        result = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=151.00,  # +100 pips
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
        )
        assert [a.key for a in result.fired] == ["move"]
        assert result.state["move"] is True

    def test_steady_state_does_not_refire(self) -> None:
        forecast = _forecast(date(2026, 8, 28), 150.00)
        r1 = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=151.00,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
        )
        r2 = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=151.00,  # unchanged — same breach, hourly cron
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 11, 0),
            prev_state=r1.state,
        )
        assert r2.fired == ()
        assert r2.cleared_keys == ()

    def test_fire_then_clear_then_refire_second_fire_not_suppressed(self) -> None:
        forecast = _forecast(date(2026, 8, 28), 150.00)

        # Run 1: breach -> fires.
        r1 = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=151.00,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
        )
        assert [a.key for a in r1.fired] == ["move"]

        # Run 2: back within threshold -> clears (recorded even though no
        # new alert fires this run).
        r2 = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=150.10,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 11, 0),
            prev_state=r1.state,
        )
        assert r2.fired == ()
        assert r2.cleared_keys == ("move",)
        assert r2.state["move"] is False

        # Run 3: breaches again -> must fire again, not be suppressed by
        # stale history.
        r3 = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=151.20,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 12, 0),
            prev_state=r2.state,
        )
        assert [a.key for a in r3.fired] == ["move"]
        assert r3.state["move"] is True

    def test_line_cross_fire_then_clear_then_refire(self) -> None:
        line = fxa.parse_lines_env("161.50")
        forecast = _forecast(date(2026, 8, 28), 165.00)

        r1 = fxa.evaluate_alerts(
            bars=(_bar(low=161.00, high=161.60),),  # spans 161.50
            live_spot=165.00,
            forecast=forecast,
            lines=line,
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
        )
        assert [a.key for a in r1.fired] == ["line:161.50"]

        r2 = fxa.evaluate_alerts(
            bars=(_bar(low=162.00, high=163.00),),  # moved away, no longer spans
            live_spot=165.00,
            forecast=forecast,
            lines=line,
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 11, 0),
            prev_state=r1.state,
        )
        assert r2.fired == ()
        assert r2.cleared_keys == ("line:161.50",)

        r3 = fxa.evaluate_alerts(
            bars=(_bar(low=161.10, high=161.70),),  # spans again
            live_spot=165.00,
            forecast=forecast,
            lines=line,
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 12, 0),
            prev_state=r2.state,
        )
        assert [a.key for a in r3.fired] == ["line:161.50"]

    def test_data_gap_fires_once_then_suppressed_across_polls(self) -> None:
        forecast = _forecast(date(2026, 8, 27), 150.00)  # stale
        r1 = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 22, 0),
            prev_state={},
        )
        assert [a.key for a in r1.fired] == ["gap"]

        r2 = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 29, 2, 0),  # next 2h cron, still stale
            prev_state=r1.state,
        )
        assert r2.fired == ()

        # Forecast catches up -> clears; then a later new gap must refire.
        r3 = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=_forecast(date(2026, 8, 28), 150.00),
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 29, 4, 0),
            prev_state=r2.state,
        )
        assert r3.cleared_keys == ("gap",)

    def test_spot_fetch_failure_is_itself_an_alert(self) -> None:
        result = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=_forecast(date(2026, 8, 28), 150.00),
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
            spot_fetch_error="URLError: timed out",
        )
        assert "fetch_failure:spot" in [a.key for a in result.fired]

    def test_forecast_fetch_failure_is_itself_an_alert(self) -> None:
        result = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=150.00,
            forecast=None,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
            forecast_fetch_error="FileNotFoundError: input_snapshot.json",
        )
        assert "fetch_failure:forecast" in [a.key for a in result.fired]

    def test_spot_fetch_failure_carries_forward_move_state_untouched(self) -> None:
        forecast = _forecast(date(2026, 8, 28), 150.00)
        r1 = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=151.00,  # breach -> move active
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
        )
        assert r1.state["move"] is True

        r2 = fxa.evaluate_alerts(
            bars=(),
            live_spot=None,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 11, 0),
            prev_state=r1.state,
            spot_fetch_error="URLError: timed out",
        )
        # Cannot evaluate move this run -> carried forward, not guessed/cleared.
        assert r2.state["move"] is True
        assert "move" not in [a.key for a in r2.fired]
        assert "move" not in r2.cleared_keys
        # But the fetch failure itself is a fresh alert.
        assert [a.key for a in r2.fired] == ["fetch_failure:spot"]

    def test_no_lines_no_forecast_change_writes_nothing(self) -> None:
        forecast = _forecast(date(2026, 8, 28), 150.00)
        result = fxa.evaluate_alerts(
            bars=self._snapshot_bars(),
            live_spot=150.10,
            forecast=forecast,
            lines=(),
            move_threshold_bp=60.0,
            now_jst=_jst(2026, 8, 28, 10, 0),
            prev_state={},
        )
        assert result.fired == ()
        assert result.cleared_keys == ()


# ---------------------------------------------------------------------------
# render_state_comment
# ---------------------------------------------------------------------------


class TestRenderStateComment:
    def test_none_when_nothing_changed(self) -> None:
        assert fxa.render_state_comment((), (), {}, datetime.now(timezone.utc)) is None

    def test_body_when_fired(self) -> None:
        alert = fxa.Alert(key="move", title="Move alert", body="detail text")
        body = fxa.render_state_comment(
            (alert,), (), {"move": True}, datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
        )
        assert body is not None
        assert "Move alert" in body
        assert "detail text" in body
        assert fxa.encode_state_marker({"move": True}) in body

    def test_body_when_only_cleared_no_new_fires(self) -> None:
        """The one exception to 'alert-free run writes nothing': a clear
        transition must still be recorded even with zero new fires."""
        body = fxa.render_state_comment(
            (), ("move",), {"move": False}, datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
        )
        assert body is not None
        assert "Cleared: move" in body

    def test_state_marker_from_rendered_body_round_trips(self) -> None:
        alert = fxa.Alert(key="gap", title="Gap", body="detail")
        state = {"gap": True, "move": False}
        body = fxa.render_state_comment(
            (alert,), (), state, datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
        )
        assert body is not None
        assert fxa.parse_alert_state([body]) == state


# ---------------------------------------------------------------------------
# GitHub Issue state I/O
# ---------------------------------------------------------------------------


class TestGitHubIssueStateIO:
    def test_initial_issue_body_restores_state_before_any_comments(self, monkeypatch) -> None:
        initial = fxa.encode_state_marker({"move": True, "gap": False})
        monkeypatch.setattr(fxa, "fetch_issue_comment_bodies", lambda *_args, **_kwargs: [])
        bodies = fxa.fetch_issue_state_bodies(
            "owner/repo", "token", {"number": 7, "body": "created\n" + initial}
        )
        assert fxa.parse_alert_state(bodies) == {"move": True, "gap": False}

    def test_comment_fetch_follows_pagination_and_newest_marker_wins(self, monkeypatch) -> None:
        calls: list[str] = []
        older = fxa.encode_state_marker({"move": False})
        newer = fxa.encode_state_marker({"move": True, "gap": True})
        page1 = [{"body": older}] + [{"body": "noise"} for _ in range(99)]
        page2 = [{"body": newer}]

        def fake_request(method, url, token, body=None, timeout=30):
            calls.append(url)
            return page1 if url.endswith("page=1") else page2

        monkeypatch.setattr(fxa, "_github_request", fake_request)
        bodies = fxa.fetch_issue_comment_bodies("owner/repo", "token", 9)
        assert len(bodies) == 101
        assert calls == [
            f"{fxa.GITHUB_API}/repos/owner/repo/issues/9/comments?per_page=100&page=1",
            f"{fxa.GITHUB_API}/repos/owner/repo/issues/9/comments?per_page=100&page=2",
        ]
        assert fxa.parse_alert_state(bodies) == {"move": True, "gap": True}


# ---------------------------------------------------------------------------
# read_forecast_meta (local filesystem I/O — no network)
# ---------------------------------------------------------------------------


class TestReadForecastMeta:
    def test_reads_current_spot_and_as_of_from_input_snapshot(self, tmp_path) -> None:
        latest = tmp_path / "csv" / "latest"
        latest.mkdir(parents=True)
        (latest / "input_snapshot.json").write_text(
            '{"as_of_jst": "2026-08-28T08:00:00+09:00", "current_spot": 150.234}',
            encoding="utf-8",
        )
        meta = fxa.read_forecast_meta(str(tmp_path))
        assert meta.as_of_jst == date(2026, 8, 28)
        assert meta.current_spot == pytest.approx(150.234)

    def test_reads_batch_id_from_manifest_when_present(self, tmp_path) -> None:
        latest = tmp_path / "csv" / "latest"
        latest.mkdir(parents=True)
        (latest / "input_snapshot.json").write_text(
            '{"as_of_jst": "2026-08-28T08:00:00+09:00", "current_spot": 150.0}',
            encoding="utf-8",
        )
        (latest / "manifest.json").write_text(
            '{"forecast_batch_id": "fb_USDJPY_20260828T080000_v1_abcdef1234567890"}',
            encoding="utf-8",
        )
        meta = fxa.read_forecast_meta(str(tmp_path))
        assert meta.forecast_batch_id == "fb_USDJPY_20260828T080000_v1_abcdef1234567890"

    def test_missing_snapshot_raises(self, tmp_path) -> None:
        with pytest.raises(OSError):
            fxa.read_forecast_meta(str(tmp_path))

    def test_missing_manifest_is_tolerated(self, tmp_path) -> None:
        latest = tmp_path / "csv" / "latest"
        latest.mkdir(parents=True)
        (latest / "input_snapshot.json").write_text(
            '{"as_of_jst": "2026-08-28T08:00:00+09:00", "current_spot": 150.0}',
            encoding="utf-8",
        )
        meta = fxa.read_forecast_meta(str(tmp_path))
        assert meta.forecast_batch_id is None


# ---------------------------------------------------------------------------
# FIX 6: malformed env config must surface as an alert, not crash main()
# ---------------------------------------------------------------------------


class TestMainConfigErrorHandling:
    """main()'s env parsing used to happen outside any guarded region, so a
    malformed repo variable (e.g. FX_ALERT_LINES set to a non-numeric value)
    raised ValueError and crashed the run before it ever reached the
    fetch-failure alert path. It must now surface as a config-error alert
    through that same path instead."""

    def _stub_io(self, monkeypatch, *, created: dict) -> None:
        # Pin main()'s internal datetime.now(timezone.utc) so the data-gap
        # check does not depend on the real wall clock at test-run time.
        fixed_now = datetime(2026, 8, 31, 0, 0, 0)  # Monday 00:00 UTC == 09:00 JST

        class _FixedDatetime(fxa.datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_now.replace(tzinfo=tz) if tz else fixed_now

        monkeypatch.setattr(fxa, "datetime", _FixedDatetime)
        monkeypatch.setattr(fxa, "fetch_yahoo_daily", lambda *a, **k: (150.0, ()))
        monkeypatch.setattr(
            fxa,
            "read_forecast_meta",
            lambda *a, **k: fxa.ForecastMeta(
                as_of_jst=date(2026, 8, 31), current_spot=150.0
            ),
        )
        monkeypatch.setattr(fxa, "find_open_alert_issue", lambda *a, **k: None)

        def fake_create(repo, token, label, title, body):
            created["title"] = title
            created["body"] = body
            return {"number": 1}

        monkeypatch.setattr(fxa, "create_alert_issue", fake_create)
        monkeypatch.setattr(
            fxa,
            "comment_on_issue",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("no existing issue in this test")
            ),
        )

    def test_malformed_fx_alert_lines_does_not_crash_and_names_the_variable(
        self, monkeypatch, capsys
    ) -> None:
        created: dict = {}
        self._stub_io(monkeypatch, created=created)
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        monkeypatch.setenv("FX_ALERT_LINES", "not-a-number")
        monkeypatch.delenv("FX_ALERT_MOVE_BP", raising=False)

        exit_code = fxa.main()

        assert exit_code == 0
        assert created.get("body") is not None
        assert "FX_ALERT_LINES" in created["body"]
        assert "not-a-number" in created["body"]

    def test_malformed_fx_alert_move_bp_does_not_crash_and_names_the_variable(
        self, monkeypatch
    ) -> None:
        created: dict = {}
        self._stub_io(monkeypatch, created=created)
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        monkeypatch.setenv("FX_ALERT_MOVE_BP", "sixty")
        monkeypatch.delenv("FX_ALERT_LINES", raising=False)

        exit_code = fxa.main()

        assert exit_code == 0
        assert created.get("body") is not None
        assert "FX_ALERT_MOVE_BP" in created["body"]
        assert "sixty" in created["body"]

    def test_valid_config_produces_no_config_error_alert(self, monkeypatch) -> None:
        """Control case: a well-formed config alone writes nothing (no
        fired/cleared alerts at all in this stub scenario)."""
        created: dict = {}
        self._stub_io(monkeypatch, created=created)
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        monkeypatch.setenv("FX_ALERT_MOVE_BP", "60")
        monkeypatch.setenv("FX_ALERT_LINES", "161.50")

        exit_code = fxa.main()

        assert exit_code == 0
        assert created == {}


# ---------------------------------------------------------------------------
# fetch_yahoo_daily parsing (network call itself is not exercised in tests)
# ---------------------------------------------------------------------------


class TestFetchYahooDailyParsing:
    def test_no_network_access_in_tests(self, monkeypatch) -> None:
        def _boom(*args, **kwargs):
            raise AssertionError("network access attempted in tests")

        monkeypatch.setattr(fxa.urllib.request, "urlopen", _boom)
        with pytest.raises(AssertionError):
            fxa.fetch_yahoo_daily()

    def test_parses_valid_payload(self, monkeypatch) -> None:
        import json as _json

        payload = {
            "chart": {
                "result": [
                    {
                        "meta": {"regularMarketPrice": 150.5},
                        "timestamp": [1000, 2000],
                        "indicators": {
                            "quote": [
                                {
                                    "open": [149.0, 150.0],
                                    "high": [149.5, 150.5],
                                    "low": [148.5, 149.5],
                                    "close": [149.2, 150.2],
                                }
                            ]
                        },
                    }
                ]
            }
        }

        class _FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return _json.dumps(payload).encode("utf-8")

        monkeypatch.setattr(fxa.urllib.request, "urlopen", lambda *a, **k: _FakeResp())
        spot, bars = fxa.fetch_yahoo_daily()
        assert spot == pytest.approx(150.5)
        assert len(bars) == 2
        assert bars[-1].close == pytest.approx(150.2)

    def test_missing_regular_market_price_raises(self, monkeypatch) -> None:
        import json as _json

        payload = {"chart": {"result": [{"meta": {}, "timestamp": [], "indicators": {}}]}}

        class _FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return _json.dumps(payload).encode("utf-8")

        monkeypatch.setattr(fxa.urllib.request, "urlopen", lambda *a, **k: _FakeResp())
        with pytest.raises(ValueError):
            fxa.fetch_yahoo_daily()

    # -- FIX 5: HTTP-200-with-error-payload shapes must raise ValueError,
    # never an uncaught TypeError/IndexError that would escape main()'s
    # (urllib.error.URLError, ValueError, KeyError, TimeoutError, OSError)
    # guard and crash the run instead of surfacing a fetch-failure alert. --

    def _fake_resp(self, payload: dict) -> object:
        import json as _json

        class _FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return _json.dumps(payload).encode("utf-8")

        return _FakeResp()

    def test_null_result_raises_value_error(self, monkeypatch) -> None:
        """{"chart": {"result": null, "error": {...}}} -- Yahoo's documented
        shape for an invalid/unrecognized symbol. Subscripting None would
        raise TypeError, not ValueError, if left unguarded."""
        payload = {
            "chart": {
                "result": None,
                "error": {"code": "Not Found", "description": "No data found"},
            }
        }
        monkeypatch.setattr(
            fxa.urllib.request, "urlopen", lambda *a, **k: self._fake_resp(payload)
        )
        with pytest.raises(ValueError):
            fxa.fetch_yahoo_daily()

    def test_empty_result_list_raises_value_error(self, monkeypatch) -> None:
        """{"chart": {"result": []}} -- indexing [0] on this would raise
        IndexError, not ValueError, if left unguarded."""
        payload = {"chart": {"result": []}}
        monkeypatch.setattr(
            fxa.urllib.request, "urlopen", lambda *a, **k: self._fake_resp(payload)
        )
        with pytest.raises(ValueError):
            fxa.fetch_yahoo_daily()

    def test_missing_chart_key_raises_value_error(self, monkeypatch) -> None:
        payload = {"not_chart": {}}
        monkeypatch.setattr(
            fxa.urllib.request, "urlopen", lambda *a, **k: self._fake_resp(payload)
        )
        with pytest.raises(ValueError):
            fxa.fetch_yahoo_daily()


# ---------------------------------------------------------------------------
# Independence contract
# ---------------------------------------------------------------------------


class TestIndependenceContract:
    def test_module_has_no_third_party_dependencies(self) -> None:
        import ast

        tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
        stdlib_roots = {
            "json",
            "os",
            "re",
            "sys",
            "urllib",
            "dataclasses",
            "datetime",
            "__future__",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root in stdlib_roots, f"unexpected import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    root = node.module.split(".")[0]
                    assert root in stdlib_roots, f"unexpected import: {node.module}"
