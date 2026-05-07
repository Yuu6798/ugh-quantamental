"""Tests for FX weekly report generation (Phase 2 Milestone 16)."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EvaluationRecord,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.report_models import WeeklyReportRequest
from ugh_quantamental.fx_protocol.reporting import (
    _WeeklyRow,
    _build_baseline_comparisons,
    _build_grv_fire_summary,
    _build_mismatch_summary,
    _build_state_metrics,
    _build_strategy_metrics,
    _select_false_positive_cases,
    _select_representative_failures,
    _select_representative_successes,
    resolve_completed_window_ends,
)
from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
from ugh_quantamental.schemas.market_svp import StateProbabilities

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 1, 0, 0, 0, tzinfo=_UTC),
    )


def _make_ugh_forecast(
    as_of_jst: datetime,
    window_end_jst: datetime,
    locked_at_utc: datetime,
    forecast_id: str,
    direction: ForecastDirection,
    bp: float,
    dominant_state: LifecycleState = LifecycleState.fire,
    grv_lock: float = 0.5,
    mismatch_px: float = 0.2,
    conviction: float = 0.7,
    urgency: float = 0.5,
) -> ForecastRecord:
    probs = StateProbabilities(
        dormant=0.1, setup=0.2, fire=0.4, expansion=0.15, exhaustion=0.1, failure=0.05
    )
    return ForecastRecord(
        forecast_id=forecast_id,
        forecast_batch_id=f"batch_{as_of_jst.strftime('%Y%m%d')}",
        pair=CurrencyPair.USDJPY,
        strategy_kind=StrategyKind.ugh,
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=locked_at_utc,
        market_data_provenance=_provenance(),
        forecast_direction=direction,
        expected_close_change_bp=bp,
        expected_range=ExpectedRange(low_price=148.0, high_price=152.0),
        dominant_state=dominant_state,
        state_probabilities=probs,
        q_dir=QuestionDirection.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.5,
        grv_raw=0.3,
        grv_lock=grv_lock,
        alignment=0.8,
        e_star=bp,
        mismatch_px=mismatch_px,
        mismatch_sem=0.1,
        conviction=conviction,
        urgency=urgency,
        input_snapshot_ref="snap-ref-1",
        primary_question="Will USDJPY close higher?",
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _make_baseline_forecast(
    as_of_jst: datetime,
    window_end_jst: datetime,
    locked_at_utc: datetime,
    forecast_id: str,
    strategy_kind: StrategyKind,
    direction: ForecastDirection,
    bp: float,
) -> ForecastRecord:
    return ForecastRecord(
        forecast_id=forecast_id,
        forecast_batch_id=f"batch_{as_of_jst.strftime('%Y%m%d')}",
        pair=CurrencyPair.USDJPY,
        strategy_kind=strategy_kind,
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=locked_at_utc,
        market_data_provenance=_provenance(),
        forecast_direction=direction,
        expected_close_change_bp=bp,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _make_outcome(
    window_start_jst: datetime,
    window_end_jst: datetime,
    outcome_id: str,
    realized_open: float = 150.0,
    realized_close: float = 150.8,
) -> OutcomeRecord:
    realized_high = max(realized_open, realized_close) + 0.5
    realized_low = min(realized_open, realized_close) - 0.5
    realized_direction = (
        ForecastDirection.up
        if realized_close > realized_open
        else ForecastDirection.down
        if realized_close < realized_open
        else ForecastDirection.flat
    )
    realized_close_change_bp = (realized_close - realized_open) / realized_open * 10_000
    realized_range_price = realized_high - realized_low
    return OutcomeRecord(
        outcome_id=outcome_id,
        pair=CurrencyPair.USDJPY,
        window_start_jst=window_start_jst,
        window_end_jst=window_end_jst,
        market_data_provenance=_provenance(),
        realized_open=realized_open,
        realized_high=realized_high,
        realized_low=realized_low,
        realized_close=realized_close,
        realized_direction=realized_direction,
        realized_close_change_bp=realized_close_change_bp,
        realized_range_price=realized_range_price,
        event_happened=False,
        event_tags=(),
        schema_version="v1",
        protocol_version="v1",
    )


def _make_ugh_eval(
    forecast: ForecastRecord,
    outcome: OutcomeRecord,
    evaluation_id: str,
    direction_hit: bool,
    close_error_bp: float = 5.0,
    disconfirmer_explained: bool | None = False,
) -> EvaluationRecord:
    return EvaluationRecord(
        evaluation_id=evaluation_id,
        forecast_id=forecast.forecast_id,
        outcome_id=outcome.outcome_id,
        pair=CurrencyPair.USDJPY,
        strategy_kind=StrategyKind.ugh,
        direction_hit=direction_hit,
        range_hit=True,
        close_error_bp=close_error_bp,
        magnitude_error_bp=close_error_bp * 0.5,
        state_proxy_hit=None,
        mismatch_change_bp=2.0,
        realized_state_proxy=None,
        actual_state_change=None,
        disconfirmers_hit=(),
        disconfirmer_explained=disconfirmer_explained,
        evaluated_at_utc=datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _make_baseline_eval(
    forecast: ForecastRecord,
    outcome: OutcomeRecord,
    evaluation_id: str,
    direction_hit: bool,
    close_error_bp: float = 10.0,
) -> EvaluationRecord:
    return EvaluationRecord(
        evaluation_id=evaluation_id,
        forecast_id=forecast.forecast_id,
        outcome_id=outcome.outcome_id,
        pair=CurrencyPair.USDJPY,
        strategy_kind=forecast.strategy_kind,
        direction_hit=direction_hit,
        range_hit=None,
        close_error_bp=close_error_bp,
        magnitude_error_bp=close_error_bp * 0.8,
        disconfirmers_hit=(),
        disconfirmer_explained=None,
        evaluated_at_utc=datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _make_weekly_row(
    strategy_kind: StrategyKind = StrategyKind.ugh,
    direction_hit: bool = True,
    conviction: float = 0.7,
    close_error_bp: float = 5.0,
    dominant_state: LifecycleState = LifecycleState.fire,
    grv_lock: float = 0.5,
    mismatch_px: float = 0.2,
    disconfirmer_explained: bool | None = False,
    forecast_id: str = "fc_001",
    as_of_jst: datetime | None = None,
) -> _WeeklyRow:
    if as_of_jst is None:
        as_of_jst = datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST)
    return _WeeklyRow(
        evaluation_id=f"ev_{forecast_id}",
        forecast_id=forecast_id,
        outcome_id="oc_001",
        strategy_kind=strategy_kind,
        direction_hit=direction_hit,
        range_hit=True if strategy_kind == StrategyKind.ugh else None,
        close_error_bp=close_error_bp,
        magnitude_error_bp=close_error_bp * 0.5,
        disconfirmer_explained=disconfirmer_explained,
        as_of_jst=as_of_jst,
        window_end_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=10.0,
        dominant_state=dominant_state,
        grv_lock=grv_lock,
        mismatch_px=mismatch_px,
        conviction=conviction,
        urgency=0.5,
        realized_direction=ForecastDirection.up if direction_hit else ForecastDirection.down,
        realized_close_change_bp=10.0 if direction_hit else -5.0,
    )


# ---------------------------------------------------------------------------
# resolve_completed_window_ends — pure function tests
# ---------------------------------------------------------------------------


def test_resolve_weekday_after_0800() -> None:
    """On Mon 10:00 JST, business_day_count=5 → last 5 Mon-Fri 08:00 ends."""
    report_at = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)  # Monday
    ends = resolve_completed_window_ends(report_at, 5)
    assert len(ends) == 5
    # Latest should be Monday 2026-03-16 08:00 JST
    assert ends[-1] == datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
    # Previous should be Friday 2026-03-13 08:00 JST
    assert ends[-2] == datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    # All at 08:00
    for w in ends:
        assert w.hour == 8
        assert w.minute == 0


def test_resolve_weekday_before_0800() -> None:
    """On Mon 07:59 JST, Mon 08:00 not yet passed → latest end is Fri 08:00."""
    report_at = datetime(2026, 3, 16, 7, 59, 0, tzinfo=_JST)  # Monday
    ends = resolve_completed_window_ends(report_at, 1)
    assert len(ends) == 1
    # 2026-03-16 is Monday, but before 08:00, so latest completed is Friday 2026-03-13
    assert ends[0] == datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)


def test_resolve_exactly_0800() -> None:
    """At exactly 08:00 on Mon → that Monday is included as a completed window."""
    report_at = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)  # Monday at exactly 08:00
    ends = resolve_completed_window_ends(report_at, 1)
    assert ends[0] == datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)


def test_resolve_on_saturday() -> None:
    """On Saturday, the latest completed window is previous Friday 08:00."""
    # 2026-03-14 is Saturday
    report_at = datetime(2026, 3, 14, 14, 0, 0, tzinfo=_JST)
    ends = resolve_completed_window_ends(report_at, 1)
    assert ends[0] == datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)


def test_resolve_on_sunday() -> None:
    """On Sunday, the latest completed window is previous Friday 08:00."""
    # 2026-03-15 is Sunday
    report_at = datetime(2026, 3, 15, 20, 0, 0, tzinfo=_JST)
    ends = resolve_completed_window_ends(report_at, 2)
    assert ends[-1] == datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    assert ends[-2] == datetime(2026, 3, 12, 8, 0, 0, tzinfo=_JST)


def test_resolve_five_windows_chronological_order() -> None:
    """5 resolved windows are returned oldest-first."""
    report_at = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)
    ends = resolve_completed_window_ends(report_at, 5)
    assert ends[0] < ends[1] < ends[2] < ends[3] < ends[4]


def test_resolve_business_day_count_one() -> None:
    """business_day_count=1 returns exactly one window."""
    report_at = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)
    ends = resolve_completed_window_ends(report_at, 1)
    assert len(ends) == 1


def test_resolve_all_are_weekdays() -> None:
    """All resolved windows fall on Mon-Fri."""
    report_at = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)
    ends = resolve_completed_window_ends(report_at, 10)
    for w in ends:
        assert w.isoweekday() in range(1, 6), f"{w} is not a weekday"


def test_resolve_naive_input_treated_as_jst() -> None:
    """Naive datetime is treated as JST — same result as explicit JST-aware."""
    naive = datetime(2026, 3, 16, 10, 0, 0)  # no tzinfo
    aware = datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST)
    naive_ends = resolve_completed_window_ends(naive, 3)
    aware_ends = resolve_completed_window_ends(aware, 3)
    assert naive_ends == aware_ends


def test_resolve_utc_aware_input() -> None:
    """UTC-aware input is correctly converted to JST before resolving."""
    # 2026-03-16 01:00 UTC = 2026-03-16 10:00 JST → Monday at 10:00 JST
    utc_at = datetime(2026, 3, 16, 1, 0, 0, tzinfo=timezone.utc)
    ends = resolve_completed_window_ends(utc_at, 1)
    assert ends[0] == datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)


# ---------------------------------------------------------------------------
# Strategy metrics (pure unit tests, no DB)
# ---------------------------------------------------------------------------


def test_strategy_metrics_ugh_accuracy() -> None:
    rows = [
        _make_weekly_row(direction_hit=True, close_error_bp=5.0, forecast_id="f1"),
        _make_weekly_row(direction_hit=True, close_error_bp=3.0, forecast_id="f2"),
        _make_weekly_row(direction_hit=False, close_error_bp=20.0, forecast_id="f3"),
    ]
    m = _build_strategy_metrics(rows, StrategyKind.ugh)
    assert m.forecast_count == 3
    assert m.direction_hit_count == 2
    assert m.direction_accuracy == pytest.approx(2 / 3)
    assert m.range_evaluable_count == 3  # all UGH rows have range_hit set
    assert m.range_hit_count == 3
    assert m.mean_abs_close_error_bp == pytest.approx((5.0 + 3.0 + 20.0) / 3)


def test_strategy_metrics_baseline_zero_range() -> None:
    rows = [
        _make_weekly_row(
            strategy_kind=StrategyKind.baseline_random_walk,
            direction_hit=True,
            close_error_bp=15.0,
            forecast_id="f1",
        ),
        _make_weekly_row(
            strategy_kind=StrategyKind.baseline_random_walk,
            direction_hit=False,
            close_error_bp=25.0,
            forecast_id="f2",
        ),
    ]
    m = _build_strategy_metrics(rows, StrategyKind.baseline_random_walk)
    assert m.range_evaluable_count == 0
    assert m.range_hit_count == 0
    assert m.range_hit_rate is None
    assert m.direction_accuracy == pytest.approx(0.5)


def test_strategy_metrics_empty() -> None:
    m = _build_strategy_metrics([], StrategyKind.ugh)
    assert m.forecast_count == 0
    assert m.direction_accuracy is None
    assert m.mean_abs_close_error_bp is None


# ---------------------------------------------------------------------------
# Baseline comparison (pure unit tests)
# ---------------------------------------------------------------------------


def test_baseline_comparison_delta() -> None:
    rows = (
        [_make_weekly_row(strategy_kind=StrategyKind.ugh, direction_hit=True, forecast_id=f"f{i}") for i in range(4)]
        + [
            _make_weekly_row(
                strategy_kind=StrategyKind.baseline_random_walk,
                direction_hit=False,
                close_error_bp=20.0,
                forecast_id="fb1",
            ),
            _make_weekly_row(
                strategy_kind=StrategyKind.baseline_random_walk,
                direction_hit=True,
                close_error_bp=15.0,
                forecast_id="fb2",
            ),
        ]
    )
    ugh_metrics = _build_strategy_metrics(rows, StrategyKind.ugh)
    comps = _build_baseline_comparisons(rows, ugh_metrics)
    rw = next(c for c in comps if c.baseline_strategy_kind == StrategyKind.baseline_random_walk)
    # UGH accuracy = 1.0, RW accuracy = 0.5 → delta = -0.5
    assert rw.direction_accuracy_delta_vs_ugh == pytest.approx(-0.5)


def test_baseline_comparison_null_when_no_data() -> None:
    rows: list[_WeeklyRow] = []
    ugh_metrics = _build_strategy_metrics(rows, StrategyKind.ugh)
    comps = _build_baseline_comparisons(rows, ugh_metrics)
    for c in comps:
        assert c.direction_accuracy_delta_vs_ugh is None
        assert c.mean_abs_close_error_bp_delta_vs_ugh is None


# ---------------------------------------------------------------------------
# State metrics (pure unit tests)
# ---------------------------------------------------------------------------


def test_state_metrics_groups() -> None:
    rows = [
        _make_weekly_row(dominant_state=LifecycleState.fire, direction_hit=True, forecast_id="f1"),
        _make_weekly_row(dominant_state=LifecycleState.fire, direction_hit=False, forecast_id="f2"),
        _make_weekly_row(
            dominant_state=LifecycleState.expansion, direction_hit=True, forecast_id="f3"
        ),
    ]
    metrics = _build_state_metrics(rows)
    states = {m.dominant_state for m in metrics}
    assert LifecycleState.fire in states
    assert LifecycleState.expansion in states

    fire_m = next(m for m in metrics if m.dominant_state == LifecycleState.fire)
    assert fire_m.forecast_count == 2
    assert fire_m.direction_accuracy == pytest.approx(0.5)

    exp_m = next(m for m in metrics if m.dominant_state == LifecycleState.expansion)
    assert exp_m.direction_accuracy == pytest.approx(1.0)


def test_state_metrics_empty() -> None:
    assert _build_state_metrics([]) == ()


# ---------------------------------------------------------------------------
# GRV fire summary (pure unit tests)
# ---------------------------------------------------------------------------


def test_grv_fire_summary_counts() -> None:
    rows = [
        _make_weekly_row(dominant_state=LifecycleState.fire, grv_lock=0.8, direction_hit=True, forecast_id="f1"),
        _make_weekly_row(dominant_state=LifecycleState.fire, grv_lock=0.6, direction_hit=False, forecast_id="f2"),
        _make_weekly_row(dominant_state=LifecycleState.setup, grv_lock=0.3, direction_hit=True, forecast_id="f3"),
    ]
    s = _build_grv_fire_summary(rows)
    assert s.fire_count == 2
    assert s.non_fire_count == 1
    assert s.mean_grv_lock_fire == pytest.approx(0.7)
    assert s.mean_grv_lock_non_fire == pytest.approx(0.3)
    assert s.fire_direction_accuracy == pytest.approx(0.5)


def test_grv_fire_summary_no_fire_rows() -> None:
    rows = [
        _make_weekly_row(dominant_state=LifecycleState.setup, forecast_id="f1"),
    ]
    s = _build_grv_fire_summary(rows)
    assert s.fire_count == 0
    assert s.fire_direction_accuracy is None
    assert s.mean_grv_lock_fire is None


# ---------------------------------------------------------------------------
# Mismatch summary (pure unit tests)
# ---------------------------------------------------------------------------


def test_mismatch_summary_split() -> None:
    rows = [
        _make_weekly_row(mismatch_px=5.0, direction_hit=True, forecast_id="f1"),
        _make_weekly_row(mismatch_px=3.0, direction_hit=False, forecast_id="f2"),
        _make_weekly_row(mismatch_px=-2.0, direction_hit=True, forecast_id="f3"),
        _make_weekly_row(mismatch_px=0.0, direction_hit=False, forecast_id="f4"),
    ]
    s = _build_mismatch_summary(rows)
    assert s.positive_mismatch_count == 2
    assert s.non_positive_mismatch_count == 2
    assert s.positive_mismatch_direction_accuracy == pytest.approx(0.5)
    assert s.non_positive_mismatch_direction_accuracy == pytest.approx(0.5)


def test_mismatch_summary_excludes_none() -> None:
    rows = [
        _make_weekly_row(mismatch_px=None, direction_hit=True, forecast_id="f1"),
        _make_weekly_row(mismatch_px=1.0, direction_hit=True, forecast_id="f2"),
    ]
    # Set mismatch_px=None explicitly
    rows[0] = _WeeklyRow(
        **{**rows[0].__dict__, "mismatch_px": None}  # type: ignore[arg-type]
    )
    s = _build_mismatch_summary(rows)
    assert s.positive_mismatch_count == 1
    assert s.non_positive_mismatch_count == 0


# ---------------------------------------------------------------------------
# Case example selection (pure unit tests)
# ---------------------------------------------------------------------------


def test_false_positive_sort_desc_conviction_then_desc_error() -> None:
    rows = [
        _make_weekly_row(direction_hit=False, conviction=0.9, close_error_bp=10.0, forecast_id="f1"),
        _make_weekly_row(direction_hit=False, conviction=0.9, close_error_bp=20.0, forecast_id="f2"),
        _make_weekly_row(direction_hit=False, conviction=0.5, close_error_bp=50.0, forecast_id="f3"),
        _make_weekly_row(direction_hit=True, conviction=0.99, close_error_bp=1.0, forecast_id="f4"),  # excluded
    ]
    cases = _select_false_positive_cases(rows, max_examples=2)
    assert len(cases) == 2
    # First: highest conviction (0.9), highest error (20.0)
    assert cases[0].forecast_id == "f2"
    # Second: conviction 0.9, error 10.0
    assert cases[1].forecast_id == "f1"


def test_representative_successes_sort() -> None:
    rows = [
        _make_weekly_row(direction_hit=True, conviction=0.9, close_error_bp=2.0, forecast_id="f1"),
        _make_weekly_row(direction_hit=True, conviction=0.9, close_error_bp=1.0, forecast_id="f2"),
        _make_weekly_row(direction_hit=False, conviction=0.99, close_error_bp=0.0, forecast_id="f3"),  # excluded
    ]
    cases = _select_representative_successes(rows, max_examples=3)
    assert len(cases) == 2
    # Sort: desc conviction, asc close_error → f2 (0.9, 1.0) before f1 (0.9, 2.0)
    assert cases[0].forecast_id == "f2"
    assert cases[1].forecast_id == "f1"


def test_representative_failures_sort_desc_error() -> None:
    rows = [
        _make_weekly_row(direction_hit=False, conviction=0.5, close_error_bp=30.0, forecast_id="f1"),
        _make_weekly_row(direction_hit=False, conviction=0.9, close_error_bp=10.0, forecast_id="f2"),
        _make_weekly_row(direction_hit=True, conviction=0.99, close_error_bp=1.0, forecast_id="f3"),  # excluded
    ]
    cases = _select_representative_failures(rows, max_examples=3)
    assert len(cases) == 2
    # Sort: desc close_error → f1 (30.0) before f2 (10.0)
    assert cases[0].forecast_id == "f1"
    assert cases[1].forecast_id == "f2"


def test_case_examples_respect_max_examples() -> None:
    rows = [
        _make_weekly_row(direction_hit=False, forecast_id=f"f{i}") for i in range(10)
    ]
    cases = _select_false_positive_cases(rows, max_examples=3)
    assert len(cases) == 3


# ---------------------------------------------------------------------------
# Integration tests with in-memory SQLite
# ---------------------------------------------------------------------------

if HAS_SQLALCHEMY:
    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine, create_session_factory
    from ugh_quantamental.persistence.models import (
        FxEvaluationRecord as FxEvalORM,
        FxForecastRecord as FxFcORM,
        FxOutcomeRecord as FxOcORM,
    )
    from ugh_quantamental.persistence.serializers import dump_model_json


def _jst_to_naive_utc(dt: datetime) -> datetime:
    """Convert JST datetime to naive UTC for ORM column insertion."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_JST)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _to_naive_utc_or_keep(dt: datetime) -> datetime:
    """For ORM columns that store datetime(timezone=False)."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


# 5 business days (as_of, window_end) pairs for the test week ending 2026-03-16.
_WINDOWS: list[tuple[datetime, datetime]] = [
    (datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST), datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)),   # Mon→Tue
    (datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST), datetime(2026, 3, 11, 8, 0, 0, tzinfo=_JST)),  # Tue→Wed
    (datetime(2026, 3, 11, 8, 0, 0, tzinfo=_JST), datetime(2026, 3, 12, 8, 0, 0, tzinfo=_JST)),  # Wed→Thu
    (datetime(2026, 3, 12, 8, 0, 0, tzinfo=_JST), datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)),  # Thu→Fri
    (datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST), datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)),  # Fri→Mon
]


@pytest.fixture()
def db_session():
    """In-memory SQLite session with all tables created."""
    if not HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")
    engine = create_db_engine()
    create_all_tables(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        yield session


def _seed_window(
    session: Any,
    as_of_jst: datetime,
    window_end_jst: datetime,
    window_idx: int,
    ugh_direction_hit: bool = True,
    realized_close: float = 150.8,  # > 150.0 = up direction
) -> None:
    """Insert ORM records for one complete forecast-outcome-evaluation window."""
    from datetime import timedelta

    # as_of_jst 08:00 JST = 23:00 UTC previous calendar day.
    # locked_at_utc must be strictly before that, so use 10 hours earlier.
    locked_at_utc_aware = as_of_jst.astimezone(_UTC) - timedelta(hours=10)

    ugh_fc = _make_ugh_forecast(
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=locked_at_utc_aware,
        forecast_id=f"ugh_{window_idx}",
        direction=ForecastDirection.up,
        bp=10.0,
        dominant_state=LifecycleState.fire if window_idx % 2 == 0 else LifecycleState.setup,
        grv_lock=0.6,
        mismatch_px=2.0 if window_idx % 2 == 0 else -1.0,
        conviction=0.8 - window_idx * 0.05,
        urgency=0.5,
    )
    rw_fc = _make_baseline_forecast(
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=locked_at_utc_aware,
        forecast_id=f"rw_{window_idx}",
        strategy_kind=StrategyKind.baseline_random_walk,
        direction=ForecastDirection.flat,
        bp=0.0,
    )
    pdd_fc = _make_baseline_forecast(
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=locked_at_utc_aware,
        forecast_id=f"pdd_{window_idx}",
        strategy_kind=StrategyKind.baseline_prev_day_direction,
        direction=ForecastDirection.up,
        bp=8.0,
    )
    st_fc = _make_baseline_forecast(
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        locked_at_utc=locked_at_utc_aware,
        forecast_id=f"st_{window_idx}",
        strategy_kind=StrategyKind.baseline_simple_technical,
        direction=ForecastDirection.up,
        bp=12.0,
    )

    outcome = _make_outcome(
        window_start_jst=as_of_jst,
        window_end_jst=window_end_jst,
        outcome_id=f"oc_{window_idx}",
        realized_open=150.0,
        realized_close=realized_close,
    )

    window_end_naive_utc = _jst_to_naive_utc(window_end_jst)
    as_of_naive_utc = _jst_to_naive_utc(as_of_jst)

    # Insert forecast records.
    for fc, sk in [
        (ugh_fc, "ugh"),
        (rw_fc, "baseline_random_walk"),
        (pdd_fc, "baseline_prev_day_direction"),
        (st_fc, "baseline_simple_technical"),
    ]:
        session.add(
            FxFcORM(
                forecast_id=fc.forecast_id,
                forecast_batch_id=f"batch_{window_idx}",
                pair="USDJPY",
                strategy_kind=sk,
                as_of_jst=as_of_naive_utc,
                window_end_jst=window_end_naive_utc,
                protocol_version="v1",
                payload_json=dump_model_json(fc),
            )
        )

    # Insert outcome record.
    session.add(
        FxOcORM(
            outcome_id=outcome.outcome_id,
            pair="USDJPY",
            window_start_jst=as_of_naive_utc,
            window_end_jst=window_end_naive_utc,
            protocol_version="v1",
            payload_json=dump_model_json(outcome),
        )
    )

    # Insert evaluation records.
    realized_dir = outcome.realized_direction
    ugh_hit = ugh_direction_hit
    pdd_hit = ForecastDirection.up == realized_dir

    ugh_eval = _make_ugh_eval(ugh_fc, outcome, f"ev_ugh_{window_idx}", ugh_hit, close_error_bp=5.0 + window_idx)
    rw_eval = _make_baseline_eval(rw_fc, outcome, f"ev_rw_{window_idx}", direction_hit=False, close_error_bp=15.0)
    pdd_eval = _make_baseline_eval(pdd_fc, outcome, f"ev_pdd_{window_idx}", direction_hit=pdd_hit, close_error_bp=8.0)
    st_eval = _make_baseline_eval(st_fc, outcome, f"ev_st_{window_idx}", direction_hit=pdd_hit, close_error_bp=9.0)

    for ev in [ugh_eval, rw_eval, pdd_eval, st_eval]:
        session.add(
            FxEvalORM(
                evaluation_id=ev.evaluation_id,
                forecast_id=ev.forecast_id,
                outcome_id=ev.outcome_id,
                pair="USDJPY",
                strategy_kind=ev.strategy_kind.value,
                window_start_jst=as_of_naive_utc,
                window_end_jst=window_end_naive_utc,
                protocol_version="v1",
                payload_json=dump_model_json(ev),
            )
        )

    session.flush()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_five_windows(db_session: Any) -> None:
    """Full weekly report over 5 seeded windows."""
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    for i, (as_of, window_end) in enumerate(_WINDOWS):
        _seed_window(db_session, as_of, window_end, i, ugh_direction_hit=(i % 2 == 0))

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
        max_examples=3,
    )
    result = run_weekly_report(db_session, request)

    assert result.pair == CurrencyPair.USDJPY
    assert result.requested_window_count == 5
    assert result.included_window_count == 5
    assert result.missing_window_count == 0
    assert len(result.window_end_jst_values) == 5
    # v2: 5 UGH-class strategies (legacy ugh + 4 v2 variants) + 3 baselines = 8 metrics rows.
    # The seeded fixture only emits legacy ``ugh`` rows so v2 variants appear with
    # forecast_count=0; this is the expected v1-era report shape until step 7.5
    # stratification adds a theory_version filter.
    assert len(result.strategy_metrics) == 8
    # 3 baseline comparisons (one per baseline; UGH is the comparison anchor).
    assert len(result.baseline_comparisons) == 3
    # The fixture seeds legacy ``ugh`` rows; the canonical UGH metrics anchor
    # therefore resolves to ``ugh`` (first UGH-class kind with non-zero count).
    ugh_m = next(m for m in result.strategy_metrics if m.strategy_kind == StrategyKind.ugh)
    assert ugh_m.forecast_count == 5


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_missing_windows(db_session: Any) -> None:
    """Only 2 of 5 windows have data → missing_window_count = 3."""
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    # Seed only first 2 windows.
    for i in range(2):
        _seed_window(db_session, _WINDOWS[i][0], _WINDOWS[i][1], i)

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
        max_examples=3,
    )
    result = run_weekly_report(db_session, request)

    assert result.included_window_count == 2
    assert result.missing_window_count == 3


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_zero_windows_raises(db_session: Any) -> None:
    """No data at all → ValueError."""
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
    )
    with pytest.raises(ValueError, match="No evaluation data found"):
        run_weekly_report(db_session, request)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_read_only(db_session: Any) -> None:
    """run_weekly_report must not write any new records."""
    from sqlalchemy import func, select

    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    # Seed one window.
    _seed_window(db_session, _WINDOWS[0][0], _WINDOWS[0][1], 0)

    # Count records before the report.
    count_before = (
        db_session.execute(select(func.count()).select_from(FxEvalORM)).scalar()
        + db_session.execute(select(func.count()).select_from(FxFcORM)).scalar()
        + db_session.execute(select(func.count()).select_from(FxOcORM)).scalar()
    )

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
    )
    run_weekly_report(db_session, request)

    # Count records after the report — must be the same.
    count_after = (
        db_session.execute(select(func.count()).select_from(FxEvalORM)).scalar()
        + db_session.execute(select(func.count()).select_from(FxFcORM)).scalar()
        + db_session.execute(select(func.count()).select_from(FxOcORM)).scalar()
    )
    assert count_after == count_before


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_strategy_metrics_accuracy(db_session: Any) -> None:
    """UGH direction_accuracy computed correctly from seeded data."""
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    # Seed 4 windows: 3 hits, 1 miss.
    _seed_window(db_session, _WINDOWS[0][0], _WINDOWS[0][1], 0, ugh_direction_hit=True)
    _seed_window(db_session, _WINDOWS[1][0], _WINDOWS[1][1], 1, ugh_direction_hit=True)
    _seed_window(db_session, _WINDOWS[2][0], _WINDOWS[2][1], 2, ugh_direction_hit=True)
    _seed_window(db_session, _WINDOWS[3][0], _WINDOWS[3][1], 3, ugh_direction_hit=False)

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
    )
    result = run_weekly_report(db_session, request)

    ugh_m = next(m for m in result.strategy_metrics if m.strategy_kind == StrategyKind.ugh)
    assert ugh_m.forecast_count == 4
    assert ugh_m.direction_hit_count == 3
    assert ugh_m.direction_accuracy == pytest.approx(0.75)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_baseline_comparisons_present(db_session: Any) -> None:
    """Baseline comparisons are generated for all 3 baseline strategies."""
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    _seed_window(db_session, _WINDOWS[0][0], _WINDOWS[0][1], 0)

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
    )
    result = run_weekly_report(db_session, request)

    kinds = {c.baseline_strategy_kind for c in result.baseline_comparisons}
    assert StrategyKind.baseline_random_walk in kinds
    assert StrategyKind.baseline_prev_day_direction in kinds
    assert StrategyKind.baseline_simple_technical in kinds


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_run_weekly_report_false_positive_cases_ordered(db_session: Any) -> None:
    """False-positive cases (direction_hit=False) are in the result."""
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    # Seed one window with a miss.
    _seed_window(db_session, _WINDOWS[0][0], _WINDOWS[0][1], 0, ugh_direction_hit=False)

    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
        max_examples=3,
    )
    result = run_weekly_report(db_session, request)

    assert len(result.false_positive_cases) >= 1
    for case in result.false_positive_cases:
        assert case.strategy_kind == StrategyKind.ugh


# ---------------------------------------------------------------------------
# Regression tests for review fixes
# ---------------------------------------------------------------------------


def test_case_sort_deterministic_on_equal_keys_false_positive() -> None:
    """Rows with identical conviction/error are broken by forecast_id — output is deterministic."""
    rows = [
        _make_weekly_row(direction_hit=False, conviction=0.7, close_error_bp=10.0, forecast_id="z_last"),
        _make_weekly_row(direction_hit=False, conviction=0.7, close_error_bp=10.0, forecast_id="a_first"),
    ]
    cases_a = _select_false_positive_cases(rows, max_examples=2)
    cases_b = _select_false_positive_cases(list(reversed(rows)), max_examples=2)
    # Order must be identical regardless of input order: tie broken by forecast_id ascending.
    assert cases_a[0].forecast_id == cases_b[0].forecast_id == "a_first"
    assert cases_a[1].forecast_id == cases_b[1].forecast_id == "z_last"


def test_case_sort_deterministic_on_equal_keys_successes() -> None:
    """Representative successes tie-break by forecast_id for deterministic output."""
    rows = [
        _make_weekly_row(direction_hit=True, conviction=0.7, close_error_bp=5.0, forecast_id="z_last"),
        _make_weekly_row(direction_hit=True, conviction=0.7, close_error_bp=5.0, forecast_id="a_first"),
    ]
    cases_a = _select_representative_successes(rows, max_examples=2)
    cases_b = _select_representative_successes(list(reversed(rows)), max_examples=2)
    assert cases_a[0].forecast_id == cases_b[0].forecast_id == "a_first"
    assert cases_a[1].forecast_id == cases_b[1].forecast_id == "z_last"


def test_case_sort_deterministic_on_equal_keys_failures() -> None:
    """Representative failures tie-break by forecast_id for deterministic output."""
    rows = [
        _make_weekly_row(direction_hit=False, conviction=0.7, close_error_bp=10.0, forecast_id="z_last"),
        _make_weekly_row(direction_hit=False, conviction=0.7, close_error_bp=10.0, forecast_id="a_first"),
    ]
    cases_a = _select_representative_failures(rows, max_examples=2)
    cases_b = _select_representative_failures(list(reversed(rows)), max_examples=2)
    assert cases_a[0].forecast_id == cases_b[0].forecast_id == "a_first"
    assert cases_a[1].forecast_id == cases_b[1].forecast_id == "z_last"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_included_window_count_uses_eval_records_not_join(db_session: Any) -> None:
    """Window inclusion is based on FxEvaluationRecord rows, not on the fc/oc join result.

    If an evaluation record exists but its forecast is absent from FxForecastRecord
    (a dangling eval), the window must still be counted as included so that the fc/oc
    join filter cannot cause a window to be misclassified as missing.
    """
    from ugh_quantamental.fx_protocol.reporting import run_weekly_report

    # Seed one full window so we have eval + forecast + outcome.
    _seed_window(db_session, _WINDOWS[0][0], _WINDOWS[0][1], 0)

    # Now orphan all forecast records for that window by deleting them.
    # This simulates the "dangling evaluation record" scenario.
    from sqlalchemy import delete

    db_session.execute(delete(FxFcORM).where(FxFcORM.forecast_batch_id == "batch_0"))
    db_session.flush()

    # The window still has evaluation records in the DB even though forecasts are gone.
    # included_window_count must be 1 (not 0), and run_weekly_report must not raise.
    request = WeeklyReportRequest(
        pair=CurrencyPair.USDJPY,
        report_generated_at_jst=datetime(2026, 3, 16, 10, 0, 0, tzinfo=_JST),
        business_day_count=5,
    )
    result = run_weekly_report(db_session, request)
    assert result.included_window_count == 1
    assert result.missing_window_count == 4
    # No joinable rows → strategy_metrics have forecast_count = 0 (metrics are empty)
    ugh_m = next(m for m in result.strategy_metrics if m.strategy_kind == StrategyKind.ugh)
    assert ugh_m.forecast_count == 0
