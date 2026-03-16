"""Read-only weekly FX report generation (Phase 2 Milestone 16)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.models import (
    EvaluationRecord,
    ForecastDirection,
    ForecastRecord,
    OutcomeRecord,
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
    WeeklyReportResult,
)
from ugh_quantamental.schemas.enums import LifecycleState

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_JST = ZoneInfo("Asia/Tokyo")

_BASELINE_KINDS: tuple[StrategyKind, ...] = (
    StrategyKind.baseline_random_walk,
    StrategyKind.baseline_prev_day_direction,
    StrategyKind.baseline_simple_technical,
)

_ALL_STRATEGY_KINDS: tuple[StrategyKind, ...] = (StrategyKind.ugh, *_BASELINE_KINDS)


# ---------------------------------------------------------------------------
# Internal row type
# ---------------------------------------------------------------------------


@dataclass
class _WeeklyRow:
    """Internal joined row combining evaluation, forecast, and outcome data."""

    # Evaluation
    evaluation_id: str
    forecast_id: str
    outcome_id: str
    strategy_kind: StrategyKind
    direction_hit: bool
    range_hit: bool | None
    close_error_bp: float | None
    magnitude_error_bp: float | None
    disconfirmer_explained: bool | None
    # Forecast
    as_of_jst: datetime
    window_end_jst: datetime
    forecast_direction: ForecastDirection
    expected_close_change_bp: float
    dominant_state: LifecycleState | None
    grv_lock: float | None
    mismatch_px: float | None
    conviction: float | None
    urgency: float | None
    # Outcome
    realized_direction: ForecastDirection
    realized_close_change_bp: float


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _to_jst_naive(dt: datetime) -> datetime:
    """Normalize *dt* to a naive JST datetime for canonical comparison."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(_JST)
    return dt.replace(tzinfo=None)


def _jst_to_naive_utc(dt: datetime) -> datetime:
    """Convert a JST datetime to naive UTC for SQLAlchemy DateTime(timezone=False) queries."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_JST)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _safe_mean(values: list[float]) -> float | None:
    """Return the arithmetic mean of *values*, or ``None`` if the list is empty."""
    if not values:
        return None
    return sum(values) / len(values)


def _direction_accuracy(rows: list[_WeeklyRow]) -> float | None:
    """Hit rate over *rows*; ``None`` if empty."""
    if not rows:
        return None
    return sum(1 for r in rows if r.direction_hit) / len(rows)


# ---------------------------------------------------------------------------
# Public: window resolution
# ---------------------------------------------------------------------------


def resolve_completed_window_ends(
    report_generated_at_jst: datetime,
    business_day_count: int,
) -> tuple[datetime, ...]:
    """Return the most recent ``business_day_count`` completed protocol window-end timestamps.

    A completed window-end is a Mon–Fri 08:00 JST timestamp that is ``<=``
    ``report_generated_at_jst``.  Results are returned in chronological order
    (oldest first).

    Parameters
    ----------
    report_generated_at_jst:
        The moment at which the report is generated.  Timezone-aware values
        are converted to JST; naive values are treated as already in JST.
    business_day_count:
        How many completed window-end timestamps to return.  Must be >= 1.
    """
    if report_generated_at_jst.tzinfo is not None:
        ts = report_generated_at_jst.astimezone(_JST)
    else:
        ts = report_generated_at_jst.replace(tzinfo=_JST)

    # Anchor: 08:00 JST on the same calendar date as ts.
    candidate = ts.replace(hour=8, minute=0, second=0, microsecond=0)
    # If the anchor is after ts, the today's 08:00 window has not yet opened;
    # step back one calendar day.
    if candidate > ts:
        candidate -= timedelta(days=1)

    results: list[datetime] = []
    while len(results) < business_day_count:
        if candidate.isoweekday() in range(1, 6):  # Mon–Fri
            results.append(candidate)
        candidate -= timedelta(days=1)

    # Return in chronological order (oldest first).
    return tuple(reversed(results))


# ---------------------------------------------------------------------------
# Private: data loading
# ---------------------------------------------------------------------------


def _load_weekly_rows(
    session: "Session",
    pair_value: str,
    naive_utc_windows: tuple[datetime, ...],
) -> list[_WeeklyRow]:
    """Load and join evaluation, forecast, and outcome records for the given windows.

    All three record types are fetched in batch queries (no N+1).
    Records with missing forecast or outcome counterparts are silently skipped.
    """
    from sqlalchemy import select

    from ugh_quantamental.persistence.models import (
        FxEvaluationRecord,
        FxForecastRecord,
        FxOutcomeRecord,
    )

    # 1. Evaluation records for this pair + windows.
    eval_orms = list(
        session.execute(
            select(FxEvaluationRecord).where(
                FxEvaluationRecord.pair == pair_value,
                FxEvaluationRecord.window_end_jst.in_(naive_utc_windows),
            )
        ).scalars()
    )
    if not eval_orms:
        return []

    # 2. Forecast records (one batch query).
    forecast_ids = {r.forecast_id for r in eval_orms}
    forecast_map: dict[str, ForecastRecord] = {
        r.forecast_id: ForecastRecord.model_validate(r.payload_json)
        for r in session.execute(
            select(FxForecastRecord).where(FxForecastRecord.forecast_id.in_(forecast_ids))
        ).scalars()
    }

    # 3. Outcome records (one batch query).
    outcome_ids = {r.outcome_id for r in eval_orms}
    outcome_map: dict[str, OutcomeRecord] = {
        r.outcome_id: OutcomeRecord.model_validate(r.payload_json)
        for r in session.execute(
            select(FxOutcomeRecord).where(FxOutcomeRecord.outcome_id.in_(outcome_ids))
        ).scalars()
    }

    rows: list[_WeeklyRow] = []
    for eval_orm in eval_orms:
        ev = EvaluationRecord.model_validate(eval_orm.payload_json)
        fc = forecast_map.get(eval_orm.forecast_id)
        oc = outcome_map.get(eval_orm.outcome_id)
        if fc is None or oc is None:
            continue
        rows.append(
            _WeeklyRow(
                evaluation_id=ev.evaluation_id,
                forecast_id=ev.forecast_id,
                outcome_id=ev.outcome_id,
                strategy_kind=ev.strategy_kind,
                direction_hit=ev.direction_hit,
                range_hit=ev.range_hit,
                close_error_bp=ev.close_error_bp,
                magnitude_error_bp=ev.magnitude_error_bp,
                disconfirmer_explained=ev.disconfirmer_explained,
                as_of_jst=fc.as_of_jst,
                window_end_jst=fc.window_end_jst,
                forecast_direction=fc.forecast_direction,
                expected_close_change_bp=fc.expected_close_change_bp,
                dominant_state=fc.dominant_state,
                grv_lock=fc.grv_lock,
                mismatch_px=fc.mismatch_px,
                conviction=fc.conviction,
                urgency=fc.urgency,
                realized_direction=oc.realized_direction,
                realized_close_change_bp=oc.realized_close_change_bp,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Private: metric builders
# ---------------------------------------------------------------------------


def _build_strategy_metrics(
    rows: list[_WeeklyRow],
    strategy_kind: StrategyKind,
) -> StrategyWeeklyMetrics:
    """Compute weekly metrics for one strategy kind."""
    sk_rows = [r for r in rows if r.strategy_kind == strategy_kind]
    forecast_count = len(sk_rows)

    direction_evaluable_count = forecast_count  # direction_hit is never None
    direction_hit_count = sum(1 for r in sk_rows if r.direction_hit)
    direction_accuracy = (
        direction_hit_count / direction_evaluable_count
        if direction_evaluable_count > 0
        else None
    )

    is_ugh = strategy_kind == StrategyKind.ugh
    if is_ugh:
        range_rows = [r for r in sk_rows if r.range_hit is not None]
        range_evaluable_count = len(range_rows)
        range_hit_count = sum(1 for r in range_rows if r.range_hit)
        range_hit_rate = (
            range_hit_count / range_evaluable_count if range_evaluable_count > 0 else None
        )
    else:
        range_evaluable_count = 0
        range_hit_count = 0
        range_hit_rate = None

    mean_abs_close_error_bp = _safe_mean(
        [r.close_error_bp for r in sk_rows if r.close_error_bp is not None]
    )
    mean_abs_magnitude_error_bp = _safe_mean(
        [r.magnitude_error_bp for r in sk_rows if r.magnitude_error_bp is not None]
    )

    return StrategyWeeklyMetrics(
        strategy_kind=strategy_kind,
        forecast_count=forecast_count,
        direction_evaluable_count=direction_evaluable_count,
        direction_hit_count=direction_hit_count,
        direction_accuracy=direction_accuracy,
        range_evaluable_count=range_evaluable_count,
        range_hit_count=range_hit_count,
        range_hit_rate=range_hit_rate,
        mean_abs_close_error_bp=mean_abs_close_error_bp,
        mean_abs_magnitude_error_bp=mean_abs_magnitude_error_bp,
    )


def _build_baseline_comparisons(
    rows: list[_WeeklyRow],
    ugh_metrics: StrategyWeeklyMetrics,
) -> tuple[BaselineWeeklyComparison, ...]:
    """Compute direction-accuracy and close-error deltas for each baseline vs UGH."""
    results: list[BaselineWeeklyComparison] = []
    for bl_kind in _BASELINE_KINDS:
        bl = _build_strategy_metrics(rows, bl_kind)

        dir_delta: float | None
        if ugh_metrics.direction_accuracy is not None and bl.direction_accuracy is not None:
            dir_delta = bl.direction_accuracy - ugh_metrics.direction_accuracy
        else:
            dir_delta = None

        err_delta: float | None
        if (
            ugh_metrics.mean_abs_close_error_bp is not None
            and bl.mean_abs_close_error_bp is not None
        ):
            err_delta = bl.mean_abs_close_error_bp - ugh_metrics.mean_abs_close_error_bp
        else:
            err_delta = None

        results.append(
            BaselineWeeklyComparison(
                baseline_strategy_kind=bl_kind,
                direction_accuracy_delta_vs_ugh=dir_delta,
                mean_abs_close_error_bp_delta_vs_ugh=err_delta,
            )
        )
    return tuple(results)


def _build_state_metrics(ugh_rows: list[_WeeklyRow]) -> tuple[StateWeeklyMetrics, ...]:
    """Compute per-dominant-state metrics for UGH rows."""
    groups: dict[LifecycleState, list[_WeeklyRow]] = defaultdict(list)
    for row in ugh_rows:
        if row.dominant_state is not None:
            groups[row.dominant_state].append(row)

    results: list[StateWeeklyMetrics] = []
    for state in sorted(groups, key=lambda s: s.value):
        state_rows = groups[state]
        close_errors = [r.close_error_bp for r in state_rows if r.close_error_bp is not None]
        results.append(
            StateWeeklyMetrics(
                dominant_state=state,
                forecast_count=len(state_rows),
                direction_accuracy=_direction_accuracy(state_rows),
                mean_abs_close_error_bp=_safe_mean(close_errors),
            )
        )
    return tuple(results)


def _build_grv_fire_summary(ugh_rows: list[_WeeklyRow]) -> WeeklyGrvFireSummary:
    """Compute GRV-lock and directional-accuracy split by fire vs non-fire state."""
    fire_rows = [r for r in ugh_rows if r.dominant_state == LifecycleState.fire]
    non_fire_rows = [r for r in ugh_rows if r.dominant_state != LifecycleState.fire]

    return WeeklyGrvFireSummary(
        fire_count=len(fire_rows),
        non_fire_count=len(non_fire_rows),
        mean_grv_lock_fire=_safe_mean(
            [r.grv_lock for r in fire_rows if r.grv_lock is not None]
        ),
        mean_grv_lock_non_fire=_safe_mean(
            [r.grv_lock for r in non_fire_rows if r.grv_lock is not None]
        ),
        fire_direction_accuracy=_direction_accuracy(fire_rows),
    )


def _build_mismatch_summary(ugh_rows: list[_WeeklyRow]) -> WeeklyMismatchSummary:
    """Compute directional-accuracy split by sign of mismatch_px."""
    pos_rows = [r for r in ugh_rows if r.mismatch_px is not None and r.mismatch_px > 0]
    non_pos_rows = [r for r in ugh_rows if r.mismatch_px is not None and r.mismatch_px <= 0]

    return WeeklyMismatchSummary(
        positive_mismatch_count=len(pos_rows),
        non_positive_mismatch_count=len(non_pos_rows),
        positive_mismatch_direction_accuracy=_direction_accuracy(pos_rows),
        non_positive_mismatch_direction_accuracy=_direction_accuracy(non_pos_rows),
    )


# ---------------------------------------------------------------------------
# Private: case example builders
# ---------------------------------------------------------------------------


def _make_case_example(row: _WeeklyRow) -> WeeklyCaseExample:
    return WeeklyCaseExample(
        forecast_id=row.forecast_id,
        strategy_kind=row.strategy_kind,
        as_of_jst=row.as_of_jst,
        dominant_state=row.dominant_state,
        forecast_direction=row.forecast_direction,
        realized_direction=row.realized_direction,
        expected_close_change_bp=row.expected_close_change_bp,
        realized_close_change_bp=row.realized_close_change_bp,
        close_error_bp=row.close_error_bp,
        conviction=row.conviction,
        urgency=row.urgency,
        disconfirmer_explained=row.disconfirmer_explained,
    )


def _select_false_positive_cases(
    ugh_rows: list[_WeeklyRow],
    max_examples: int,
) -> tuple[WeeklyCaseExample, ...]:
    """UGH rows where direction_hit == False; sort by desc conviction, desc close_error_bp."""
    fp = [r for r in ugh_rows if not r.direction_hit]
    fp.sort(key=lambda r: (-(r.conviction or 0.0), -(r.close_error_bp or 0.0)))
    return tuple(_make_case_example(r) for r in fp[:max_examples])


def _select_representative_successes(
    ugh_rows: list[_WeeklyRow],
    max_examples: int,
) -> tuple[WeeklyCaseExample, ...]:
    """UGH rows where direction_hit == True; sort by desc conviction, asc close_error_bp."""
    hits = [r for r in ugh_rows if r.direction_hit]
    hits.sort(key=lambda r: (-(r.conviction or 0.0), r.close_error_bp or 0.0))
    return tuple(_make_case_example(r) for r in hits[:max_examples])


def _select_representative_failures(
    ugh_rows: list[_WeeklyRow],
    max_examples: int,
) -> tuple[WeeklyCaseExample, ...]:
    """UGH rows where direction_hit == False; sort by desc abs close_error_bp, desc conviction."""
    fails = [r for r in ugh_rows if not r.direction_hit]
    fails.sort(key=lambda r: (-(r.close_error_bp or 0.0), -(r.conviction or 0.0)))
    return tuple(_make_case_example(r) for r in fails[:max_examples])


# ---------------------------------------------------------------------------
# Public: main entry point
# ---------------------------------------------------------------------------


def run_weekly_report(session: "Session", request: WeeklyReportRequest) -> WeeklyReportResult:
    """Generate a read-only weekly FX report from persisted evaluation data.

    Steps:
    1. Resolve the ``business_day_count`` most recent completed window-end timestamps.
    2. Query evaluation, forecast, and outcome records for those windows.
    3. Count included vs missing windows.
    4. Raise ``ValueError`` if zero windows have data.
    5. Build and return ``WeeklyReportResult``.

    This function never writes, flushes, or commits any data.
    """
    # 1. Resolve window ends (JST-aware).
    window_ends_jst = resolve_completed_window_ends(
        request.report_generated_at_jst,
        request.business_day_count,
    )

    # 2. Convert to naive UTC for DB queries (DateTime(timezone=False) columns).
    naive_utc_windows = tuple(_jst_to_naive_utc(dt) for dt in window_ends_jst)

    # 3. Load all rows for this pair + window set.
    all_rows = _load_weekly_rows(session, request.pair.value, naive_utc_windows)

    # 4. Determine which windows have data.
    naive_jst_with_data = {_to_jst_naive(r.window_end_jst) for r in all_rows}
    included_window_count = sum(
        1 for w in window_ends_jst if _to_jst_naive(w) in naive_jst_with_data
    )
    missing_window_count = request.business_day_count - included_window_count

    if included_window_count == 0:
        raise ValueError(
            f"No evaluation data found for any of the {request.business_day_count} requested "
            f"windows for pair {request.pair.value}. Cannot generate weekly report."
        )

    # 5. Build metrics.
    ugh_rows = [r for r in all_rows if r.strategy_kind == StrategyKind.ugh]

    strategy_metrics = tuple(
        _build_strategy_metrics(all_rows, kind) for kind in _ALL_STRATEGY_KINDS
    )
    ugh_metrics = next(m for m in strategy_metrics if m.strategy_kind == StrategyKind.ugh)

    baseline_comparisons = _build_baseline_comparisons(all_rows, ugh_metrics)
    state_metrics = _build_state_metrics(ugh_rows)
    grv_fire_summary = _build_grv_fire_summary(ugh_rows)
    mismatch_summary = _build_mismatch_summary(ugh_rows)

    # Disconfirmer explained rate: UGH only, rows where value is not None.
    disconf_rows = [r for r in ugh_rows if r.disconfirmer_explained is not None]
    ugh_disconfirmer_explained_rate: float | None = (
        sum(1 for r in disconf_rows if r.disconfirmer_explained) / len(disconf_rows)
        if disconf_rows
        else None
    )

    false_positive_cases = _select_false_positive_cases(ugh_rows, request.max_examples)
    representative_successes = _select_representative_successes(ugh_rows, request.max_examples)
    representative_failures = _select_representative_failures(ugh_rows, request.max_examples)

    return WeeklyReportResult(
        pair=request.pair,
        report_generated_at_jst=request.report_generated_at_jst,
        window_end_jst_values=window_ends_jst,
        requested_window_count=request.business_day_count,
        included_window_count=included_window_count,
        missing_window_count=missing_window_count,
        strategy_metrics=strategy_metrics,
        baseline_comparisons=baseline_comparisons,
        state_metrics=state_metrics,
        grv_fire_summary=grv_fire_summary,
        mismatch_summary=mismatch_summary,
        ugh_disconfirmer_explained_rate=ugh_disconfirmer_explained_rate,
        false_positive_cases=false_positive_cases,
        representative_successes=representative_successes,
        representative_failures=representative_failures,
    )
