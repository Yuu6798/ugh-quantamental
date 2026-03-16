"""Tests for FX weekly report model validation (Phase 2 Milestone 16)."""

from __future__ import annotations

from datetime import datetime

import pytest

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    ForecastDirection,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.report_models import (
    BaselineWeeklyComparison,
    StateWeeklyMetrics,
    StrategyWeeklyMetrics,
    WeeklyCaseExample,
    WeeklyGrvFireSummary,
    WeeklyMismatchSummary,
    WeeklyReportRequest,
)
from ugh_quantamental.schemas.enums import LifecycleState

_NOW = datetime(2026, 3, 16, 10, 0, 0)


# ---------------------------------------------------------------------------
# WeeklyReportRequest
# ---------------------------------------------------------------------------


def test_weekly_report_request_defaults() -> None:
    req = WeeklyReportRequest(pair=CurrencyPair.USDJPY, report_generated_at_jst=_NOW)
    assert req.business_day_count == 5
    assert req.max_examples == 3


def test_weekly_report_request_custom() -> None:
    req = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=_NOW,
        business_day_count=3,
        max_examples=5,
    )
    assert req.business_day_count == 3
    assert req.max_examples == 5


@pytest.mark.parametrize("business_day_count", [0, -1])
def test_weekly_report_request_invalid_business_day_count(business_day_count: int) -> None:
    with pytest.raises(Exception):
        WeeklyReportRequest(
            pair=CurrencyPair.USDJPY,
            report_generated_at_jst=_NOW,
            business_day_count=business_day_count,
        )


@pytest.mark.parametrize("max_examples", [0, -1])
def test_weekly_report_request_invalid_max_examples(max_examples: int) -> None:
    with pytest.raises(Exception):
        WeeklyReportRequest(
            pair=CurrencyPair.USDJPY,
            report_generated_at_jst=_NOW,
            max_examples=max_examples,
        )


def test_weekly_report_request_normalizes_utc_to_jst() -> None:
    """UTC-aware input is normalized to JST-aware so the *_jst field is canonical."""
    from datetime import timezone
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    # 2026-03-16 01:00 UTC == 2026-03-16 10:00 JST
    utc_input = datetime(2026, 3, 16, 1, 0, 0, tzinfo=timezone.utc)
    req = WeeklyReportRequest(pair=CurrencyPair.USDJPY, report_generated_at_jst=utc_input)
    assert req.report_generated_at_jst.tzinfo is not None
    assert req.report_generated_at_jst == datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)


def test_weekly_report_request_normalizes_naive_to_jst() -> None:
    """Naive input is treated as already in JST and given explicit JST tzinfo."""
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    naive = datetime(2026, 3, 16, 10, 0, 0)  # no tzinfo
    req = WeeklyReportRequest(pair=CurrencyPair.USDJPY, report_generated_at_jst=naive)
    assert req.report_generated_at_jst.tzinfo is not None
    assert req.report_generated_at_jst == datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)


def test_weekly_report_request_result_carries_normalized_timestamp() -> None:
    """WeeklyReportResult.report_generated_at_jst reflects the normalized JST value."""
    from datetime import timezone
    from zoneinfo import ZoneInfo

    _JST = ZoneInfo("Asia/Tokyo")
    # Same instant, different input forms — both must produce the same normalized field.
    utc_input = datetime(2026, 3, 16, 1, 0, 0, tzinfo=timezone.utc)
    jst_input = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)
    req_utc = WeeklyReportRequest(pair=CurrencyPair.USDJPY, report_generated_at_jst=utc_input)
    req_jst = WeeklyReportRequest(pair=CurrencyPair.USDJPY, report_generated_at_jst=jst_input)
    assert req_utc.report_generated_at_jst == req_jst.report_generated_at_jst


def test_weekly_report_request_frozen() -> None:
    req = WeeklyReportRequest(pair=CurrencyPair.USDJPY, report_generated_at_jst=_NOW)
    with pytest.raises(Exception):
        req.business_day_count = 10  # type: ignore[misc]


def test_weekly_report_request_extra_fields_forbidden() -> None:
    with pytest.raises(Exception):
        WeeklyReportRequest(
            pair=CurrencyPair.USDJPY,
            report_generated_at_jst=_NOW,
            unknown_field="x",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# StrategyWeeklyMetrics
# ---------------------------------------------------------------------------


def test_strategy_weekly_metrics_ugh() -> None:
    m = StrategyWeeklyMetrics(
        strategy_kind=StrategyKind.ugh,
        forecast_count=5,
        direction_evaluable_count=5,
        direction_hit_count=3,
        direction_accuracy=0.6,
        range_evaluable_count=5,
        range_hit_count=4,
        range_hit_rate=0.8,
        mean_abs_close_error_bp=12.5,
        mean_abs_magnitude_error_bp=8.0,
    )
    assert m.strategy_kind == StrategyKind.ugh
    assert m.direction_accuracy == 0.6


def test_strategy_weekly_metrics_baseline_nulls() -> None:
    m = StrategyWeeklyMetrics(
        strategy_kind=StrategyKind.baseline_random_walk,
        forecast_count=5,
        direction_evaluable_count=5,
        direction_hit_count=2,
        direction_accuracy=0.4,
        range_evaluable_count=0,
        range_hit_count=0,
        range_hit_rate=None,
        mean_abs_close_error_bp=20.0,
        mean_abs_magnitude_error_bp=None,
    )
    assert m.range_hit_rate is None
    assert m.range_evaluable_count == 0


def test_strategy_weekly_metrics_frozen() -> None:
    m = StrategyWeeklyMetrics(
        strategy_kind=StrategyKind.ugh,
        forecast_count=1,
        direction_evaluable_count=1,
        direction_hit_count=1,
        direction_accuracy=1.0,
        range_evaluable_count=1,
        range_hit_count=1,
        range_hit_rate=1.0,
        mean_abs_close_error_bp=0.0,
        mean_abs_magnitude_error_bp=0.0,
    )
    with pytest.raises(Exception):
        m.forecast_count = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# BaselineWeeklyComparison
# ---------------------------------------------------------------------------


def test_baseline_weekly_comparison_with_deltas() -> None:
    c = BaselineWeeklyComparison(
        baseline_strategy_kind=StrategyKind.baseline_random_walk,
        direction_accuracy_delta_vs_ugh=-0.1,
        mean_abs_close_error_bp_delta_vs_ugh=5.0,
    )
    assert c.direction_accuracy_delta_vs_ugh == pytest.approx(-0.1)
    assert c.mean_abs_close_error_bp_delta_vs_ugh == pytest.approx(5.0)


def test_baseline_weekly_comparison_nulls() -> None:
    c = BaselineWeeklyComparison(
        baseline_strategy_kind=StrategyKind.baseline_prev_day_direction,
        direction_accuracy_delta_vs_ugh=None,
        mean_abs_close_error_bp_delta_vs_ugh=None,
    )
    assert c.direction_accuracy_delta_vs_ugh is None


# ---------------------------------------------------------------------------
# StateWeeklyMetrics
# ---------------------------------------------------------------------------


def test_state_weekly_metrics() -> None:
    m = StateWeeklyMetrics(
        dominant_state=LifecycleState.fire,
        forecast_count=3,
        direction_accuracy=0.67,
        mean_abs_close_error_bp=10.0,
    )
    assert m.dominant_state == LifecycleState.fire
    assert m.forecast_count == 3


def test_state_weekly_metrics_null_accuracy() -> None:
    m = StateWeeklyMetrics(
        dominant_state=LifecycleState.dormant,
        forecast_count=0,
        direction_accuracy=None,
        mean_abs_close_error_bp=None,
    )
    assert m.direction_accuracy is None


# ---------------------------------------------------------------------------
# WeeklyGrvFireSummary
# ---------------------------------------------------------------------------


def test_weekly_grv_fire_summary() -> None:
    s = WeeklyGrvFireSummary(
        fire_count=2,
        non_fire_count=8,
        mean_grv_lock_fire=0.75,
        mean_grv_lock_non_fire=0.40,
        fire_direction_accuracy=0.5,
    )
    assert s.fire_count == 2
    assert s.mean_grv_lock_fire == pytest.approx(0.75)


def test_weekly_grv_fire_summary_nulls() -> None:
    s = WeeklyGrvFireSummary(
        fire_count=0,
        non_fire_count=5,
        mean_grv_lock_fire=None,
        mean_grv_lock_non_fire=0.3,
        fire_direction_accuracy=None,
    )
    assert s.fire_direction_accuracy is None


# ---------------------------------------------------------------------------
# WeeklyMismatchSummary
# ---------------------------------------------------------------------------


def test_weekly_mismatch_summary() -> None:
    s = WeeklyMismatchSummary(
        positive_mismatch_count=3,
        non_positive_mismatch_count=7,
        positive_mismatch_direction_accuracy=0.33,
        non_positive_mismatch_direction_accuracy=0.71,
    )
    assert s.positive_mismatch_count == 3


def test_weekly_mismatch_summary_nulls() -> None:
    s = WeeklyMismatchSummary(
        positive_mismatch_count=0,
        non_positive_mismatch_count=0,
        positive_mismatch_direction_accuracy=None,
        non_positive_mismatch_direction_accuracy=None,
    )
    assert s.positive_mismatch_direction_accuracy is None


# ---------------------------------------------------------------------------
# WeeklyCaseExample
# ---------------------------------------------------------------------------


def test_weekly_case_example() -> None:
    ex = WeeklyCaseExample(
        forecast_id="fc_001",
        strategy_kind=StrategyKind.ugh,
        as_of_jst=datetime(2026, 3, 10, 8, 0, 0),
        dominant_state=LifecycleState.fire,
        forecast_direction=ForecastDirection.up,
        realized_direction=ForecastDirection.down,
        expected_close_change_bp=20.0,
        realized_close_change_bp=-15.0,
        close_error_bp=35.0,
        conviction=0.8,
        urgency=0.6,
        disconfirmer_explained=False,
    )
    assert ex.forecast_id == "fc_001"
    assert ex.close_error_bp == pytest.approx(35.0)


def test_weekly_case_example_null_fields() -> None:
    ex = WeeklyCaseExample(
        forecast_id="fc_002",
        strategy_kind=StrategyKind.ugh,
        as_of_jst=datetime(2026, 3, 10, 8, 0, 0),
        dominant_state=None,
        forecast_direction=ForecastDirection.up,
        realized_direction=ForecastDirection.up,
        expected_close_change_bp=5.0,
        realized_close_change_bp=3.0,
        close_error_bp=None,
        conviction=None,
        urgency=None,
        disconfirmer_explained=None,
    )
    assert ex.dominant_state is None
    assert ex.conviction is None
