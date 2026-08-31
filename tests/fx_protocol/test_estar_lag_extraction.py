"""Unit tests for the e_star transition-extraction decision function
(FX-ESTAR-LAG, ``scripts/analyze_estar_lag.py``).

``scripts/`` is not a package, so the module under test is loaded directly by
file path. All fixtures are synthetic ``(date, e_star)`` sequences — no file
I/O, no real snapshot data.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

_SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "analyze_estar_lag.py"
)
_spec = importlib.util.spec_from_file_location("analyze_estar_lag", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
analyze_estar_lag = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = analyze_estar_lag
_spec.loader.exec_module(analyze_estar_lag)

extract_transitions = analyze_estar_lag.extract_transitions
business_day_shift = analyze_estar_lag.business_day_shift
ALWAYS_POSITIVE_POST_SHOCK = analyze_estar_lag.ALWAYS_POSITIVE_POST_SHOCK
NO_POST_SHOCK_RECOVERY = analyze_estar_lag.NO_POST_SHOCK_RECOVERY
SUSTAINED_POSITIVE = analyze_estar_lag.SUSTAINED_POSITIVE
CROSSED_POSITIVE = analyze_estar_lag.CROSSED_POSITIVE


def _series(*pairs: tuple[str, float]) -> list[tuple[str, float]]:
    return list(pairs)


class TestSingleCrossing:
    """A series with exactly one dip then one sustained recovery: primary
    and secondary must agree.
    """

    def test_single_crossing_primary_equals_secondary(self) -> None:
        series = _series(
            ("2026-07-30", -0.1),
            ("2026-07-31", -0.2),
            ("2026-08-03", 0.1),
            ("2026-08-04", 0.2),
            ("2026-08-05", 0.3),
        )
        primary, secondary = extract_transitions(series)
        assert primary.label == SUSTAINED_POSITIVE
        assert secondary.label == CROSSED_POSITIVE
        assert primary.date == secondary.date == "2026-08-03"

    def test_pre_shock_positive_day_is_not_a_fallback(self) -> None:
        """The first day in the (already-filtered) window being positive must
        not itself count as a crossing candidate — a preceding <=0 day is
        required within the window.
        """
        series = _series(
            ("2026-07-30", 0.5),  # positive from the very start of the window
            ("2026-07-31", -0.1),
            ("2026-08-03", 0.2),
        )
        primary, secondary = extract_transitions(series)
        # The first (window-start) positive day must not be reported as the
        # transition; only the crossing on 2026-08-03 qualifies.
        assert primary.date == secondary.date == "2026-08-03"


class TestMultiCrossing:
    """Multi-crossing series: primary (sustained) and secondary (first
    crossing, single-day OK) must diverge.
    """

    def test_multi_crossing_primary_and_secondary_diverge(self) -> None:
        series = _series(
            ("2026-07-30", -0.1),
            ("2026-07-31", 0.05),  # first crossing (single day)
            ("2026-08-03", -0.2),  # reverts
            ("2026-08-04", -0.1),
            ("2026-08-05", 0.1),  # second crossing — this one sustains
            ("2026-08-06", 0.2),
            ("2026-08-07", 0.3),
        )
        primary, secondary = extract_transitions(series)
        assert secondary.label == CROSSED_POSITIVE
        assert secondary.date == "2026-07-31"
        assert primary.label == SUSTAINED_POSITIVE
        assert primary.date == "2026-08-05"
        assert primary.date != secondary.date

    def test_many_intermittent_crossings_before_final_sustain(self) -> None:
        series = _series(
            ("2026-07-30", -1.0),
            ("2026-07-31", 0.01),  # crossing 1 (secondary)
            ("2026-08-03", -0.01),
            ("2026-08-04", 0.02),  # crossing 2
            ("2026-08-05", -0.02),
            ("2026-08-06", 0.03),  # crossing 3 — sustains from here (primary)
            ("2026-08-07", 0.04),
            ("2026-08-10", 0.05),
        )
        primary, secondary = extract_transitions(series)
        assert secondary.date == "2026-07-31"
        assert primary.date == "2026-08-06"

    def test_single_day_crossing_exactly_at_window_end(self) -> None:
        """A crossing on the very last day trivially 'sustains' (nothing
        after it to revert): primary and secondary agree on that date even
        though earlier crossings existed.
        """
        series = _series(
            ("2026-07-30", -0.5),
            ("2026-07-31", 0.1),  # crossing 1 (secondary)
            ("2026-08-03", -0.3),
            ("2026-08-04", 0.2),  # final day, trivially sustained (primary)
        )
        primary, secondary = extract_transitions(series)
        assert secondary.date == "2026-07-31"
        assert primary.date == "2026-08-04"


class TestAlwaysPositivePostShock:
    """No day in the window is <=0 at all: report lag eliminated, not a
    (falsely early) transition date.
    """

    def test_always_positive_reports_special_label_and_null_date(self) -> None:
        series = _series(
            ("2026-07-30", 0.1),
            ("2026-07-31", 0.2),
            ("2026-08-03", 0.3),
        )
        primary, secondary = extract_transitions(series)
        assert primary.label == ALWAYS_POSITIVE_POST_SHOCK
        assert primary.date is None
        assert secondary.label == ALWAYS_POSITIVE_POST_SHOCK
        assert secondary.date is None

    def test_single_day_always_positive_series(self) -> None:
        series = _series(("2026-07-30", 0.5))
        primary, secondary = extract_transitions(series)
        assert primary.label == ALWAYS_POSITIVE_POST_SHOCK
        assert secondary.label == ALWAYS_POSITIVE_POST_SHOCK


class TestNoPostShockRecovery:
    """Becomes <=0 at some point (with or without an intervening crossing)
    and never holds positive through the window end.
    """

    def test_never_recovers_at_all(self) -> None:
        series = _series(
            ("2026-07-30", 0.1),
            ("2026-07-31", -0.2),
            ("2026-08-03", -0.3),
            ("2026-08-04", -0.1),
        )
        primary, secondary = extract_transitions(series)
        assert primary.label == NO_POST_SHOCK_RECOVERY
        assert primary.date is None
        assert secondary.label == NO_POST_SHOCK_RECOVERY
        assert secondary.date is None

    def test_intermittent_crossing_then_final_relapse_is_no_recovery(self) -> None:
        """A crossing happened mid-window but the series ends <=0 — must be
        reported as NO_POST_SHOCK_RECOVERY, not as a stale sustained/first
        crossing from earlier in the window.
        """
        series = _series(
            ("2026-07-30", -0.5),
            ("2026-07-31", 0.2),  # crosses...
            ("2026-08-03", 0.3),
            ("2026-08-04", -0.1),  # ...but relapses and never recovers
            ("2026-08-05", -0.2),
        )
        primary, secondary = extract_transitions(series)
        assert primary.label == NO_POST_SHOCK_RECOVERY
        assert primary.date is None
        assert secondary.label == NO_POST_SHOCK_RECOVERY
        assert secondary.date is None

    def test_single_day_series_at_or_below_zero(self) -> None:
        series = _series(("2026-07-30", 0.0))
        primary, secondary = extract_transitions(series)
        assert primary.label == NO_POST_SHOCK_RECOVERY
        assert secondary.label == NO_POST_SHOCK_RECOVERY


class TestZeroIsNonPositive:
    """e_star == 0.0 counts as <=0 (non-positive), not as a positive value."""

    def test_zero_does_not_count_as_positive(self) -> None:
        series = _series(
            ("2026-07-30", -0.1),
            ("2026-07-31", 0.0),
            ("2026-08-03", 0.1),
        )
        primary, secondary = extract_transitions(series)
        # 0.0 on 07-31 is non-positive, so the crossing candidate is 08-03
        # (preceded by >=1 <=0 day — both 07-30 and 07-31 qualify).
        assert primary.date == secondary.date == "2026-08-03"

    def test_zero_satisfies_the_preceding_non_positive_requirement(self) -> None:
        series = _series(
            ("2026-07-30", 0.1),
            ("2026-07-31", 0.0),
            ("2026-08-03", 0.1),
        )
        primary, secondary = extract_transitions(series)
        assert primary.date == secondary.date == "2026-08-03"


class TestEmptySeriesRejected:
    def test_empty_series_raises(self) -> None:
        with pytest.raises(ValueError):
            extract_transitions([])


class TestBusinessDayShift:
    def test_shift_is_signed_business_day_offset(self) -> None:
        dates = ["2026-07-30", "2026-07-31", "2026-08-03", "2026-08-04", "2026-08-05"]
        baseline = analyze_estar_lag.Transition(SUSTAINED_POSITIVE, "2026-08-05")
        ablated = analyze_estar_lag.Transition(SUSTAINED_POSITIVE, "2026-08-03")
        assert business_day_shift(baseline, ablated, dates) == -2

    def test_shift_is_none_when_either_side_is_a_special_label(self) -> None:
        dates = ["2026-07-30", "2026-07-31", "2026-08-03"]
        baseline = analyze_estar_lag.Transition(SUSTAINED_POSITIVE, "2026-08-03")
        ablated = analyze_estar_lag.Transition(ALWAYS_POSITIVE_POST_SHOCK, None)
        assert business_day_shift(baseline, ablated, dates) is None
        assert business_day_shift(ablated, baseline, dates) is None
