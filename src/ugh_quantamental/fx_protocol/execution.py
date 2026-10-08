"""Pure decision and evaluation rules for the FX execution layer v1 (spec §4, §5).

No I/O and no clock access: live spot retrieval, outcome loading and CSV
persistence belong to the automation / exports modules. Every function here
is deterministic in its inputs, so a day's six :class:`ExecutionDecision` rows
can be re-derived from the persisted forecast directions and snapshot
statistics alone.

The parameters below are frozen under ``EXECUTION_VERSION = "x1"``. Changing
any of them (or a book rule) is a spec revision and an ``execution_version``
bump (spec §9), never an in-place edit.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from ugh_quantamental.fx_protocol.execution_models import (
    EXECUTION_BOOK_ORDER,
    BookId,
    EntryStatus,
    ExecutionDecision,
    ExecutionEvaluation,
    LiveEntry,
    SkipReason,
)
from ugh_quantamental.fx_protocol.forecast_models import BaselineContext
from ugh_quantamental.fx_protocol.models import (
    _UGH_V2_STRATEGY_KINDS,
    ForecastDirection,
    StrategyKind,
    _to_jst,
)

__all__ = [
    "CONSENSUS_PARTIAL_SIZE",
    "EXECUTION_INITIAL_EQUITY_JPY",
    "EXECUTION_ROUND_TRIP_COST_JPY_PER_USD",
    "EXECUTION_VERSION",
    "MIN_COMPLETED_CLOSES",
    "UGH_X1_SHOCK_MULTIPLIER",
    "UGH_X1_TARGET_BP",
    "build_execution_decisions",
    "evaluate_execution_decisions",
]

# ---------------------------------------------------------------------------
# Frozen parameters (spec §4; bump EXECUTION_VERSION to change)
# ---------------------------------------------------------------------------

#: Version tag written on every decision / evaluation row.
EXECUTION_VERSION: str = "x1"
#: Starting equity of every book's equity curve (reporting layer, spec §5.2 / §8).
EXECUTION_INITIAL_EQUITY_JPY: int = 3_000_000
#: Round-trip transaction cost in JPY per USD of notional (≈ 0.67bp at 150).
EXECUTION_ROUND_TRIP_COST_JPY_PER_USD: float = 0.01
#: ``ugh_x1`` daily volatility target in bp; size = target / trailing mean |Δclose|.
UGH_X1_TARGET_BP: float = 30.0
#: ``ugh_x1`` shock filter: skip when |previous Δclose| exceeds this multiple of trailing.
UGH_X1_SHOCK_MULTIPLIER: float = 2.5
#: ``ugh_consensus`` size when three variants agree and the fourth is flat.
CONSENSUS_PARTIAL_SIZE: float = 0.5
#: ``momentum_3d`` reads ``completed_closes[-5]``, so at least five closes are required.
MIN_COMPLETED_CLOSES: int = 5

_BATCH_ERROR_PREFIX: str = "execution layer requires a complete daily forecast batch"
_REQUIRED_STRATEGY_KINDS: tuple[StrategyKind, ...] = (
    *_UGH_V2_STRATEGY_KINDS,
    StrategyKind.baseline_simple_technical,
)
_UGH_VARIANT_COUNT: int = len(_UGH_V2_STRATEGY_KINDS)
_BP_SCALE: float = 10_000.0
_DIRECTION_SIDE: dict[ForecastDirection, int] = {
    ForecastDirection.up: 1,
    ForecastDirection.down: -1,
    ForecastDirection.flat: 0,
}


# ---------------------------------------------------------------------------
# Internal value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Call:
    """A book's position call before entry metadata is attached."""

    side: int
    size: float
    skip_reason: SkipReason | None


@dataclass(frozen=True, slots=True)
class _Entry:
    """Entry metadata shared by every row of a batch (spec §5.1 entry columns)."""

    status: EntryStatus
    price_live: float | None
    time_utc: datetime
    vendor: str | None
    feed: str | None


def _trade(side: int, size: float) -> _Call:
    return _Call(side=side, size=size, skip_reason=None)


def _skip(reason: SkipReason) -> _Call:
    return _Call(side=0, size=0.0, skip_reason=reason)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def _resolve_directions(
    forecast_directions: Mapping[StrategyKind, ForecastDirection],
) -> dict[StrategyKind, ForecastDirection]:
    """Return the required strategy directions, else raise ``ValueError``.

    Every ``ugh_v2_*`` variant and ``baseline_simple_technical`` must be
    present; other keys (the remaining baselines, legacy ``ugh``) are ignored.
    """
    missing = [kind.value for kind in _REQUIRED_STRATEGY_KINDS if kind not in forecast_directions]
    if missing:
        raise ValueError(f"{_BATCH_ERROR_PREFIX}: missing forecast directions for {missing}")
    return {kind: ForecastDirection(forecast_directions[kind]) for kind in _REQUIRED_STRATEGY_KINDS}


def _entry_fields(
    entry_status: EntryStatus,
    live_entry: LiveEntry | None,
    decided_at_utc: datetime,
) -> _Entry:
    """Resolve the entry columns, else raise ``ValueError`` on a status / live_entry mismatch."""
    if (entry_status == "live") != (live_entry is not None):
        raise ValueError(
            "execution layer requires a live_entry exactly when entry_status == 'live' "
            f"(got entry_status={entry_status!r}, "
            f"live_entry={'present' if live_entry is not None else 'None'})"
        )
    if live_entry is None:
        return _Entry(
            status=entry_status,
            price_live=None,
            time_utc=decided_at_utc,
            vendor=None,
            feed=None,
        )
    return _Entry(
        status=entry_status,
        price_live=live_entry.price,
        time_utc=live_entry.retrieved_at_utc,
        vendor=live_entry.vendor,
        feed=live_entry.feed,
    )


# ---------------------------------------------------------------------------
# Book rules (spec §4)
# ---------------------------------------------------------------------------


def _decide_ugh_x1(
    beta_direction: ForecastDirection,
    previous_close_change_bp: float | None,
    trailing_mean_abs_close_change_bp: float,
) -> _Call:
    """Main book: β direction, vol-targeted size, shock filter; conviction is never consulted.

    ``flat`` is checked before the shock filter, so a flat β on a shock day
    records ``flat``. A missing ``previous_close_change_bp`` disables the filter.
    """
    side = _DIRECTION_SIDE[beta_direction]
    if side == 0:
        return _skip("flat")
    trailing = trailing_mean_abs_close_change_bp
    previous = previous_close_change_bp
    if previous is not None and abs(previous) > UGH_X1_SHOCK_MULTIPLIER * trailing:
        return _skip("shock_filter")
    size = 1.0 if trailing == 0 else min(1.0, UGH_X1_TARGET_BP / trailing)
    return _trade(side, size)


def _decide_ugh_beta_unit(beta_direction: ForecastDirection) -> _Call:
    """β direction at unit size; the raw directional signal without any sizing rule."""
    side = _DIRECTION_SIDE[beta_direction]
    if side == 0:
        return _skip("flat")
    return _trade(side, 1.0)


def _decide_ugh_consensus(up_count: int, down_count: int) -> _Call:
    """Full agreement of the four UGH variants trades 1.0; three plus one flat trades 0.5."""
    if up_count == _UGH_VARIANT_COUNT:
        return _trade(1, 1.0)
    if down_count == _UGH_VARIANT_COUNT:
        return _trade(-1, 1.0)
    if up_count == _UGH_VARIANT_COUNT - 1 and down_count == 0:
        return _trade(1, CONSENSUS_PARTIAL_SIZE)
    if down_count == _UGH_VARIANT_COUNT - 1 and up_count == 0:
        return _trade(-1, CONSENSUS_PARTIAL_SIZE)
    return _skip("no_consensus")


def _decide_ugh_divergence(
    beta_direction: ForecastDirection,
    technical_direction: ForecastDirection,
) -> _Call:
    """β direction only on days it disagrees with ``baseline_simple_technical``."""
    side = _DIRECTION_SIDE[beta_direction]
    if side == 0:
        return _skip("flat")
    if beta_direction == technical_direction:
        return _skip("agree_with_technical")
    return _trade(side, 1.0)


def _decide_bench_gpt_m3(momentum_3d: float) -> _Call:
    """Benchmark: sign of the 3-day close momentum lagged two windows."""
    if momentum_3d > 0:
        return _trade(1, 1.0)
    if momentum_3d < 0:
        return _trade(-1, 1.0)
    return _skip("momentum_zero")


def _decide_bench_long() -> _Call:
    """Benchmark: always long at unit size."""
    return _trade(1, 1.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_execution_decisions(
    *,
    forecast_directions: Mapping[StrategyKind, ForecastDirection],
    baseline_context: BaselineContext,
    completed_closes: Sequence[float],
    as_of_jst: datetime,
    window_end_jst: datetime,
    forecast_batch_id: str,
    entry_status: EntryStatus,
    live_entry: LiveEntry | None,
    decided_at_utc: datetime,
) -> tuple[ExecutionDecision, ...]:
    """Build the six book decisions for one forecast window (spec §4 / §5.1).

    Parameters
    ----------
    forecast_directions:
        ``strategy_kind -> forecast_direction`` of the day's batch. Must hold
        every ``ugh_v2_*`` variant and ``baseline_simple_technical``; other
        keys are ignored.
    baseline_context:
        Snapshot statistics at decision time; supplies
        ``previous_close_change_bp`` and ``trailing_mean_abs_close_change_bp``.
    completed_closes:
        Close prices of the completed windows ordered oldest → newest (at
        least ``MIN_COMPLETED_CLOSES``). ``momentum_3d`` is
        ``completed_closes[-2] - completed_closes[-5]``.
    as_of_jst, window_end_jst, forecast_batch_id:
        The consumed batch's window and id, copied onto every row.
    entry_status:
        Written as given. ``"live"`` requires ``live_entry``; any other status
        requires ``live_entry is None``.
    live_entry:
        Live spot observed at decision time (price / time / vendor / feed go
        onto every row, skipped books included), or ``None``.
    decided_at_utc:
        Decision timestamp; becomes ``entry_time_utc`` when no live spot exists.

    Returns
    -------
    tuple[ExecutionDecision, ...]
        Exactly one row per book, in ``EXECUTION_BOOK_ORDER``.

    Raises
    ------
    ValueError
        If a required strategy direction is missing, ``completed_closes`` is
        shorter than ``MIN_COMPLETED_CLOSES``, or ``entry_status`` and
        ``live_entry`` disagree.
    """
    directions = _resolve_directions(forecast_directions)
    if len(completed_closes) < MIN_COMPLETED_CLOSES:
        raise ValueError(
            f"execution layer requires at least {MIN_COMPLETED_CLOSES} completed closes "
            f"(oldest -> newest); got {len(completed_closes)}"
        )
    if not all(math.isfinite(close) for close in completed_closes):
        raise ValueError("execution layer requires finite completed closes")
    entry = _entry_fields(entry_status, live_entry, decided_at_utc)

    beta_direction = directions[StrategyKind.ugh_v2_beta]
    technical_direction = directions[StrategyKind.baseline_simple_technical]
    variant_directions = [directions[kind] for kind in _UGH_V2_STRATEGY_KINDS]
    consensus_up_count = sum(d == ForecastDirection.up for d in variant_directions)
    consensus_down_count = sum(d == ForecastDirection.down for d in variant_directions)
    momentum_3d = completed_closes[-2] - completed_closes[-5]
    trailing = baseline_context.trailing_mean_abs_close_change_bp
    previous = baseline_context.previous_close_change_bp

    calls: dict[BookId, tuple[StrategyKind | None, _Call]] = {
        BookId.ugh_x1: (
            StrategyKind.ugh_v2_beta,
            _decide_ugh_x1(beta_direction, previous, trailing),
        ),
        BookId.ugh_beta_unit: (StrategyKind.ugh_v2_beta, _decide_ugh_beta_unit(beta_direction)),
        BookId.ugh_consensus: (
            None,
            _decide_ugh_consensus(consensus_up_count, consensus_down_count),
        ),
        BookId.ugh_divergence: (
            StrategyKind.ugh_v2_beta,
            _decide_ugh_divergence(beta_direction, technical_direction),
        ),
        BookId.bench_gpt_m3: (None, _decide_bench_gpt_m3(momentum_3d)),
        BookId.bench_long: (None, _decide_bench_long()),
    }

    decisions: list[ExecutionDecision] = []
    for book_id in EXECUTION_BOOK_ORDER:
        source_strategy_kind, call = calls[book_id]
        decisions.append(
            ExecutionDecision(
                execution_version=EXECUTION_VERSION,
                book_id=book_id,
                as_of_jst=as_of_jst,
                window_end_jst=window_end_jst,
                forecast_batch_id=forecast_batch_id,
                source_strategy_kind=source_strategy_kind,
                side=call.side,
                size=call.size,
                skip_reason=call.skip_reason,
                entry_status=entry.status,
                entry_price_live=entry.price_live,
                entry_time_utc=entry.time_utc,
                entry_vendor=entry.vendor,
                entry_feed=entry.feed,
                beta_direction=beta_direction,
                consensus_up_count=consensus_up_count,
                consensus_down_count=consensus_down_count,
                technical_direction=technical_direction,
                momentum_3d=momentum_3d,
                trailing_mean_abs_close_change_bp=trailing,
                previous_close_change_bp=previous,
            )
        )
    return tuple(decisions)


def _evaluate_one(
    decision: ExecutionDecision,
    *,
    outcome_id: str,
    realized_open: float,
    realized_close: float,
    evaluated_at_utc: datetime,
) -> ExecutionEvaluation:
    entry_price_live = decision.entry_price_live
    side = decision.side
    cost = EXECUTION_ROUND_TRIP_COST_JPY_PER_USD

    if side == 0:
        pnl_bar_bp = 0.0
        cost_bar_bp = 0.0
        pnl_live_bp: float | None = 0.0 if entry_price_live is not None else None
        cost_live_bp: float | None = 0.0 if entry_price_live is not None else None
        hit: bool | None = None
    else:
        pnl_bar_bp = side * (realized_close - realized_open) / realized_open * _BP_SCALE
        cost_bar_bp = abs(side) * cost / realized_open * _BP_SCALE
        if entry_price_live is not None:
            pnl_live_bp = side * (realized_close - entry_price_live) / entry_price_live * _BP_SCALE
            cost_live_bp = abs(side) * cost / entry_price_live * _BP_SCALE
        else:
            pnl_live_bp = None
            cost_live_bp = None
        hit = side * (realized_close - realized_open) > 0

    return ExecutionEvaluation(
        execution_version=decision.execution_version,
        book_id=decision.book_id,
        as_of_jst=decision.as_of_jst,
        window_end_jst=decision.window_end_jst,
        forecast_batch_id=decision.forecast_batch_id,
        outcome_id=outcome_id,
        side=side,
        size=decision.size,
        skip_reason=decision.skip_reason,
        entry_status=decision.entry_status,
        entry_price_live=entry_price_live,
        realized_open=realized_open,
        realized_close=realized_close,
        pnl_live_bp=pnl_live_bp,
        pnl_bar_bp=pnl_bar_bp,
        cost_live_bp=cost_live_bp,
        cost_bar_bp=cost_bar_bp,
        hit=hit,
        evaluated_at_utc=evaluated_at_utc,
    )


def evaluate_execution_decisions(
    decisions: Sequence[ExecutionDecision],
    *,
    outcome_id: str,
    window_start_jst: datetime,
    realized_open: float,
    realized_close: float,
    evaluated_at_utc: datetime,
) -> tuple[ExecutionEvaluation, ...]:
    """Evaluate a window's decisions against its realized outcome (spec §5.2).

    ``outcome_id`` / ``window_start_jst`` / ``realized_open`` / ``realized_close``
    are the window's ``OutcomeRecord`` values; exit is always ``realized_close``.
    For each decision (in input order)::

        pnl_bar_bp   = side × (realized_close − realized_open) / realized_open × 1e4
        pnl_live_bp  = side × (realized_close − entry_price_live) / entry_price_live × 1e4
        cost_bar_bp  = |side| × EXECUTION_ROUND_TRIP_COST_JPY_PER_USD / realized_open × 1e4
        cost_live_bp = |side| × EXECUTION_ROUND_TRIP_COST_JPY_PER_USD / entry_price_live × 1e4
        hit          = side × (realized_close − realized_open) > 0

    ``*_live`` values are ``None`` when the decision carries no live entry
    price. Skipped rows (``side == 0``) evaluate to zero P&L and cost (the
    ``*_live`` values are ``0.0`` with a live price, else ``None``) with
    ``hit`` None.

    Raises
    ------
    ValueError
        If ``decisions`` is empty, mixes ``forecast_batch_id`` values,
        ``window_start_jst`` differs from any decision's ``as_of_jst``, a book
        appears more than once, or a realized price is not finite and positive.
    """
    if not decisions:
        raise ValueError("execution layer evaluation requires at least one decision")
    batch_ids = {decision.forecast_batch_id for decision in decisions}
    if len(batch_ids) != 1:
        raise ValueError(
            "execution layer evaluation requires decisions from a single forecast_batch_id; "
            f"got {sorted(batch_ids)}"
        )
    for name, value in (("realized_open", realized_open), ("realized_close", realized_close)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(
                f"execution layer evaluation requires a finite positive {name}; got {value!r}"
            )
    window_start = _to_jst(window_start_jst)
    for decision in decisions:
        if window_start != decision.as_of_jst:
            raise ValueError(
                "outcome window does not match the decisions' forecast window "
                f"(window_start_jst={window_start.isoformat()}, "
                f"decisions.as_of_jst={decision.as_of_jst.isoformat()})"
            )
    book_ids = [decision.book_id for decision in decisions]
    if len(set(book_ids)) != len(book_ids):
        raise ValueError("execution layer evaluation requires at most one decision per book")
    return tuple(
        _evaluate_one(
            decision,
            outcome_id=outcome_id,
            realized_open=realized_open,
            realized_close=realized_close,
            evaluated_at_utc=evaluated_at_utc,
        )
        for decision in decisions
    )
