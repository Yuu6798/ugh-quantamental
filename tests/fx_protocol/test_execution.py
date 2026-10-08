"""Tests for the FX execution layer v1: records, book decision rules, and evaluation."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from ugh_quantamental.fx_protocol import execution as execution_module
from ugh_quantamental.fx_protocol import execution_models as execution_models_module
from ugh_quantamental.fx_protocol.execution import (
    CONSENSUS_PARTIAL_SIZE,
    EXECUTION_INITIAL_EQUITY_JPY,
    EXECUTION_ROUND_TRIP_COST_JPY_PER_USD,
    EXECUTION_VERSION,
    MIN_COMPLETED_CLOSES,
    UGH_X1_SHOCK_MULTIPLIER,
    UGH_X1_TARGET_BP,
    build_execution_decisions,
    evaluate_execution_decisions,
)
from ugh_quantamental.fx_protocol.execution_models import (
    EXECUTION_BOOK_ORDER,
    BookId,
    ExecutionDecision,
    ExecutionEvaluation,
    LiveEntry,
)
from ugh_quantamental.fx_protocol.forecast_models import BaselineContext
from ugh_quantamental.fx_protocol.ids import make_forecast_batch_id
from ugh_quantamental.fx_protocol.models import CurrencyPair, ForecastDirection, StrategyKind

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc

UP = ForecastDirection.up
DOWN = ForecastDirection.down
FLAT = ForecastDirection.flat

ALPHA = StrategyKind.ugh_v2_alpha
BETA = StrategyKind.ugh_v2_beta
GAMMA = StrategyKind.ugh_v2_gamma
DELTA = StrategyKind.ugh_v2_delta
RANDOM_WALK = StrategyKind.baseline_random_walk
PREV_DAY = StrategyKind.baseline_prev_day_direction
TECHNICAL = StrategyKind.baseline_simple_technical
_REQUIRED_KINDS = (ALPHA, BETA, GAMMA, DELTA, TECHNICAL)

# Friday 2026-03-13 08:00 JST -> Monday 2026-03-16 08:00 JST (canonical business-day window).
_AS_OF = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
_WINDOW_END = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
_DECIDED_AT = datetime(2026, 3, 13, 11, 0, 0, tzinfo=_UTC)  # 20:00 JST publication time
_RETRIEVED_AT = datetime(2026, 3, 13, 11, 0, 5, tzinfo=_UTC)
_EVALUATED_AT = datetime(2026, 3, 16, 0, 0, 0, tzinfo=_UTC)
_BATCH_ID = make_forecast_batch_id(CurrencyPair.USDJPY, _AS_OF, "v1")

_DEFAULT_DIRECTIONS: dict[StrategyKind, ForecastDirection] = {
    ALPHA: UP,
    BETA: UP,
    GAMMA: UP,
    DELTA: UP,
    RANDOM_WALK: FLAT,
    PREV_DAY: UP,
    TECHNICAL: UP,
}

# Realized OHLC presets for the 2026-03-13 window (open / close only matter here).
_UP_OPEN, _UP_CLOSE = 150.10, 150.30
_DOWN_OPEN, _DOWN_CLOSE = 150.10, 149.70

# Pinned evaluation numbers for entry 150.00 live, open 150.10, close 150.30 / 149.70.
_PNL_LIVE_20BP = 20.0  # (150.30 - 150.00) / 150.00 * 1e4, and the short mirror
_PNL_BAR_UP = 13.3244503664  # (150.30 - 150.10) / 150.10 * 1e4
_PNL_BAR_DOWN = 26.6489007328  # (150.10 - 149.70) / 150.10 * 1e4
_COST_LIVE = 0.6666666667  # 0.01 / 150.00 * 1e4
_COST_BAR = 0.6662225183  # 0.01 / 150.10 * 1e4


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _directions(
    overrides: dict[StrategyKind, ForecastDirection] | None = None,
) -> dict[StrategyKind, ForecastDirection]:
    """Full 7-kind direction mapping; ``overrides`` replaces the default (all UGH up, technical up)."""
    return {**_DEFAULT_DIRECTIONS, **(overrides or {})}


def _ugh(
    alpha: ForecastDirection,
    beta: ForecastDirection,
    gamma: ForecastDirection,
    delta: ForecastDirection,
) -> dict[StrategyKind, ForecastDirection]:
    return {ALPHA: alpha, BETA: beta, GAMMA: gamma, DELTA: delta}


def _context(
    *,
    previous_close_change_bp: float | None = 12.0,
    trailing_mean_abs_close_change_bp: float = 20.0,
) -> BaselineContext:
    return BaselineContext(
        current_spot=150.0,
        previous_close_change_bp=previous_close_change_bp,
        trailing_mean_range_price=1.2,
        trailing_mean_abs_close_change_bp=trailing_mean_abs_close_change_bp,
        sma5=150.2,
        sma20=149.8,
        warmup_window_count=20,
    )


def _closes(momentum_3d: float = 0.5) -> tuple[float, ...]:
    """Five closes (oldest -> newest) with ``closes[-2] - closes[-5] == momentum_3d``.

    ``closes[-1]`` deliberately moves the other way so an off-by-one on the
    newest close would flip the sign.
    """
    base = 150.0
    return (base, base - 0.4, base + 0.1, base + momentum_3d, base - 1.0)


def _live(price: float = 150.0) -> LiveEntry:
    return LiveEntry(
        price=price,
        retrieved_at_utc=_RETRIEVED_AT,
        vendor="yahoo_finance",
        feed="chart/USDJPY=X",
    )


_LIVE = _live()


def _decide(
    directions: dict[StrategyKind, ForecastDirection] | None = None,
    *,
    context: BaselineContext | None = None,
    closes: tuple[float, ...] | None = None,
    entry_status: str = "live",
    live_entry: LiveEntry | None = _LIVE,
    as_of_jst: datetime = _AS_OF,
    window_end_jst: datetime = _WINDOW_END,
    forecast_batch_id: str = _BATCH_ID,
    decided_at_utc: datetime = _DECIDED_AT,
) -> tuple[ExecutionDecision, ...]:
    return build_execution_decisions(
        forecast_directions=_directions() if directions is None else directions,
        baseline_context=context or _context(),
        completed_closes=_closes() if closes is None else closes,
        as_of_jst=as_of_jst,
        window_end_jst=window_end_jst,
        forecast_batch_id=forecast_batch_id,
        entry_status=entry_status,  # type: ignore[arg-type]
        live_entry=live_entry,
        decided_at_utc=decided_at_utc,
    )


def _evaluate(
    decisions: tuple[ExecutionDecision, ...],
    *,
    outcome_id: str = "oc_test_001",
    window_start_jst: datetime = _AS_OF,
    realized_open: float = _UP_OPEN,
    realized_close: float = _UP_CLOSE,
    evaluated_at_utc: datetime = _EVALUATED_AT,
) -> tuple[ExecutionEvaluation, ...]:
    return evaluate_execution_decisions(
        decisions,
        outcome_id=outcome_id,
        window_start_jst=window_start_jst,
        realized_open=realized_open,
        realized_close=realized_close,
        evaluated_at_utc=evaluated_at_utc,
    )


def _by_book(decisions: tuple[ExecutionDecision, ...]) -> dict[BookId, ExecutionDecision]:
    return {d.book_id: d for d in decisions}


def _eval_by_book(
    evaluations: tuple[ExecutionEvaluation, ...],
) -> dict[BookId, ExecutionEvaluation]:
    return {e.book_id: e for e in evaluations}


def _decision(**overrides: object) -> ExecutionDecision:
    base: dict[str, object] = dict(
        execution_version="x1",
        book_id=BookId.ugh_x1,
        as_of_jst=_AS_OF,
        window_end_jst=_WINDOW_END,
        forecast_batch_id=_BATCH_ID,
        source_strategy_kind=BETA,
        side=1,
        size=1.0,
        skip_reason=None,
        entry_status="live",
        entry_price_live=150.0,
        entry_time_utc=_RETRIEVED_AT,
        entry_vendor="yahoo_finance",
        entry_feed="chart/USDJPY=X",
        beta_direction=UP,
        consensus_up_count=4,
        consensus_down_count=0,
        technical_direction=UP,
        momentum_3d=0.5,
        trailing_mean_abs_close_change_bp=20.0,
        previous_close_change_bp=12.0,
    )
    base.update(overrides)
    return ExecutionDecision(**base)


def _evaluation(**overrides: object) -> ExecutionEvaluation:
    base: dict[str, object] = dict(
        execution_version="x1",
        book_id=BookId.ugh_x1,
        as_of_jst=_AS_OF,
        window_end_jst=_WINDOW_END,
        forecast_batch_id=_BATCH_ID,
        outcome_id="oc_test_001",
        side=1,
        size=1.0,
        entry_status="live",
        entry_price_live=150.0,
        realized_open=_UP_OPEN,
        realized_close=_UP_CLOSE,
        pnl_live_bp=_PNL_LIVE_20BP,
        pnl_bar_bp=_PNL_BAR_UP,
        cost_live_bp=_COST_LIVE,
        cost_bar_bp=_COST_BAR,
        hit=True,
        evaluated_at_utc=_EVALUATED_AT,
    )
    base.update(overrides)
    return ExecutionEvaluation(**base)


# ---------------------------------------------------------------------------
# Module contracts
# ---------------------------------------------------------------------------


def test_book_id_values_and_canonical_order() -> None:
    assert [b.value for b in BookId] == [
        "ugh_x1",
        "ugh_beta_unit",
        "ugh_consensus",
        "ugh_divergence",
        "bench_gpt_m3",
        "bench_long",
    ]
    assert EXECUTION_BOOK_ORDER == tuple(BookId)
    assert len(EXECUTION_BOOK_ORDER) == 6


def test_execution_constants_are_pinned_and_exported() -> None:
    assert EXECUTION_VERSION == "x1"
    assert EXECUTION_INITIAL_EQUITY_JPY == 3_000_000
    assert EXECUTION_ROUND_TRIP_COST_JPY_PER_USD == 0.01
    assert UGH_X1_TARGET_BP == 30.0
    assert UGH_X1_SHOCK_MULTIPLIER == 2.5
    assert CONSENSUS_PARTIAL_SIZE == 0.5
    assert MIN_COMPLETED_CLOSES == 5
    assert set(execution_module.__all__) >= {
        "EXECUTION_VERSION",
        "EXECUTION_INITIAL_EQUITY_JPY",
        "EXECUTION_ROUND_TRIP_COST_JPY_PER_USD",
        "UGH_X1_TARGET_BP",
        "UGH_X1_SHOCK_MULTIPLIER",
        "CONSENSUS_PARTIAL_SIZE",
        "build_execution_decisions",
        "evaluate_execution_decisions",
    }


def test_execution_modules_are_sqlalchemy_free() -> None:
    for module in (execution_module, execution_models_module):
        for value in vars(module).values():
            origin = getattr(value, "__module__", None) or getattr(value, "__name__", "")
            assert not str(origin).startswith("sqlalchemy"), value


def test_decision_field_order_matches_spec() -> None:
    assert list(ExecutionDecision.model_fields) == [
        "execution_version",
        "book_id",
        "as_of_jst",
        "window_end_jst",
        "forecast_batch_id",
        "source_strategy_kind",
        "side",
        "size",
        "skip_reason",
        "entry_status",
        "entry_price_live",
        "entry_time_utc",
        "entry_vendor",
        "entry_feed",
        "beta_direction",
        "consensus_up_count",
        "consensus_down_count",
        "technical_direction",
        "momentum_3d",
        "trailing_mean_abs_close_change_bp",
        "previous_close_change_bp",
    ]


def test_evaluation_field_order_matches_spec() -> None:
    assert list(ExecutionEvaluation.model_fields) == [
        "execution_version",
        "book_id",
        "as_of_jst",
        "window_end_jst",
        "forecast_batch_id",
        "outcome_id",
        "side",
        "size",
        "entry_status",
        "entry_price_live",
        "realized_open",
        "realized_close",
        "pnl_live_bp",
        "pnl_bar_bp",
        "cost_live_bp",
        "cost_bar_bp",
        "hit",
        "evaluated_at_utc",
    ]


# ---------------------------------------------------------------------------
# LiveEntry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("price", [0.0, -1.0, math.nan, math.inf])
def test_live_entry_rejects_non_positive_or_non_finite_price(price: float) -> None:
    with pytest.raises(ValidationError):
        _live(price)


@pytest.mark.parametrize("field", ["vendor", "feed"])
def test_live_entry_rejects_blank_vendor_or_feed(field: str) -> None:
    with pytest.raises(ValidationError):
        LiveEntry(**{**_LIVE.model_dump(), field: ""})


def test_live_entry_normalizes_retrieved_at_to_aware_utc() -> None:
    naive = LiveEntry(
        price=150.0, retrieved_at_utc=datetime(2026, 3, 13, 11, 0, 5), vendor="v", feed="f"
    )
    jst = LiveEntry(
        price=150.0,
        retrieved_at_utc=datetime(2026, 3, 13, 20, 0, 5, tzinfo=_JST),
        vendor="v",
        feed="f",
    )
    assert naive.retrieved_at_utc == _RETRIEVED_AT
    assert naive.retrieved_at_utc.tzinfo == _UTC
    assert jst.retrieved_at_utc == _RETRIEVED_AT
    assert jst.retrieved_at_utc.tzinfo == _UTC


# ---------------------------------------------------------------------------
# ExecutionDecision validators
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("side", "size"),
    [
        pytest.param(0, 0.5, id="side-0-nonzero-size"),
        pytest.param(1, 0.0, id="side-1-zero-size"),
        pytest.param(-1, 0.0, id="side-minus-1-zero-size"),
        pytest.param(2, 1.0, id="side-above-range"),
        pytest.param(-2, 1.0, id="side-below-range"),
        pytest.param(1, 1.5, id="size-above-1"),
        pytest.param(-1, -0.1, id="size-negative"),
        pytest.param(1, math.nan, id="size-nan"),
        pytest.param(1, math.inf, id="size-inf"),
    ],
)
def test_decision_rejects_side_size_mismatch(side: int, size: float) -> None:
    with pytest.raises(ValidationError):
        _decision(side=side, size=size, skip_reason="flat" if side == 0 else None)


@pytest.mark.parametrize(
    ("side", "size"),
    [(1, 1.0), (-1, 1.0), (1, 0.5), (-1, 1e-6), (0, 0.0)],
)
def test_decision_accepts_coupled_side_size(side: int, size: float) -> None:
    row = _decision(side=side, size=size, skip_reason="flat" if side == 0 else None)
    assert (row.side, row.size) == (side, size)


def test_decision_skip_reason_coupling() -> None:
    with pytest.raises(ValidationError):
        _decision(side=0, size=0.0, skip_reason=None)
    with pytest.raises(ValidationError):
        _decision(side=1, size=1.0, skip_reason="flat")
    with pytest.raises(ValidationError):
        _decision(side=0, size=0.0, skip_reason="not_a_reason")
    assert _decision(side=0, size=0.0, skip_reason="shock_filter").skip_reason == "shock_filter"
    assert _decision(side=1, size=1.0, skip_reason=None).skip_reason is None


@pytest.mark.parametrize(
    ("entry_status", "entry_price_live", "valid"),
    [
        pytest.param("live", 150.0, True, id="live-with-price"),
        pytest.param("live", None, False, id="live-without-price"),
        pytest.param("live_unavailable", None, True, id="unavailable-without-price"),
        pytest.param("live_unavailable", 150.0, False, id="unavailable-with-price"),
        pytest.param("backfill_bar", None, True, id="backfill-without-price"),
        pytest.param("backfill_bar", 150.0, False, id="backfill-with-price"),
        pytest.param("unknown", None, False, id="unknown-status"),
    ],
)
def test_decision_entry_price_live_coupling(
    entry_status: str, entry_price_live: float | None, valid: bool
) -> None:
    if valid:
        row = _decision(entry_status=entry_status, entry_price_live=entry_price_live)
        assert (row.entry_status, row.entry_price_live) == (entry_status, entry_price_live)
    else:
        with pytest.raises(ValidationError):
            _decision(entry_status=entry_status, entry_price_live=entry_price_live)


@pytest.mark.parametrize(
    "field",
    [
        "momentum_3d",
        "trailing_mean_abs_close_change_bp",
        "previous_close_change_bp",
        "entry_price_live",
    ],
)
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_decision_rejects_non_finite_floats(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        _decision(**{field: value})


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"trailing_mean_abs_close_change_bp": -1.0}, id="negative-trailing"),
        pytest.param({"entry_price_live": 0.0}, id="zero-entry-price"),
        pytest.param({"consensus_up_count": -1}, id="negative-up-count"),
        pytest.param({"window_end_jst": _AS_OF}, id="window-end-not-after-as-of"),
        pytest.param({"execution_version": ""}, id="blank-version"),
        pytest.param({"forecast_batch_id": ""}, id="blank-batch-id"),
        pytest.param({"book_id": "ugh_x9"}, id="unknown-book"),
        pytest.param({"unexpected": 1}, id="extra-field"),
    ],
)
def test_decision_rejects_invalid_values(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _decision(**overrides)


def test_decision_is_frozen() -> None:
    row = _decision()
    with pytest.raises(ValidationError):
        row.side = 0  # type: ignore[misc]


def test_decision_normalizes_timestamps() -> None:
    row = _decision(
        as_of_jst=datetime(2026, 3, 13, 8, 0, 0),  # naive == JST
        window_end_jst=datetime(2026, 3, 15, 23, 0, 0, tzinfo=_UTC),  # == 03-16 08:00 JST
        entry_time_utc=datetime(2026, 3, 13, 11, 0, 5),  # naive == UTC
    )
    assert row.as_of_jst == _AS_OF
    assert row.as_of_jst.tzinfo is not None
    assert row.window_end_jst == _WINDOW_END
    assert row.entry_time_utc == _RETRIEVED_AT
    assert row.entry_time_utc.tzinfo == _UTC


# ---------------------------------------------------------------------------
# ExecutionEvaluation validators
# ---------------------------------------------------------------------------

_NO_LIVE = dict(
    entry_status="live_unavailable", entry_price_live=None, pnl_live_bp=None, cost_live_bp=None
)
_SIDE_ZERO = dict(
    side=0, size=0.0, pnl_live_bp=0.0, pnl_bar_bp=0.0, cost_live_bp=0.0, cost_bar_bp=0.0, hit=None
)


def test_evaluation_pnl_live_coupling() -> None:
    with pytest.raises(ValidationError):
        _evaluation(**{**_NO_LIVE, "pnl_live_bp": 20.0})
    with pytest.raises(ValidationError):
        _evaluation(entry_status="live", entry_price_live=150.0, pnl_live_bp=None)
    assert _evaluation(**_NO_LIVE).pnl_live_bp is None
    backfill = _evaluation(**{**_NO_LIVE, "entry_status": "backfill_bar"})
    assert backfill.entry_status == "backfill_bar"


def test_evaluation_cost_live_coupling() -> None:
    with pytest.raises(ValidationError):
        _evaluation(**{**_NO_LIVE, "cost_live_bp": 0.5})
    with pytest.raises(ValidationError):
        _evaluation(entry_status="live", entry_price_live=150.0, cost_live_bp=None)
    assert _evaluation(**_NO_LIVE).cost_live_bp is None


def test_evaluation_hit_coupling() -> None:
    with pytest.raises(ValidationError):
        _evaluation(side=1, size=1.0, hit=None)
    with pytest.raises(ValidationError):
        _evaluation(**{**_SIDE_ZERO, "hit": True})
    assert _evaluation(**_SIDE_ZERO).hit is None
    miss = _evaluation(side=-1, size=1.0, pnl_live_bp=-20.0, pnl_bar_bp=-13.3, hit=False)
    assert miss.hit is False


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"pnl_bar_bp": 1.0}, id="nonzero-bar-pnl"),
        pytest.param({"pnl_live_bp": 1.0}, id="nonzero-live-pnl"),
        pytest.param({"cost_live_bp": 0.5}, id="nonzero-live-cost"),
        pytest.param({"cost_bar_bp": 0.5}, id="nonzero-bar-cost"),
        pytest.param({"size": 0.5}, id="nonzero-size"),
    ],
)
def test_evaluation_side_zero_requires_zero_pnl_cost_and_size(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _evaluation(**{**_SIDE_ZERO, **overrides})


def test_evaluation_side_zero_without_live_price_keeps_live_columns_none() -> None:
    row = _evaluation(**{**_SIDE_ZERO, **_NO_LIVE})
    assert (row.pnl_live_bp, row.cost_live_bp) == (None, None)
    assert (row.pnl_bar_bp, row.cost_bar_bp, row.hit) == (0.0, 0.0, None)


@pytest.mark.parametrize(
    "field",
    [
        "entry_price_live",
        "realized_open",
        "realized_close",
        "pnl_live_bp",
        "pnl_bar_bp",
        "cost_live_bp",
        "cost_bar_bp",
    ],
)
@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_evaluation_rejects_non_finite_floats(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        _evaluation(**{field: value})


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"cost_live_bp": -0.1}, id="negative-live-cost"),
        pytest.param({"cost_bar_bp": -0.1}, id="negative-bar-cost"),
        pytest.param({"realized_open": 0.0}, id="zero-open"),
        pytest.param({"realized_close": -1.0}, id="negative-close"),
        pytest.param({"side": 2}, id="side-out-of-range"),
        pytest.param({"size": 1.5}, id="size-above-1"),
        pytest.param({"side": 1, "size": 0.0}, id="side-1-zero-size"),
        pytest.param(
            {
                "entry_status": "live",
                "entry_price_live": None,
                "pnl_live_bp": None,
                "cost_live_bp": None,
            },
            id="live-without-price",
        ),
        pytest.param({"entry_status": "live_unavailable"}, id="unavailable-with-price"),
        pytest.param({"outcome_id": ""}, id="blank-outcome-id"),
        pytest.param({"window_end_jst": _AS_OF}, id="window-end-not-after-as-of"),
        pytest.param({"unexpected": 1}, id="extra-field"),
    ],
)
def test_evaluation_rejects_invalid_values(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _evaluation(**overrides)


def test_evaluation_is_frozen() -> None:
    row = _evaluation()
    with pytest.raises(ValidationError):
        row.hit = False  # type: ignore[misc]


def test_evaluation_normalizes_timestamps() -> None:
    row = _evaluation(
        as_of_jst=datetime(2026, 3, 12, 23, 0, 0, tzinfo=_UTC),  # == 03-13 08:00 JST
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),  # naive == JST
        evaluated_at_utc=datetime(2026, 3, 16, 9, 0, 0, tzinfo=_JST),  # == 00:00 UTC
    )
    assert row.as_of_jst == _AS_OF
    assert row.window_end_jst == _WINDOW_END
    assert row.evaluated_at_utc == _EVALUATED_AT
    assert row.evaluated_at_utc.tzinfo == _UTC


# ---------------------------------------------------------------------------
# build_execution_decisions — shape and shared columns
# ---------------------------------------------------------------------------


def test_build_returns_six_rows_in_book_order() -> None:
    decisions = _decide()
    assert len(decisions) == 6
    assert tuple(d.book_id for d in decisions) == EXECUTION_BOOK_ORDER
    assert [d.source_strategy_kind for d in decisions] == [BETA, BETA, None, BETA, None, None]
    for d in decisions:
        assert d.execution_version == EXECUTION_VERSION
        assert d.forecast_batch_id == _BATCH_ID
        assert d.as_of_jst == _AS_OF
        assert d.window_end_jst == _WINDOW_END


def test_build_is_deterministic() -> None:
    assert _decide() == _decide()


def test_audit_values_identical_on_all_rows() -> None:
    directions = _directions({**_ugh(UP, DOWN, FLAT, DOWN), TECHNICAL: UP})
    decisions = _decide(
        directions,
        context=_context(previous_close_change_bp=-7.5, trailing_mean_abs_close_change_bp=33.0),
        closes=_closes(-0.25),
    )
    for d in decisions:
        assert d.beta_direction == DOWN
        assert (d.consensus_up_count, d.consensus_down_count) == (1, 2)
        assert d.technical_direction == UP
        assert d.momentum_3d == pytest.approx(-0.25, abs=1e-12)
        assert d.trailing_mean_abs_close_change_bp == 33.0
        assert d.previous_close_change_bp == -7.5


def test_audit_previous_close_change_none_propagates() -> None:
    decisions = _decide(context=_context(previous_close_change_bp=None))
    assert all(d.previous_close_change_bp is None for d in decisions)


def test_momentum_3d_uses_second_newest_and_fifth_newest_close() -> None:
    # Leading distractor: an implementation reading closes[0] or closes[-1] gets a different value.
    closes = (140.0, *_closes(0.5))
    decisions = _decide(closes=closes)
    assert closes[-2] - closes[-5] == 0.5
    assert closes[-1] - closes[-5] < 0
    assert closes[-2] - closes[0] == 10.5
    assert all(d.momentum_3d == 0.5 for d in decisions)
    assert _by_book(decisions)[BookId.bench_gpt_m3].side == 1


def test_required_directions_only_and_extra_keys_are_accepted() -> None:
    required_only = {kind: _DEFAULT_DIRECTIONS[kind] for kind in _REQUIRED_KINDS}
    with_extras = {**_directions(), StrategyKind.ugh: DOWN}
    assert len(_decide(required_only)) == 6
    assert _decide(required_only) == _decide(with_extras)


# ---------------------------------------------------------------------------
# build_execution_decisions — book rules (spec §4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("beta", "previous_bp", "trailing_bp", "side", "size", "skip"),
    [
        pytest.param(UP, 12.0, 20.0, 1, 1.0, None, id="up-calm"),
        pytest.param(DOWN, -12.0, 20.0, -1, 1.0, None, id="down-calm"),
        pytest.param(FLAT, 12.0, 20.0, 0, 0.0, "flat", id="flat"),
        pytest.param(UP, 51.0, 20.0, 0, 0.0, "shock_filter", id="shock-positive"),
        pytest.param(DOWN, -51.0, 20.0, 0, 0.0, "shock_filter", id="shock-negative-uses-abs"),
        pytest.param(UP, 50.0, 20.0, 1, 1.0, None, id="shock-boundary-is-not-strict"),
        pytest.param(FLAT, 80.0, 20.0, 0, 0.0, "flat", id="flat-evaluated-before-shock"),
        pytest.param(UP, None, 20.0, 1, 1.0, None, id="previous-none-disables-shock"),
        pytest.param(UP, None, 60.0, 1, 0.5, None, id="previous-none-still-sizes"),
        pytest.param(UP, 12.0, 60.0, 1, 0.5, None, id="size-trailing-60"),
        pytest.param(UP, 12.0, 30.0, 1, 1.0, None, id="size-trailing-30-caps-at-1"),
        pytest.param(UP, 12.0, 45.0, 1, 30.0 / 45.0, None, id="size-trailing-45"),
        pytest.param(UP, 0.0, 0.0, 1, 1.0, None, id="size-trailing-0"),
        pytest.param(UP, None, 0.0, 1, 1.0, None, id="size-trailing-0-previous-none"),
        pytest.param(UP, 1.0, 0.0, 0, 0.0, "shock_filter", id="trailing-0-any-move-is-shock"),
    ],
)
def test_ugh_x1_rules(
    beta: ForecastDirection,
    previous_bp: float | None,
    trailing_bp: float,
    side: int,
    size: float,
    skip: str | None,
) -> None:
    decisions = _decide(
        _directions({BETA: beta}),
        context=_context(
            previous_close_change_bp=previous_bp, trailing_mean_abs_close_change_bp=trailing_bp
        ),
    )
    row = _by_book(decisions)[BookId.ugh_x1]
    assert row.side == side
    assert row.size == pytest.approx(size, abs=1e-12)
    assert row.skip_reason == skip
    assert row.source_strategy_kind == BETA


@pytest.mark.parametrize(
    ("beta", "side", "size", "skip"),
    [
        pytest.param(UP, 1, 1.0, None, id="up"),
        pytest.param(DOWN, -1, 1.0, None, id="down"),
        pytest.param(FLAT, 0, 0.0, "flat", id="flat"),
    ],
)
def test_ugh_beta_unit_rules(
    beta: ForecastDirection, side: int, size: float, skip: str | None
) -> None:
    # Shock-day, high-vol context: beta_unit ignores both the shock filter and the vol target.
    decisions = _decide(
        _directions({BETA: beta}),
        context=_context(previous_close_change_bp=200.0, trailing_mean_abs_close_change_bp=60.0),
    )
    rows = _by_book(decisions)
    row = rows[BookId.ugh_beta_unit]
    assert (row.side, row.size, row.skip_reason) == (side, size, skip)
    assert row.source_strategy_kind == BETA
    assert rows[BookId.ugh_x1].skip_reason == ("flat" if beta is FLAT else "shock_filter")


@pytest.mark.parametrize(
    ("variants", "side", "size", "skip", "up_count", "down_count"),
    [
        pytest.param((UP, UP, UP, UP), 1, 1.0, None, 4, 0, id="4-up"),
        pytest.param((DOWN, DOWN, DOWN, DOWN), -1, 1.0, None, 0, 4, id="4-down"),
        pytest.param((UP, UP, UP, FLAT), 1, 0.5, None, 3, 0, id="3-up-1-flat"),
        pytest.param((FLAT, DOWN, DOWN, DOWN), -1, 0.5, None, 0, 3, id="3-down-1-flat"),
        pytest.param((UP, UP, UP, DOWN), 0, 0.0, "no_consensus", 3, 1, id="3-up-1-down"),
        pytest.param((DOWN, UP, DOWN, DOWN), 0, 0.0, "no_consensus", 1, 3, id="3-down-1-up"),
        pytest.param((UP, UP, DOWN, DOWN), 0, 0.0, "no_consensus", 2, 2, id="2-up-2-down"),
        pytest.param((UP, FLAT, UP, FLAT), 0, 0.0, "no_consensus", 2, 0, id="2-up-2-flat"),
        pytest.param((FLAT, FLAT, FLAT, FLAT), 0, 0.0, "no_consensus", 0, 0, id="4-flat"),
        pytest.param((UP, FLAT, FLAT, FLAT), 0, 0.0, "no_consensus", 1, 0, id="1-up-3-flat"),
    ],
)
def test_ugh_consensus_rules(
    variants: tuple[ForecastDirection, ...],
    side: int,
    size: float,
    skip: str | None,
    up_count: int,
    down_count: int,
) -> None:
    decisions = _decide(_directions(_ugh(*variants)))
    row = _by_book(decisions)[BookId.ugh_consensus]
    assert (row.side, row.size, row.skip_reason) == (side, size, skip)
    assert (row.consensus_up_count, row.consensus_down_count) == (up_count, down_count)
    assert row.source_strategy_kind is None


@pytest.mark.parametrize(
    ("beta", "technical", "side", "size", "skip"),
    [
        pytest.param(UP, UP, 0, 0.0, "agree_with_technical", id="agree-up"),
        pytest.param(DOWN, DOWN, 0, 0.0, "agree_with_technical", id="agree-down"),
        pytest.param(UP, DOWN, 1, 1.0, None, id="diverge-up"),
        pytest.param(DOWN, UP, -1, 1.0, None, id="diverge-down"),
        pytest.param(UP, FLAT, 1, 1.0, None, id="technical-flat-is-divergence"),
        pytest.param(FLAT, UP, 0, 0.0, "flat", id="beta-flat"),
        pytest.param(FLAT, FLAT, 0, 0.0, "flat", id="both-flat-is-flat-not-agree"),
    ],
)
def test_ugh_divergence_rules(
    beta: ForecastDirection,
    technical: ForecastDirection,
    side: int,
    size: float,
    skip: str | None,
) -> None:
    decisions = _decide(_directions({BETA: beta, TECHNICAL: technical}))
    row = _by_book(decisions)[BookId.ugh_divergence]
    assert (row.side, row.size, row.skip_reason) == (side, size, skip)
    assert row.source_strategy_kind == BETA
    assert row.technical_direction == technical


@pytest.mark.parametrize(
    ("momentum", "side", "size", "skip"),
    [
        pytest.param(0.5, 1, 1.0, None, id="positive"),
        pytest.param(-0.5, -1, 1.0, None, id="negative"),
        pytest.param(0.0, 0, 0.0, "momentum_zero", id="zero"),
    ],
)
def test_bench_gpt_m3_rules(momentum: float, side: int, size: float, skip: str | None) -> None:
    decisions = _decide(closes=_closes(momentum))
    row = _by_book(decisions)[BookId.bench_gpt_m3]
    assert (row.side, row.size, row.skip_reason) == (side, size, skip)
    assert row.momentum_3d == pytest.approx(momentum, abs=1e-12)
    assert row.source_strategy_kind is None


def test_bench_long_always_long() -> None:
    all_flat = _directions({**_ugh(FLAT, FLAT, FLAT, FLAT), TECHNICAL: FLAT, PREV_DAY: FLAT})
    decisions = _decide(
        all_flat,
        context=_context(previous_close_change_bp=500.0, trailing_mean_abs_close_change_bp=0.0),
        closes=_closes(0.0),
    )
    row = _by_book(decisions)[BookId.bench_long]
    assert (row.side, row.size, row.skip_reason) == (1, 1.0, None)
    assert row.source_strategy_kind is None
    # Every other book sits out on this degenerate day.
    assert [d.skip_reason for d in decisions[:-1]] == [
        "flat",
        "flat",
        "no_consensus",
        "flat",
        "momentum_zero",
    ]


# ---------------------------------------------------------------------------
# build_execution_decisions — entry fields
# ---------------------------------------------------------------------------


def test_live_entry_recorded_on_every_row_including_skips() -> None:
    live = _live(150.25)
    directions = _directions({**_ugh(UP, FLAT, DOWN, UP), TECHNICAL: UP})
    decisions = _decide(directions, closes=_closes(0.0), entry_status="live", live_entry=live)
    assert sum(d.side == 0 for d in decisions) == 5  # everything but bench_long skips
    for d in decisions:
        assert d.entry_status == "live"
        assert d.entry_price_live == 150.25
        assert d.entry_time_utc == _RETRIEVED_AT
        assert d.entry_vendor == "yahoo_finance"
        assert d.entry_feed == "chart/USDJPY=X"


@pytest.mark.parametrize("entry_status", ["live_unavailable", "backfill_bar"])
def test_entry_fields_without_live_entry(entry_status: str) -> None:
    decisions = _decide(entry_status=entry_status, live_entry=None)
    for d in decisions:
        assert d.entry_status == entry_status
        assert d.entry_price_live is None
        assert d.entry_time_utc == _DECIDED_AT
        assert d.entry_vendor is None
        assert d.entry_feed is None
    # Decisions themselves are unaffected by the missing live price.
    assert [(d.side, d.size) for d in decisions] == [(d.side, d.size) for d in _decide()]


# ---------------------------------------------------------------------------
# build_execution_decisions — ValueError guards
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing", _REQUIRED_KINDS, ids=[k.value for k in _REQUIRED_KINDS])
def test_missing_required_direction_raises(missing: StrategyKind) -> None:
    directions = {kind: d for kind, d in _directions().items() if kind != missing}
    with pytest.raises(
        ValueError, match="^execution layer requires a complete daily forecast batch"
    ):
        _decide(directions)


def test_empty_directions_raise() -> None:
    with pytest.raises(
        ValueError, match="^execution layer requires a complete daily forecast batch"
    ):
        _decide({})


def test_baselines_other_than_technical_do_not_satisfy_completeness() -> None:
    directions = {ALPHA: UP, BETA: UP, GAMMA: UP, DELTA: UP, RANDOM_WALK: FLAT, PREV_DAY: UP}
    with pytest.raises(ValueError, match="baseline_simple_technical"):
        _decide(directions)


@pytest.mark.parametrize(
    ("entry_status", "live_entry"),
    [
        pytest.param("live", None, id="live-without-live-entry"),
        pytest.param("live_unavailable", _LIVE, id="unavailable-with-live-entry"),
        pytest.param("backfill_bar", _LIVE, id="backfill-with-live-entry"),
    ],
)
def test_entry_status_live_entry_mismatch_raises(
    entry_status: str, live_entry: LiveEntry | None
) -> None:
    with pytest.raises(ValueError, match="live_entry exactly when entry_status == 'live'"):
        _decide(entry_status=entry_status, live_entry=live_entry)


def test_unknown_entry_status_raises() -> None:
    with pytest.raises(ValueError):
        _decide(entry_status="unknown", live_entry=None)


def test_completed_closes_shorter_than_five_raises() -> None:
    with pytest.raises(ValueError, match="completed closes"):
        _decide(closes=(150.0, 150.1, 150.2, 150.3))
    with pytest.raises(ValueError, match="completed closes"):
        _decide(closes=())
    assert len(_decide(closes=(150.0, 150.1, 150.2, 150.3, 150.4))) == 6


# ---------------------------------------------------------------------------
# evaluate_execution_decisions — numbers pinned (spec §5.2)
# ---------------------------------------------------------------------------


def test_evaluation_live_long_hit_numbers() -> None:
    decisions = _decide(live_entry=_live(150.0))
    evaluations = _evaluate(decisions, realized_open=_UP_OPEN, realized_close=_UP_CLOSE)
    assert len(evaluations) == 6
    assert tuple(e.book_id for e in evaluations) == EXECUTION_BOOK_ORDER
    row = _eval_by_book(evaluations)[BookId.ugh_x1]
    assert (row.side, row.size) == (1, 1.0)
    assert (row.entry_status, row.entry_price_live) == ("live", 150.0)
    assert (row.realized_open, row.realized_close) == (150.10, 150.30)
    assert row.pnl_live_bp == pytest.approx(20.0, abs=1e-9)
    assert row.pnl_bar_bp == pytest.approx(13.3244503664, abs=1e-8)
    assert row.cost_live_bp == pytest.approx(0.6666666667, abs=1e-9)
    assert row.cost_bar_bp == pytest.approx(0.6662225183, abs=1e-9)
    assert row.hit is True
    assert row.outcome_id == "oc_test_001"
    assert row.forecast_batch_id == _BATCH_ID
    assert row.execution_version == "x1"
    assert row.as_of_jst == _AS_OF
    assert row.window_end_jst == _WINDOW_END
    assert row.evaluated_at_utc == _EVALUATED_AT


def test_evaluation_live_short_hit_numbers() -> None:
    decisions = _decide(_directions({BETA: DOWN}), live_entry=_live(150.0))
    evaluations = _evaluate(decisions, realized_open=_DOWN_OPEN, realized_close=_DOWN_CLOSE)
    row = _eval_by_book(evaluations)[BookId.ugh_x1]
    assert row.side == -1
    assert row.pnl_live_bp == pytest.approx(_PNL_LIVE_20BP, abs=1e-9)
    assert row.pnl_bar_bp == pytest.approx(_PNL_BAR_DOWN, abs=1e-8)
    assert row.cost_live_bp == pytest.approx(_COST_LIVE, abs=1e-9)
    assert row.cost_bar_bp == pytest.approx(_COST_BAR, abs=1e-9)
    assert row.hit is True


def test_evaluation_live_long_miss_numbers() -> None:
    decisions = _decide(live_entry=_live(150.0))
    evaluations = _evaluate(decisions, realized_open=_DOWN_OPEN, realized_close=_DOWN_CLOSE)
    row = _eval_by_book(evaluations)[BookId.bench_long]
    assert row.side == 1
    assert row.pnl_live_bp == pytest.approx(-_PNL_LIVE_20BP, abs=1e-9)
    assert row.pnl_bar_bp == pytest.approx(-_PNL_BAR_DOWN, abs=1e-8)
    assert row.cost_live_bp == pytest.approx(_COST_LIVE, abs=1e-9)
    assert row.cost_bar_bp == pytest.approx(_COST_BAR, abs=1e-9)
    assert row.hit is False


def test_evaluation_flat_close_is_not_a_hit() -> None:
    decisions = _decide(live_entry=_live(150.0))
    rows = _eval_by_book(_evaluate(decisions, realized_open=150.10, realized_close=150.10))
    row = rows[BookId.bench_long]
    assert row.hit is False
    assert row.pnl_bar_bp == 0.0
    assert row.pnl_live_bp == pytest.approx((150.10 - 150.0) / 150.0 * 1e4, abs=1e-9)
    assert row.cost_bar_bp == pytest.approx(_COST_BAR, abs=1e-9)


def test_evaluation_side_zero_rows() -> None:
    decisions_live = _decide(live_entry=_live(150.0))
    decisions_no_live = _decide(entry_status="live_unavailable", live_entry=None)
    assert _by_book(decisions_live)[BookId.ugh_divergence].skip_reason == "agree_with_technical"
    skipped_live = _eval_by_book(_evaluate(decisions_live))[BookId.ugh_divergence]
    skipped_no_live = _eval_by_book(_evaluate(decisions_no_live))[BookId.ugh_divergence]
    assert (skipped_live.side, skipped_live.size) == (0, 0.0)
    assert skipped_live.entry_price_live == 150.0
    assert skipped_live.pnl_live_bp == 0.0
    assert skipped_live.pnl_bar_bp == 0.0
    assert skipped_live.cost_live_bp == 0.0
    assert skipped_live.cost_bar_bp == 0.0
    assert skipped_live.hit is None
    assert skipped_no_live.entry_price_live is None
    assert skipped_no_live.pnl_live_bp is None
    assert skipped_no_live.pnl_bar_bp == 0.0
    assert skipped_no_live.cost_live_bp is None
    assert skipped_no_live.cost_bar_bp == 0.0
    assert skipped_no_live.hit is None


@pytest.mark.parametrize("entry_status", ["live_unavailable", "backfill_bar"])
def test_evaluation_without_live_price_uses_bar_columns_only(entry_status: str) -> None:
    decisions = _decide(entry_status=entry_status, live_entry=None)
    row = _eval_by_book(_evaluate(decisions))[BookId.ugh_x1]
    assert row.entry_status == entry_status
    assert row.entry_price_live is None
    assert row.pnl_live_bp is None
    assert row.cost_live_bp is None
    assert row.pnl_bar_bp == pytest.approx(_PNL_BAR_UP, abs=1e-8)
    assert row.cost_bar_bp == pytest.approx(_COST_BAR, abs=1e-9)  # 0.01 / 150.10 * 1e4
    assert row.hit is True


def test_evaluation_bp_is_independent_of_size() -> None:
    decisions = _decide(context=_context(trailing_mean_abs_close_change_bp=60.0))
    rows = _eval_by_book(_evaluate(decisions))
    half, full = rows[BookId.ugh_x1], rows[BookId.ugh_beta_unit]
    assert (half.size, full.size) == (0.5, 1.0)
    assert half.pnl_live_bp == full.pnl_live_bp
    assert half.pnl_bar_bp == full.pnl_bar_bp
    assert half.cost_live_bp == full.cost_live_bp
    assert half.cost_bar_bp == full.cost_bar_bp


def test_evaluation_copies_version_from_decision() -> None:
    decisions = tuple(d.model_copy(update={"execution_version": "x0"}) for d in _decide())
    assert all(e.execution_version == "x0" for e in _evaluate(decisions))


def test_evaluation_is_deterministic() -> None:
    decisions = _decide()
    assert _evaluate(decisions) == _evaluate(decisions)


def test_evaluation_matches_window_across_timezone_representations() -> None:
    naive_decisions = _decide(as_of_jst=datetime(2026, 3, 13, 8, 0, 0))  # naive == JST
    utc_window_start = datetime(2026, 3, 12, 23, 0, 0, tzinfo=_UTC)  # == 03-13 08:00 JST
    evaluations = _evaluate(naive_decisions, window_start_jst=utc_window_start)
    assert len(evaluations) == 6
    assert all(e.as_of_jst == _AS_OF for e in evaluations)
    naive_window_start = datetime(2026, 3, 13, 8, 0, 0)
    assert len(_evaluate(_decide(), window_start_jst=naive_window_start)) == 6


# ---------------------------------------------------------------------------
# evaluate_execution_decisions — ValueError guards
# ---------------------------------------------------------------------------


def test_evaluation_rejects_empty_decisions() -> None:
    with pytest.raises(ValueError, match="at least one decision"):
        _evaluate(())


def test_evaluation_rejects_mixed_batch_ids() -> None:
    decisions = _decide()
    foreign = decisions[1].model_copy(update={"forecast_batch_id": "fb_other"})
    with pytest.raises(ValueError, match="single forecast_batch_id"):
        _evaluate((decisions[0], foreign))


def test_evaluation_rejects_window_mismatch() -> None:
    with pytest.raises(ValueError, match="outcome window does not match"):
        _evaluate(_decide(), window_start_jst=_WINDOW_END)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("realized_open", 0.0, id="open-zero"),
        pytest.param("realized_open", -1.0, id="open-negative"),
        pytest.param("realized_open", math.nan, id="open-nan"),
        pytest.param("realized_open", math.inf, id="open-inf"),
        pytest.param("realized_close", 0.0, id="close-zero"),
        pytest.param("realized_close", math.nan, id="close-nan"),
        pytest.param("realized_close", -math.inf, id="close-neg-inf"),
    ],
)
def test_evaluation_rejects_invalid_realized_prices(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=f"finite positive {field}"):
        _evaluate(_decide(), **{field: value})
