"""Tests for execution_reporting.py — collector, spec §8 metrics, spec §9 gate, artifacts.

No network, no clock (``generated_at_utc`` is always explicit), no randomness.
Every archive is synthesised under ``tmp_path`` through the real models and
exporters (``ExecutionDecision`` → ``evaluate_execution_decisions`` →
``export_execution_*_csv`` → ``publish_execution_csvs``), so the files the
collector reads are byte-for-byte what automation writes.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol import execution_reporting as reporting
from ugh_quantamental.fx_protocol.calendar import is_protocol_business_day, next_as_of_jst
from ugh_quantamental.fx_protocol.csv_exports import FORECAST_FIELDNAMES, write_csv_rows
from ugh_quantamental.fx_protocol.execution import (
    EXECUTION_ACTIVATION_AS_OF,
    EXECUTION_EXCLUDED_AS_OF,
    evaluate_execution_decisions,
)
from ugh_quantamental.fx_protocol.execution_exports import (
    EXECUTION_EVALUATION_FIELDNAMES,
    EXECUTION_FIELDNAMES,
    export_execution_csv,
    export_execution_evaluation_csv,
    publish_execution_csvs,
)
from ugh_quantamental.fx_protocol.execution_models import (
    EXECUTION_BOOK_ORDER,
    BookId,
    ExecutionDecision,
)
from ugh_quantamental.fx_protocol.execution_reporting import (
    EXECUTION_REPORT_BOOK_FIELDNAMES,
    GATE_BLOCKED_REASONS,
    GATE_MIN_CALENDAR_DAYS,
    CollectedExecutionEvaluations,
    IncompleteExecutionBatch,
    MissingExecutionDecision,
    MissingExecutionEvaluation,
    collect_execution_evaluation_rows,
    expected_decision_days,
    export_execution_latest_summary,
    export_execution_report_artifacts,
    is_gate_blocking_defect,
    run_execution_report,
)
from ugh_quantamental.fx_protocol.models import ForecastDirection, StrategyKind

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_PAIR = "USDJPY"
_ENTRY = 100.0  # live entry price on every fixture day (cost_live_bp = 0.01 / 100 × 1e4 = 1.0 bp)

#: This checkout's ``src`` (tests/fx_protocol/<file> → repo root → src), for the subprocess test.
_SRC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"
)
#: Bytes no UTF-8 decoder accepts: planted in a sibling file to simulate a corrupt archive.
_CORRUPT_BYTES = b"\xff\xfe\x00\x80not,utf8\n"

Leg = tuple[int, float, str | None]


def _trade(side: int, size: float = 1.0) -> Leg:
    return (side, size, None)


def _skip(reason: str = "flat") -> Leg:
    return (0, 0.0, reason)


_ALL_SKIP: dict[BookId, Leg] = {book: _skip() for book in EXECUTION_BOOK_ORDER}
_SOURCE_KIND: dict[BookId, StrategyKind | None] = {
    BookId.ugh_x1: StrategyKind.ugh_v2_beta,
    BookId.ugh_beta_unit: StrategyKind.ugh_v2_beta,
    BookId.ugh_consensus: None,
    BookId.ugh_divergence: StrategyKind.ugh_v2_beta,
    BookId.bench_gpt_m3: None,
    BookId.bench_long: None,
}


# ---------------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------------


def _as_of(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, 8, tzinfo=_JST)


def _window_end(day: date) -> datetime:
    return next_as_of_jst(_as_of(day))


def _after_close(day: date) -> datetime:
    """A UTC instant one hour after *day*'s window closed (its evaluation is due)."""
    return (_window_end(day) + timedelta(hours=1)).astimezone(_UTC)


def _before_close(day: date) -> datetime:
    """A UTC instant one hour before *day*'s window closes (the window is pending)."""
    return (_window_end(day) - timedelta(hours=1)).astimezone(_UTC)


def _batch_id(day: date, suffix: str = "") -> str:
    return f"fb_USDJPY_{day:%Y%m%d}T080000_v1{suffix}"


def _business_days(first: date, last: date) -> list[date]:
    days: list[date] = []
    day = first
    while day <= last:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


# ---------------------------------------------------------------------------
# Archive writers (real models + real exporters, into tmp_path)
# ---------------------------------------------------------------------------


def _decision(
    day: date,
    book: BookId,
    leg: Leg,
    *,
    entry_status: str,
    entry_price: float,
    version: str,
    batch_id: str,
) -> ExecutionDecision:
    side, size, skip_reason = leg
    live = entry_status == "live"
    return ExecutionDecision(
        execution_version=version,
        book_id=book,
        as_of_jst=_as_of(day),
        window_end_jst=_window_end(day),
        forecast_batch_id=batch_id,
        source_strategy_kind=_SOURCE_KIND[book],
        side=side,
        size=size,
        skip_reason=skip_reason,
        entry_status=entry_status,
        entry_price_live=entry_price if live else None,
        entry_time_utc=_as_of(day).astimezone(_UTC) + timedelta(hours=10),
        entry_vendor="yahoo_finance" if live else None,
        entry_feed="chart/USDJPY=X" if live else None,
        beta_direction=ForecastDirection.up,
        consensus_up_count=4,
        consensus_down_count=0,
        technical_direction=ForecastDirection.up,
        momentum_3d=0.5,
        trailing_mean_abs_close_change_bp=40.0,
        previous_close_change_bp=10.0,
    )


def _write_day(
    root: str,
    day: date,
    legs: dict[BookId, Leg] | None = None,
    *,
    realized_open: float = _ENTRY,
    realized_close: float = _ENTRY,
    entry_status: str | dict[BookId, str] = "live",
    entry_price: float = _ENTRY,
    version: str = "x1",
    batch_id: str | None = None,
    decisions: bool = True,
    evaluations: bool = True,
    evaluation_books: tuple[BookId, ...] = EXECUTION_BOOK_ORDER,
    live_bp: dict[BookId, tuple[float, float]] | None = None,
    date_dir: date | None = None,
) -> str:
    """Publish one batch (six decisions, their evaluations) into ``history/`` and return its dir.

    Books absent from *legs* skip (``flat``).  *live_bp* overrides
    ``(pnl_live_bp, cost_live_bp)`` per book after the real evaluation so a test
    can pin exact signed returns.  *evaluation_books* restricts the evaluation
    rows (an incomplete batch); *decisions* / *evaluations* False omit a file.
    """
    legs = {**_ALL_SKIP, **(legs or {})}
    batch_id = batch_id or _batch_id(day)
    statuses = (
        entry_status
        if isinstance(entry_status, dict)
        else {book: entry_status for book in EXECUTION_BOOK_ORDER}
    )
    decision_rows = tuple(
        _decision(
            day,
            book,
            legs[book],
            entry_status=statuses.get(book, "live"),
            entry_price=entry_price,
            version=version,
            batch_id=batch_id,
        )
        for book in EXECUTION_BOOK_ORDER
    )
    evaluation_rows = evaluate_execution_decisions(
        [d for d in decision_rows if d.book_id in evaluation_books],
        outcome_id=f"oc_{day:%Y%m%d}",
        window_start_jst=_as_of(day),
        realized_open=realized_open,
        realized_close=realized_close,
        evaluated_at_utc=_window_end(day).astimezone(_UTC),
    )
    if live_bp:
        evaluation_rows = tuple(
            ev.model_copy(
                update={
                    "pnl_live_bp": live_bp[ev.book_id][0],
                    "cost_live_bp": live_bp[ev.book_id][1],
                }
            )
            if ev.book_id in live_bp
            else ev
            for ev in evaluation_rows
        )
    staging = os.path.join(root, "staging", batch_id)
    decision_path = (
        export_execution_csv(decision_rows, _as_of(day), _PAIR, staging) if decisions else None
    )
    evaluation_path = (
        export_execution_evaluation_csv(evaluation_rows, _as_of(day), _PAIR, staging)
        if evaluations
        else None
    )
    date_str = (date_dir or day).strftime("%Y%m%d")
    publish_execution_csvs(root, date_str, batch_id, decision_path, evaluation_path)
    return os.path.join(root, "history", date_str, batch_id)


def _write_header_only_decisions(root: str, day: date) -> str:
    batch_dir = os.path.join(root, "history", day.strftime("%Y%m%d"), _batch_id(day))
    os.makedirs(batch_dir, exist_ok=True)
    with open(os.path.join(batch_dir, "execution.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(EXECUTION_FIELDNAMES) + "\n")
    return batch_dir


def _write_decision_rows(root: str, day: date, count: int) -> str:
    """Publish an ``execution.csv`` holding only the first *count* of the six decision rows."""
    batch_id = _batch_id(day)
    decisions = tuple(
        _decision(
            day,
            book,
            _trade(1),
            entry_status="live",
            entry_price=_ENTRY,
            version="x1",
            batch_id=batch_id,
        )
        for book in EXECUTION_BOOK_ORDER[:count]
    )
    staging = os.path.join(root, "staging", batch_id)
    decision_path = export_execution_csv(decisions, _as_of(day), _PAIR, staging)
    date_str = day.strftime("%Y%m%d")
    publish_execution_csvs(root, date_str, batch_id, decision_path, None)
    return os.path.join(root, "history", date_str, batch_id)


def _write_corrupt_bytes(path: str) -> None:
    """Plant a file that is not valid UTF-8 (directories created)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(_CORRUPT_BYTES)


def _write_header_only_evaluations(batch_dir: str) -> None:
    """A header-only ``execution_evaluation.csv`` in the real column layout (no data rows)."""
    path = os.path.join(batch_dir, "execution_evaluation.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(EXECUTION_EVALUATION_FIELDNAMES) + "\n")


def _write_forecast_only(root: str, day: date) -> str:
    """A day whose forecast was published but whose decisions never were."""
    batch_id = _batch_id(day)
    path = os.path.join(root, "history", day.strftime("%Y%m%d"), batch_id, "forecast.csv")
    rows = [
        {
            "forecast_id": f"fc_{day:%Y%m%d}_{kind.value}",
            "forecast_batch_id": batch_id,
            "pair": _PAIR,
            "strategy_kind": kind.value,
            "as_of_jst": _as_of(day).isoformat(),
            "window_end_jst": _window_end(day).isoformat(),
            "forecast_direction": "up",
        }
        for kind in (StrategyKind.ugh_v2_beta, StrategyKind.baseline_simple_technical)
    ]
    write_csv_rows(path, rows, FORECAST_FIELDNAMES)
    return batch_id


def _activate(monkeypatch: pytest.MonkeyPatch, day: date, excluded: tuple[date, ...] = ()) -> None:
    monkeypatch.setattr(reporting, "EXECUTION_ACTIVATION_AS_OF", day)
    monkeypatch.setattr(reporting, "EXECUTION_EXCLUDED_AS_OF", frozenset(excluded))


def _collect(root: str, generated_at: datetime) -> CollectedExecutionEvaluations:
    return collect_execution_evaluation_rows(
        os.path.join(root, "history"), generated_at_utc=generated_at
    )


def _report(
    root: str,
    generated_at: datetime,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    return run_execution_report(
        root, start_as_of_jst=start, end_as_of_jst=end, generated_at_utc=generated_at
    )


def _x1(report: dict, version: str = "x1") -> dict:
    return report["strata"][version]["books"]["ugh_x1"]


# ---------------------------------------------------------------------------
# Aggregation fixture: 6 windows × 6 books, one live-missing row, one skip row,
# two backfill rows.  Live entry is 100.0 everywhere; (open, close) per day:
#
#   D1 2026-03-02  (100.0, 101.0)   up 100 bp
#   D2 2026-03-03  ( 99.5, 100.5)   live +50 bp; bar +100.5025 bp (open differs from live entry)
#   D3 2026-03-04  (100.0,  99.0)   down 100 bp;  ugh_x1 row is live_unavailable (live-missing row)
#   D4 2026-03-05  (100.0, 100.0)   flat;         ugh_x1 skips with skip_reason=shock_filter
#   D5 2026-03-06  (100.0, 102.0)   up 200 bp;    ugh_x1 row is backfill_bar
#   D6 2026-03-09  (100.0,  99.0)   down 100 bp;  ugh_x1 row is backfill_bar
#
# ugh_x1 legs: D1 +1 ×0.5, D2 +1 ×1.0, D3 −1 ×1.0, D4 skip, D5 +1 ×1.0, D6 +1 ×0.5 (a miss).
# bench_long is +1 ×1.0 live every day; bench_gpt_m3 skips (momentum_zero) every day;
# ugh_beta_unit trades +1 live every day; ugh_consensus / ugh_divergence skip every day.
# ---------------------------------------------------------------------------

_AGG_DAYS = (
    date(2026, 3, 2),
    date(2026, 3, 3),
    date(2026, 3, 4),
    date(2026, 3, 5),
    date(2026, 3, 6),
    date(2026, 3, 9),
)
_AGG_PRICES = (
    (100.0, 101.0),
    (99.5, 100.5),
    (100.0, 99.0),
    (100.0, 100.0),
    (100.0, 102.0),
    (100.0, 99.0),
)
_AGG_X1: tuple[tuple[Leg, str], ...] = (
    (_trade(1, 0.5), "live"),
    (_trade(1), "live"),
    (_trade(-1), "live_unavailable"),
    (_skip("shock_filter"), "live"),
    (_trade(1), "backfill_bar"),
    (_trade(1, 0.5), "backfill_bar"),
)


def _write_aggregation_fixture(root: str) -> datetime:
    """Write the six windows above and return a ``generated_at_utc`` after the last close."""
    for day, (open_, close), (x1_leg, x1_status) in zip(_AGG_DAYS, _AGG_PRICES, _AGG_X1):
        _write_day(
            root,
            day,
            {
                BookId.ugh_x1: x1_leg,
                BookId.ugh_beta_unit: _trade(1),
                BookId.ugh_consensus: _skip("no_consensus"),
                BookId.ugh_divergence: _skip("agree_with_technical"),
                BookId.bench_gpt_m3: _skip("momentum_zero"),
                BookId.bench_long: _trade(1),
            },
            realized_open=open_,
            realized_close=close,
            entry_status={BookId.ugh_x1: x1_status},
        )
    return _after_close(_AGG_DAYS[-1])


@pytest.fixture
def aggregation_root(tmp_path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, datetime]:
    root = str(tmp_path / "csv")
    _activate(monkeypatch, _AGG_DAYS[0])
    generated_at = _write_aggregation_fixture(root)
    return root, generated_at


# ---------------------------------------------------------------------------
# 集計: fixed numbers
# ---------------------------------------------------------------------------


class TestAggregationNumbers:
    def test_ugh_x1_metrics(self, aggregation_root: tuple[str, datetime]) -> None:
        root, generated_at = aggregation_root
        m = _x1(_report(root, generated_at))

        assert m["decision_count"] == 6
        assert m["trade_count"] == 5  # D1, D2, D3, D5, D6 (D4 is the skip row)
        assert m["live_trade_count"] == 2  # D1, D2 (D3 has no live price; D5/D6 are backfill)
        assert m["skip_counts"] == {"shock_filter": 1}
        assert m["live_coverage_rate"] == pytest.approx(3 / 6)  # live rows: D1, D2, D4
        # hits: D1 up/+1, D2 up/+1, D3 down/−1, D5 up/+1 hit; D6 down/+1 misses → 4 / 5
        assert m["direction_hit_rate"] == pytest.approx(0.8)
        # capture (unit size) = 100 + (1.0 / 99.5 × 1e4 = 100.5025) + 100 + 200 − 100
        assert m["capture_bp"] == pytest.approx(400.5025125628141)

        # live signed bp = size × (pnl_live_bp − cost_live_bp), live trade rows only:
        #   D1 0.5 × (100 − 1) = 49.5 ; D2 1.0 × (50 − 1) = 49.0 → mean 49.25, n = 2 → t None
        assert m["signed_bp_live_mean"] == pytest.approx(49.25)
        assert m["signed_bp_live_sd"] == pytest.approx(0.3535533905932738)
        assert m["signed_bp_live_t"] is None
        # bar signed bp over all trade rows:
        #   D1 0.5 × (100 − 1) = 49.5 ; D2 1.0 × (100.5025 − 1.0050) = 99.4975 ;
        #   D3 1.0 × (100 − 1) = 99.0 ; D5 1.0 × (200 − 1) = 199.0 ; D6 0.5 × (−100 − 1) = −50.5
        #   mean = 396.4975 / 5 = 79.2995 ; stdev = 90.6369 ; t = 79.2995 / (90.6369 / √5) = 1.9564
        assert m["signed_bp_bar_mean"] == pytest.approx(79.2994974874372)
        assert m["signed_bp_bar_sd"] == pytest.approx(90.63691093797368)
        assert m["signed_bp_bar_t"] == pytest.approx(1.956367059826538)

        # live equity (D1, D2, D4 flat), initial 3,000,000:
        #   D1 position = 3,000,000 × 0.5 / 100 = 15,000 USD ; gross 15,000 × 1.0 = 15,000 ;
        #      cost 15,000 × 0.01 = 150 → +14,850 → 3,014,850
        #   D2 position = 3,014,850 / 100 = 30,148.5 ; gross 30,148.5 × 0.5 = 15,074.25 ;
        #      cost 301.485 → +14,772.765 → 3,029,622.765
        assert m["pnl_jpy_live"] == pytest.approx(29622.765)
        assert m["final_equity_jpy_live"] == pytest.approx(3029622.765)
        assert m["cost_jpy_live"] == pytest.approx(451.485)
        assert m["max_drawdown_live"] == 0.0
        assert m["profit_factor_live"] is None  # no losing live trade
        # bar equity (all six rows, entry = realized_open):
        #   D1 +14,850 → 3,014,850 ; D2 position 3,014,850 / 99.5 = 30,300 ; gross 30,300 ;
        #      cost 303 → +29,997 → 3,044,847 ; D3 position 30,448.47 ; gross +30,448.47 ;
        #      cost 304.4847 → +30,143.9853 → 3,074,990.9853 ; D4 flat ;
        #   D5 position 30,749.9099 ; gross 61,499.8197 ; cost 307.4991 → +61,192.3206 →
        #      3,136,183.3059 ; D6 position 15,680.9165 ; gross −15,680.9165 ; cost 156.8092 →
        #      −15,837.7257 → 3,120,345.5802 ; drawdown 15,837.7257 / 3,136,183.3059 = 0.50500%
        assert m["pnl_jpy_bar"] == pytest.approx(120345.58021263685)
        assert m["final_equity_jpy_bar"] == pytest.approx(3120345.580212637)
        assert m["cost_jpy_bar"] == pytest.approx(1221.7929638253736)
        assert m["max_drawdown_bar"] == pytest.approx(0.00505)

    def test_bench_long_metrics(self, aggregation_root: tuple[str, datetime]) -> None:
        root, generated_at = aggregation_root
        m = _report(root, generated_at)["strata"]["x1"]["books"]["bench_long"]

        assert m["decision_count"] == 6
        assert m["trade_count"] == 6
        assert m["skip_counts"] == {}
        assert m["live_coverage_rate"] == 1.0
        assert m["direction_hit_rate"] == pytest.approx(0.5)  # D1, D2, D5 hit; D3, D4, D6 miss
        assert m["capture_bp"] == pytest.approx(200.5025125628141)
        # live signed bp: 99, 49, −101, −1 (flat day still pays cost), 199, −101
        #   mean = 144 / 6 = 24 ; squared deviations 5625+625+15625+625+30625+15625 = 68,750 ;
        #   stdev = √(68,750 / 5) = 117.2604 ; t = 24 / (117.2604 / √6) = 0.5013
        assert m["signed_bp_live_mean"] == pytest.approx(24.0)
        assert m["signed_bp_live_sd"] == pytest.approx(117.26039399558574)
        assert m["signed_bp_live_t"] == pytest.approx(0.5013436491524097)
        # live equity: +29,700 ; +14,845.53 ; −30,749.9099 ; −301.3796 ; +59,968.5354 ;
        #   −31,041.9740 → 3,042,420.8019 ; peak 3,073,462.7760 → drawdown 1.0199%
        assert m["pnl_jpy_live"] == pytest.approx(42420.80193530256)
        assert m["cost_jpy_live"] == pytest.approx(1817.4998166704613)
        assert m["max_drawdown_live"] == pytest.approx(0.01019899)
        # PF = (29,700 + 14,845.53 + 59,968.5354) / (30,749.9099 + 301.3796 + 31,041.9740)
        assert m["profit_factor_live"] == pytest.approx(1.6831788116252657)
        assert m["pnl_jpy_bar"] == pytest.approx(57709.34867869597)
        assert m["signed_bp_bar_t"] == pytest.approx(0.6553536511416502)

    def test_all_skip_book_has_null_statistics(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        m = _report(root, generated_at)["strata"]["x1"]["books"]["ugh_consensus"]

        assert m["decision_count"] == 6
        assert m["trade_count"] == 0
        assert m["skip_counts"] == {"no_consensus": 6}
        assert m["direction_hit_rate"] is None
        assert m["capture_bp"] == 0.0
        assert m["signed_bp_live_mean"] is None
        assert m["signed_bp_live_t"] is None
        assert m["signed_bp_bar_t"] is None
        assert m["pnl_jpy_live"] == 0.0
        assert m["final_equity_jpy_bar"] == 3_000_000.0
        assert m["max_drawdown_live"] == 0.0
        assert m["profit_factor_live"] is None
        assert m["cost_jpy_bar"] == 0.0

    def test_benchmark_deltas(self, aggregation_root: tuple[str, datetime]) -> None:
        root, generated_at = aggregation_root
        deltas = _report(root, generated_at)["strata"]["x1"]["benchmark_deltas"]

        assert set(deltas) == {"bench_gpt_m3", "bench_long"}
        # ugh_x1 live P&L 29,622.765 − bench_long 42,420.8019 ; capture 400.5025 − 200.5025
        assert deltas["bench_long"]["pnl_jpy_live_delta"] == pytest.approx(-12798.03693530243)
        assert deltas["bench_long"]["capture_bp_delta"] == pytest.approx(200.0)
        # bench_gpt_m3 never trades: both deltas equal ugh_x1's own values
        assert deltas["bench_gpt_m3"]["pnl_jpy_live_delta"] == pytest.approx(29622.765)
        assert deltas["bench_gpt_m3"]["capture_bp_delta"] == pytest.approx(400.5025125628141)

    def test_gate_values(self, aggregation_root: tuple[str, datetime]) -> None:
        root, generated_at = aggregation_root
        gate = _report(root, generated_at)["gate"]

        cohort = gate["cohort"]
        assert cohort["execution_version"] == "x1"
        assert cohort["trade_count"] == 2  # ugh_x1 live trades: D1, D2
        assert cohort["observation_days"] == 6  # every window has live rows (other books)
        assert cohort["first_as_of_jst"] == "2026-03-02T08:00:00+09:00"
        assert cohort["last_as_of_jst"] == "2026-03-09T08:00:00+09:00"
        assert cohort["observation_calendar_days"] == 7
        assert cohort["excluded_days"] == 0

        criteria = gate["criteria"]
        assert criteria["trades_and_duration"]["current"] == {
            "trade_count": 2,
            "observation_calendar_days": 7,
        }
        assert criteria["trades_and_duration"]["threshold"] == {
            "trade_count": 100,
            "observation_calendar_days": GATE_MIN_CALENDAR_DAYS,
        }
        assert criteria["trades_and_duration"]["met"] is False
        assert criteria["t_stat_live"]["current"] is None
        assert criteria["t_stat_live"]["met"] is False
        assert criteria["max_drawdown_live"]["current"] == 0.0
        assert criteria["max_drawdown_live"]["met"] is True
        assert criteria["beats_benchmarks"]["current"] == pytest.approx(29622.765)
        assert criteria["beats_benchmarks"]["threshold"]["bench_gpt_m3"] == 0.0
        assert criteria["beats_benchmarks"]["threshold"]["bench_long"] == pytest.approx(
            42420.80193530256
        )
        assert criteria["beats_benchmarks"]["met"] is False
        # ugh_x1 was not a live row on D3 (live_unavailable), D5 and D6 (backfill_bar)
        assert gate["blocked_reasons"] == ("missing_live",)
        assert gate["passed"] is False
        inventory = _report(root, generated_at)["inventory"]
        assert inventory["missing_live"]["items"] == ["2026-03-04", "2026-03-06", "2026-03-09"]

    def test_report_is_json_serialisable_and_pure(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        before = sorted(
            os.path.relpath(os.path.join(d, f), root)
            for d, _, files in os.walk(root)
            for f in files
        )
        report = _report(root, generated_at)
        after = sorted(
            os.path.relpath(os.path.join(d, f), root)
            for d, _, files in os.walk(root)
            for f in files
        )
        assert before == after  # nothing written
        encoded = json.dumps(report, allow_nan=False)  # strict: no NaN, no coerced datetimes
        assert json.loads(encoded)["gate"]["blocked_reasons"] == ["missing_live"]
        assert report["generated_at_utc"] == generated_at.isoformat()
        assert report["window"] == {"start_as_of_jst": None, "end_as_of_jst": None}


class TestWindow:
    def test_window_filters_rows_by_jst_date_inclusive(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        report = _report(root, generated_at, start=_as_of(_AGG_DAYS[1]), end=_as_of(_AGG_DAYS[2]))
        assert report["row_count"] == 12
        assert report["batch_count"] == 2
        assert _x1(report)["decision_count"] == 2
        assert report["window"] == {"start_as_of_jst": "2026-03-03", "end_as_of_jst": "2026-03-04"}

    def test_midnight_bounds_cover_the_whole_day(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        start = datetime(2026, 3, 9, tzinfo=_JST)
        report = _report(root, generated_at, start=start, end=start)
        assert report["batch_count"] == 1
        assert _x1(report)["decision_count"] == 1

    def test_open_bound_and_empty_window(self, aggregation_root: tuple[str, datetime]) -> None:
        root, generated_at = aggregation_root
        assert _report(root, generated_at, end=_as_of(_AGG_DAYS[0]))["batch_count"] == 1
        empty = _report(root, generated_at, start=_as_of(date(2026, 4, 1)))
        assert empty["strata"] == {}
        assert empty["row_count"] == 0
        assert empty["history_row_count"] == 36


class TestCollectorDedup:
    def test_same_batch_in_two_dirs_counted_once(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        src = os.path.join(root, "history", "20260302", _batch_id(_AGG_DAYS[0]))
        dst = os.path.join(root, "history", "20260303", _batch_id(_AGG_DAYS[0]))
        shutil.copytree(src, dst)  # the batch republished under the next day's date dir

        collected = _collect(root, generated_at)
        assert len(collected.rows) == 36
        assert (
            sum(1 for r in collected.rows if r["forecast_batch_id"] == _batch_id(_AGG_DAYS[0])) == 6
        )
        assert collected.duplicate_batches == ()
        assert collected.incomplete_batches == ()
        report = _report(root, generated_at)
        assert _x1(report)["decision_count"] == 6
        assert report["strata"]["x1"]["batch_count"] == 6

    def test_rows_are_raw_cells_sorted_by_window(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        collected = _collect(root, generated_at)
        assert all(isinstance(v, str) for row in collected.rows for v in row.values())
        as_ofs = [row["as_of_jst"] for row in collected.rows]
        assert as_ofs == sorted(as_ofs)
        assert [row["book_id"] for row in collected.rows[:6]] == [
            b.value for b in EXECUTION_BOOK_ORDER
        ]

    def test_missing_history_dir_is_empty_archive(self, tmp_path, monkeypatch) -> None:
        _activate(monkeypatch, date(2026, 3, 2))
        collected = _collect(str(tmp_path / "csv"), _before_close(date(2026, 3, 2)))
        assert collected.rows == ()
        assert collected.blocked_reasons() == ()


# ---------------------------------------------------------------------------
# ゲート: cohort boundaries (criteria 1–4)
# ---------------------------------------------------------------------------

# Gate histories start on Tuesday 2026-01-06: +181 calendar days is Monday 2026-07-06,
# +182 is Tuesday 2026-07-07 (131 business days in between, all with live files).
_GATE_FIRST = date(2026, 1, 6)
_GATE_LAST_181 = date(2026, 7, 6)
_GATE_LAST_182 = date(2026, 7, 7)


def _write_gate_history(
    root: str, first: date, last: date, trade_days: int, *, tie: bool = False
) -> list[date]:
    """Live files for every business day in [first, last]; ``ugh_x1`` trades the first N days.

    Up days (even index, close 101.0): ugh_x1 +1 → 100 − 1 = 99 bp; bench_long +1 → 99;
    bench_gpt_m3 −1 → −101.  Down days (odd index, close 99.5): ugh_x1 −1 → 50 − 1 = 49;
    bench_long +1 → −51; bench_gpt_m3 +1 → −51.  Later days are flat skips.  With *tie*
    bench_long mirrors ugh_x1 exactly and bench_gpt_m3 never trades.
    """
    days = _business_days(first, last)
    for index, day in enumerate(days):
        if index >= trade_days:
            _write_day(root, day)
            continue
        if index % 2 == 0:
            close = 101.0
            legs = {BookId.ugh_x1: _trade(1), BookId.bench_long: _trade(1)}
            if not tie:
                legs[BookId.bench_gpt_m3] = _trade(-1)
        else:
            close = 99.5
            legs = {BookId.ugh_x1: _trade(-1), BookId.bench_long: _trade(-1 if tie else 1)}
            if not tie:
                legs[BookId.bench_gpt_m3] = _trade(1)
        _write_day(root, day, legs, realized_close=close)
    return days


class TestGateBoundaries:
    @pytest.mark.parametrize(("trade_days", "met"), [(99, False), (100, True)])
    def test_trade_count_boundary(self, tmp_path, monkeypatch, trade_days: int, met: bool) -> None:
        root = str(tmp_path / "csv")
        _activate(monkeypatch, _GATE_FIRST)
        _write_gate_history(root, _GATE_FIRST, _GATE_LAST_182, trade_days)
        gate = _report(root, _after_close(_GATE_LAST_182))["gate"]

        assert gate["blocked_reasons"] == ()
        assert gate["cohort"]["trade_count"] == trade_days
        assert gate["cohort"]["observation_calendar_days"] == 182
        assert gate["criteria"]["trades_and_duration"]["met"] is met
        assert gate["criteria"]["t_stat_live"]["met"] is True
        assert gate["criteria"]["max_drawdown_live"]["met"] is True
        assert gate["criteria"]["beats_benchmarks"]["met"] is True
        assert gate["passed"] is met

    @pytest.mark.parametrize(
        ("last", "calendar_days", "met"),
        [(_GATE_LAST_181, 181, False), (_GATE_LAST_182, 182, True)],
    )
    def test_calendar_days_boundary_with_100_trades(
        self, tmp_path, monkeypatch, last: date, calendar_days: int, met: bool
    ) -> None:
        root = str(tmp_path / "csv")
        _activate(monkeypatch, _GATE_FIRST)
        _write_gate_history(root, _GATE_FIRST, last, 100)
        gate = _report(root, _after_close(last))["gate"]

        assert gate["blocked_reasons"] == ()
        assert gate["cohort"]["trade_count"] == 100
        assert gate["cohort"]["observation_calendar_days"] == calendar_days
        assert gate["criteria"]["trades_and_duration"]["met"] is met
        assert gate["passed"] is met

    @pytest.mark.parametrize(
        ("pnl_bps", "t_stat", "met"),
        [
            # signed bp = size × (pnl_live_bp − cost_live_bp) with cost 1.0 → 1, 1, 1, 5:
            #   mean 2 ; deviations −1, −1, −1, 3 → stdev √(12 / 3) = 2 ; t = 2 / (2 / √4) = 2.00
            ((2.0, 2.0, 2.0, 6.0), 2.0, True),
            # 0.99, 0.99, 0.99, 4.99: mean 1.99 ; stdev 2 ; t = 1.99 / (2 / 2) = 1.99
            ((1.99, 1.99, 1.99, 5.99), 1.99, False),
        ],
    )
    def test_t_stat_boundary(
        self, tmp_path, monkeypatch, pnl_bps: tuple[float, ...], t_stat: float, met: bool
    ) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 5))
        _activate(monkeypatch, days[0])
        for day, pnl_bp in zip(days, pnl_bps):
            _write_day(
                root,
                day,
                {BookId.ugh_x1: _trade(1)},
                realized_close=101.0,
                live_bp={BookId.ugh_x1: (pnl_bp, 1.0)},
            )
        gate = _report(root, _after_close(days[-1]))["gate"]

        assert gate["blocked_reasons"] == ()
        assert gate["criteria"]["t_stat_live"]["current"] == pytest.approx(t_stat)
        assert gate["criteria"]["t_stat_live"]["met"] is met

    @pytest.mark.parametrize(
        ("close", "drawdown", "met"),
        [
            # position 3,000,000 / 100 = 30,000 USD; gross 30,000 × (90.01 − 100) = −299,700;
            # cost 30,000 × 0.01 = 300 → −300,000 = exactly 10.00% of 3,000,000 → passes
            (90.01, 0.10, True),
            # gross 30,000 × (90.0 − 100) = −300,000; cost 300 → −300,300 = 10.01% → fails
            (90.0, 0.1001, False),
        ],
    )
    def test_drawdown_boundary(
        self, tmp_path, monkeypatch, close: float, drawdown: float, met: bool
    ) -> None:
        root = str(tmp_path / "csv")
        day = date(2026, 3, 2)
        _activate(monkeypatch, day)
        _write_day(root, day, {BookId.ugh_x1: _trade(1)}, realized_close=close)
        gate = _report(root, _after_close(day))["gate"]

        assert gate["blocked_reasons"] == ()
        assert gate["criteria"]["max_drawdown_live"]["current"] == pytest.approx(drawdown)
        assert gate["criteria"]["max_drawdown_live"]["met"] is met

    def test_benchmark_tie_is_not_beaten(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_gate_history(root, days[0], days[-1], 2, tie=True)
        report = _report(root, _after_close(days[-1]))
        gate = report["gate"]

        x1_pnl = gate["criteria"]["beats_benchmarks"]["current"]
        assert gate["criteria"]["beats_benchmarks"]["threshold"]["bench_long"] == x1_pnl
        assert gate["criteria"]["beats_benchmarks"]["threshold"]["bench_gpt_m3"] == 0.0
        assert x1_pnl > 0.0
        assert gate["criteria"]["beats_benchmarks"]["met"] is False
        deltas = report["strata"]["x1"]["benchmark_deltas"]
        assert deltas["bench_long"] == {"pnl_jpy_live_delta": 0.0, "capture_bp_delta": 0.0}


# ---------------------------------------------------------------------------
# ゲート: cohort membership
# ---------------------------------------------------------------------------


class TestGateCohort:
    def test_cohort_independent_of_window(self, aggregation_root: tuple[str, datetime]) -> None:
        root, generated_at = aggregation_root
        whole = _report(root, generated_at)
        narrow = _report(root, generated_at, start=_as_of(_AGG_DAYS[3]), end=_as_of(_AGG_DAYS[3]))
        assert narrow["row_count"] == 6
        assert narrow["gate"] == whole["gate"]
        assert narrow["inventory"] == whole["inventory"]

    def test_other_version_and_backfill_rows_are_not_in_cohort(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 5))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(root, days[2], {BookId.ugh_x1: _trade(1)}, realized_close=101.0, version="x0")
        _write_day(
            root,
            days[3],
            {BookId.ugh_x1: _trade(1)},
            realized_close=101.0,
            entry_status="backfill_bar",
        )
        report = _report(root, _after_close(days[-1]))

        assert report["gate"]["cohort"]["trade_count"] == 2
        assert report["gate"]["cohort"]["observation_days"] == 2
        assert report["gate"]["cohort"]["last_as_of_jst"] == _as_of(days[1]).isoformat()
        # the stratum view still shows every row: x1 has 3 batches (two live, one backfill)
        assert _x1(report)["decision_count"] == 3
        assert _x1(report)["live_coverage_rate"] == pytest.approx(2 / 3)
        assert _x1(report, "x0")["decision_count"] == 1
        # days[2] has no current-version live decision, days[3] no live decision at all
        assert report["gate"]["blocked_reasons"] == ("missing_decisions", "missing_live")

    def test_trade_count_counts_ugh_x1_only(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 4))
        _activate(monkeypatch, days[0])
        for day in days:
            _write_day(
                root,
                day,
                {
                    BookId.ugh_beta_unit: _trade(1),
                    BookId.bench_gpt_m3: _trade(-1),
                    BookId.bench_long: _trade(1),
                },
                realized_close=101.0,
            )
        report = _report(root, _after_close(days[-1]))

        assert report["gate"]["cohort"]["trade_count"] == 0
        assert report["gate"]["cohort"]["observation_days"] == 3
        assert report["strata"]["x1"]["books"]["bench_long"]["trade_count"] == 3
        assert report["strata"]["x1"]["books"]["ugh_beta_unit"]["trade_count"] == 3
        assert _x1(report)["trade_count"] == 0

    def test_skip_rows_do_not_change_t_or_trade_count(self, tmp_path, monkeypatch) -> None:
        def _trades_only(root: str, days: list[date]) -> None:
            for day, pnl_bp in zip(days, (2.0, 2.0, 2.0, 6.0)):
                _write_day(
                    root,
                    day,
                    {BookId.ugh_x1: _trade(1)},
                    realized_close=101.0,
                    live_bp={BookId.ugh_x1: (pnl_bp, 1.0)},
                )

        days = _business_days(date(2026, 3, 2), date(2026, 3, 9))  # 6 business days
        _activate(monkeypatch, days[0])

        root_a = str(tmp_path / "a")
        _trades_only(root_a, days[:4])
        gate_a = _report(root_a, _after_close(days[3]))["gate"]

        root_b = str(tmp_path / "b")
        _trades_only(root_b, days[:4])
        for day in days[4:]:  # two live skip days (side 0, skip_reason flat)
            _write_day(root_b, day, {BookId.ugh_x1: _skip("flat")})
        report_b = _report(root_b, _after_close(days[-1]))
        gate_b = report_b["gate"]

        assert gate_a["criteria"]["t_stat_live"]["current"] == 2.0
        assert gate_b["criteria"]["t_stat_live"]["current"] == 2.0
        assert gate_a["cohort"]["trade_count"] == gate_b["cohort"]["trade_count"] == 4
        assert gate_b["cohort"]["observation_days"] == 6
        assert _x1(report_b)["signed_bp_live_t"] == 2.0
        assert _x1(report_b)["signed_bp_live_mean"] == 2.0
        assert _x1(report_b)["decision_count"] == 6
        assert _x1(report_b)["skip_counts"] == {"flat": 2}

    def test_strata_split_by_version_never_summed(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 4))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(root, days[2], {BookId.ugh_x1: _trade(1)}, realized_close=102.0, version="x0")
        report = _report(root, _after_close(days[-1]))

        assert list(report["strata"]) == ["x0", "x1"]
        assert _x1(report)["decision_count"] == 2
        assert _x1(report)["trade_count"] == 2
        assert _x1(report, "x0")["decision_count"] == 1
        # x1 live equity: 2 × (+1 % − cost): 3,000,000 → 3,029,700 → 3,059,697
        assert _x1(report)["final_equity_jpy_live"] == pytest.approx(3059697.0)
        # x0: one +2 % day: position 30,000; gross 60,000; cost 300 → 3,059,700
        assert _x1(report, "x0")["final_equity_jpy_live"] == pytest.approx(3059700.0)
        assert report["strata"]["x0"]["batch_count"] == 1
        assert report["strata"]["x1"]["batch_count"] == 2


# ---------------------------------------------------------------------------
# ゲート: blocking inventories
# ---------------------------------------------------------------------------


class TestBlockingInventory:
    def test_incomplete_batch_excluded_and_blocks(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(
            root,
            days[1],
            {BookId.ugh_x1: _trade(1)},
            realized_close=101.0,
            evaluation_books=EXECUTION_BOOK_ORDER[:5],  # bench_long evaluation row missing
        )
        generated_at = _before_close(days[1])  # pending window: only the incompleteness blocks
        collected = _collect(root, generated_at)

        assert collected.incomplete_batches == (
            IncompleteExecutionBatch(
                forecast_batch_id=_batch_id(days[1]),
                execution_version="x1",
                as_of_jst=_as_of(days[1]),
                missing_books=("bench_long",),
            ),
        )
        assert len(collected.rows) == 6
        assert {r["forecast_batch_id"] for r in collected.rows} == {_batch_id(days[0])}
        report = _report(root, generated_at)
        assert _x1(report)["decision_count"] == 1
        assert report["gate"]["cohort"]["trade_count"] == 1
        assert report["gate"]["blocked_reasons"] == ("incomplete_batches",)
        assert "incomplete_batches" in report["gate"]["blocked_reasons"]
        assert report["gate"]["passed"] is False
        assert report["inventory"]["incomplete_batches"]["count"] == 1
        assert report["inventory"]["incomplete_batches"]["items"][0]["missing_books"] == [
            "bench_long"
        ]

    def test_old_version_incomplete_batch_does_not_block(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(
            root,
            days[1],
            {BookId.ugh_x1: _trade(1)},
            realized_close=101.0,
            version="x0",
            evaluation_books=EXECUTION_BOOK_ORDER[:5],
        )
        generated_at = _before_close(days[1])
        collected = _collect(root, generated_at)

        assert collected.incomplete_batches == ()
        assert collected.archive_defects.incomplete_batches[0].execution_version == "x0"
        assert collected.archive_defects.incomplete_batches[0].as_of_jst == _as_of(days[1])
        assert collected.blocked_reasons() == ()
        assert _report(root, generated_at)["gate"]["blocked_reasons"] == ()

    @pytest.mark.parametrize("header_only", [False, True])
    def test_missing_evaluation_blocks(self, tmp_path, monkeypatch, header_only: bool) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        batch_dir = _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, evaluations=False)
        if header_only:
            _write_header_only_evaluations(batch_dir)
        collected = _collect(root, _after_close(days[1]))

        assert collected.missing_evaluations == (
            MissingExecutionEvaluation(
                forecast_batch_id=_batch_id(days[1]),
                execution_version="x1",
                as_of_jst=_as_of(days[1]),
                window_end_jst=_window_end(days[1]),
            ),
        )
        assert collected.missing_decisions == ()
        assert collected.missing_live == ()
        gate = _report(root, _after_close(days[1]))["gate"]
        assert gate["blocked_reasons"] == ("missing_evaluations",)
        assert "missing_evaluations" in gate["blocked_reasons"]
        assert gate["passed"] is False

    def test_pending_window_is_not_a_missing_evaluation(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, evaluations=False)
        generated_at = _before_close(days[1])
        collected = _collect(root, generated_at)

        assert collected.missing_evaluations == ()
        assert collected.blocked_reasons() == ()
        assert _report(root, generated_at)["gate"]["blocked_reasons"] == ()

    def test_header_only_decision_file_blocks(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_header_only_decisions(root, days[1])
        generated_at = _before_close(days[1])
        collected = _collect(root, generated_at)

        assert collected.incomplete_decision_batches == (f"history/20260303/{_batch_id(days[1])}",)
        gate = _report(root, generated_at)["gate"]
        assert gate["blocked_reasons"] == ("incomplete_decisions",)
        assert "incomplete_decisions" in gate["blocked_reasons"]
        assert gate["passed"] is False

    def test_missing_decisions_from_calendar_cohort(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 4))
        _activate(monkeypatch, days[0])
        published_batch = _write_forecast_only(root, days[0])  # forecast only, no execution.csv
        # days[1]: nothing at all in the archive (activation day .. first success)
        _write_day(root, days[2], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = _after_close(days[2])
        collected = _collect(root, generated_at)

        assert collected.missing_decisions == (
            MissingExecutionDecision(as_of_jst=_as_of(days[0]), forecast_batch_id=published_batch),
            MissingExecutionDecision(as_of_jst=_as_of(days[1]), forecast_batch_id=None),
        )
        assert collected.missing_live == (days[0], days[1])
        gate = _report(root, generated_at)["gate"]
        assert "missing_decisions" in gate["blocked_reasons"]
        assert gate["blocked_reasons"] == ("missing_decisions", "missing_live")
        assert gate["passed"] is False

    def test_activation_marker_is_not_inferred_from_first_success(
        self, tmp_path, monkeypatch
    ) -> None:
        """Regression guard: the cohort starts at the pinned marker, not at the first file."""
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 6))
        _activate(monkeypatch, days[0])
        for day in days[3:]:
            _write_day(root, day, {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        collected = _collect(root, _after_close(days[-1]))

        assert [m.as_of_jst.date() for m in collected.missing_decisions] == days[:3]
        assert all(m.forecast_batch_id is None for m in collected.missing_decisions)
        assert collected.missing_live == tuple(days[:3])

    def test_pre_activation_defects_are_archive_only(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 5))
        _activate(monkeypatch, days[3])  # D1..D3 are backfill territory
        _write_day(
            root,
            days[0],
            {BookId.ugh_x1: _trade(1)},
            entry_status="backfill_bar",
            decisions=False,
            evaluation_books=EXECUTION_BOOK_ORDER[1:],  # five books only
        )
        _write_day(
            root,
            days[1],
            {BookId.ugh_x1: _trade(1)},
            entry_status="backfill_bar",
            evaluations=False,
        )
        for suffix in ("_a", "_b"):  # two complete batches on the same day
            _write_day(
                root,
                days[2],
                {BookId.ugh_x1: _trade(1)},
                entry_status="backfill_bar",
                batch_id=_batch_id(days[2], suffix),
            )
        _write_day(root, days[3], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = _after_close(days[3])
        collected = _collect(root, generated_at)

        assert collected.blocked_reasons() == ()
        archive = collected.archive_defects
        assert [b.forecast_batch_id for b in archive.incomplete_batches] == [_batch_id(days[0])]
        assert archive.incomplete_batches[0].missing_books == ("ugh_x1",)
        assert [m.forecast_batch_id for m in archive.missing_evaluations] == [_batch_id(days[1])]
        assert archive.duplicate_batches == (days[2],)
        assert archive.missing_decisions == ()
        assert archive.missing_live == ()
        # the defective archive batches are excluded from aggregation as well
        assert {r["forecast_batch_id"] for r in collected.rows} == {_batch_id(days[3])}
        report = _report(root, generated_at)
        assert report["gate"]["blocked_reasons"] == ()
        assert report["inventory"]["archive_defects"]["duplicate_batches"]["items"] == [
            "2026-03-04"
        ]
        assert report["inventory"]["duplicate_batches"]["count"] == 0

    def test_backfill_day_stays_missing_live_until_excluded(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(
            root,
            days[0],
            {BookId.ugh_x1: _trade(1)},
            realized_close=101.0,
            entry_status="backfill_bar",
        )
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = _after_close(days[1])
        collected = _collect(root, generated_at)

        assert (
            collected.missing_decisions == ()
        )  # the backfill wrote a complete current-version file
        assert collected.missing_live == (days[0],)
        report = _report(root, generated_at)
        assert report["gate"]["blocked_reasons"] == ("missing_live",)
        assert report["gate"]["cohort"]["excluded_days"] == 0
        assert _x1(report)["decision_count"] == 2  # bar series still counts the backfill row
        assert report["gate"]["cohort"]["trade_count"] == 1

        _activate(monkeypatch, days[0], excluded=(days[0],))
        collected = _collect(root, generated_at)
        assert collected.missing_live == ()
        assert collected.blocked_reasons() == ()
        report = _report(root, generated_at)
        assert report["gate"]["blocked_reasons"] == ()
        assert report["gate"]["cohort"]["excluded_days"] == 1
        assert report["gate"]["cohort"]["excluded_as_of_jst"] == ["2026-03-02"]

    def test_live_unavailable_day_is_missing_live(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, entry_status="live_unavailable")
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        collected = _collect(root, _after_close(days[1]))

        assert collected.missing_decisions == ()
        assert collected.missing_live == (days[0],)
        assert collected.blocked_reasons() == ("missing_live",)

    def test_duplicate_batches_excluded_and_block(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        for suffix in ("_a", "_b"):
            _write_day(
                root,
                days[0],
                {BookId.ugh_x1: _trade(1)},
                realized_close=101.0,
                batch_id=_batch_id(days[0], suffix),
            )
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = _after_close(days[1])
        collected = _collect(root, generated_at)

        assert collected.duplicate_batches == (days[0],)
        assert collected.missing_decisions == ()
        assert collected.missing_live == ()
        assert {r["forecast_batch_id"] for r in collected.rows} == {_batch_id(days[1])}
        report = _report(root, generated_at)
        assert _x1(report)["decision_count"] == 1
        assert report["gate"]["cohort"]["trade_count"] == 1
        assert report["gate"]["blocked_reasons"] == ("duplicate_batches",)
        assert report["gate"]["passed"] is False
        assert report["inventory"]["duplicate_batches"]["items"] == ["2026-03-02"]


# ---------------------------------------------------------------------------
# Corrupt / partial sibling files and input normalisation
# ---------------------------------------------------------------------------


class TestArchiveRobustness:
    """Corrupt or partial sibling files become inventory entries; the report always completes."""

    def test_corrupt_forecast_csv_does_not_break_the_lookup(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_corrupt_bytes(
            os.path.join(root, "history", "20260302", _batch_id(days[0]), "forecast.csv")
        )
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = _after_close(days[1])
        collected = _collect(root, generated_at)

        assert collected.missing_decisions == (
            MissingExecutionDecision(as_of_jst=_as_of(days[0]), forecast_batch_id=None),
        )
        report = _report(root, generated_at)
        assert report["gate"]["blocked_reasons"] == ("missing_decisions", "missing_live")
        assert report["inventory"]["missing_decisions"]["items"][0]["forecast_batch_id"] is None
        paths = export_execution_report_artifacts(report, root, "weekly", "20260303")
        assert all(os.path.isfile(p) for p in paths.values())

    @pytest.mark.parametrize("kind", ["partial", "corrupt"])
    def test_partial_or_unreadable_decision_file_is_incomplete(
        self, tmp_path, monkeypatch, kind: str
    ) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        if kind == "partial":
            _write_decision_rows(root, days[1], 3)
        else:
            _write_corrupt_bytes(
                os.path.join(root, "history", "20260303", _batch_id(days[1]), "execution.csv")
            )
        generated_at = _before_close(days[1])  # pending window: only the broken file blocks
        collected = _collect(root, generated_at)

        assert collected.incomplete_decision_batches == (f"history/20260303/{_batch_id(days[1])}",)
        assert collected.blocked_reasons() == ("incomplete_decisions",)
        assert _report(root, generated_at)["gate"]["blocked_reasons"] == ("incomplete_decisions",)

    def test_pre_activation_incomplete_decision_file_is_archive_only(
        self, tmp_path, monkeypatch
    ) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[1])  # days[0] is before the marker
        _write_decision_rows(root, days[0], 3)
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = _after_close(days[1])
        collected = _collect(root, generated_at)

        assert collected.incomplete_decision_batches == ()
        assert collected.archive_defects.incomplete_decision_batches == (
            f"history/20260302/{_batch_id(days[0])}",
        )
        assert collected.blocked_reasons() == ()
        assert _report(root, generated_at)["gate"]["blocked_reasons"] == ()

    def test_unreadable_evaluation_file_is_a_missing_evaluation(
        self, tmp_path, monkeypatch
    ) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        batch_dir = _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, evaluations=False)
        _write_corrupt_bytes(os.path.join(batch_dir, "execution_evaluation.csv"))
        generated_at = _after_close(days[1])
        collected = _collect(root, generated_at)

        assert [m.forecast_batch_id for m in collected.missing_evaluations] == [_batch_id(days[1])]
        assert {r["forecast_batch_id"] for r in collected.rows} == {_batch_id(days[0])}
        assert collected.incomplete_batches == ()
        gate = _report(root, generated_at)["gate"]
        assert gate["blocked_reasons"] == ("missing_evaluations",)

    @pytest.mark.parametrize("field", ["execution_version", "as_of_jst"])
    def test_rows_disagreeing_on_batch_metadata_make_the_batch_incomplete(
        self, tmp_path, monkeypatch, field: str
    ) -> None:
        """Six valid rows that disagree on the batch metadata (a version boundary, a partial
        copy) are not reduced to the first row's values: the batch is incomplete and blocks."""
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        batch_dir = _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        path = os.path.join(batch_dir, "execution_evaluation.csv")
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = list(reader.fieldnames or ())
            rows = list(reader)
        rows[-1][field] = "x0" if field == "execution_version" else _as_of(days[0]).isoformat()
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        generated_at = _after_close(days[1])
        collected = _collect(root, generated_at)

        assert [m.forecast_batch_id for m in collected.incomplete_batches] == [_batch_id(days[1])]
        incomplete = collected.incomplete_batches[0]
        assert incomplete.missing_books == ()
        assert incomplete.inconsistent_fields == (field,)
        assert incomplete.execution_version == "x1"  # routed by the current version
        assert incomplete.as_of_jst == _as_of(days[1])  # routed by the latest day
        assert {r["forecast_batch_id"] for r in collected.rows} == {_batch_id(days[0])}
        gate = _report(root, generated_at)["gate"]
        assert "incomplete_batches" in gate["blocked_reasons"]
        assert gate["cohort"]["trade_count"] == 1  # the mixed batch's rows never reach the gate

    def test_naive_generated_at_is_treated_as_utc(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        assert generated_at.tzinfo is _UTC
        naive = generated_at.replace(tzinfo=None)
        assert _collect(root, naive) == _collect(root, generated_at)
        assert _report(root, naive) == _report(root, generated_at)


# ---------------------------------------------------------------------------
# Activation / version split and calendar cohort, tested directly
# ---------------------------------------------------------------------------


class TestActivationSplit:
    @pytest.mark.parametrize(
        ("as_of", "version", "blocking"),
        [
            (date(2026, 3, 4), "x1", False),  # day before the marker
            (date(2026, 3, 5), "x1", True),  # marker day, current version
            (date(2026, 3, 6), "x1", True),
            (date(2026, 3, 5), "x0", False),  # another version never blocks
            (date(2026, 3, 5), None, True),  # unreadable version on/after the marker blocks
            (date(2026, 3, 4), None, False),
            (datetime(2026, 3, 4, 23, 30, tzinfo=_UTC), "x1", True),  # = 03-05 08:30 JST
        ],
    )
    def test_is_gate_blocking_defect(
        self, monkeypatch, as_of: date | datetime, version: str | None, blocking: bool
    ) -> None:
        _activate(monkeypatch, date(2026, 3, 5))
        assert is_gate_blocking_defect(as_of, version) is blocking

    def test_expected_days_close_with_the_window(self, monkeypatch) -> None:
        _activate(monkeypatch, date(2026, 3, 5))  # Thursday
        # Friday's window closes Monday 08:00 JST; one hour later both days are expected
        expected, excluded = expected_decision_days(datetime(2026, 3, 9, 0, 0, tzinfo=_UTC))
        assert expected == (date(2026, 3, 5), date(2026, 3, 6))
        assert excluded == ()
        # one hour before Friday's window closes only Thursday is expected
        expected, _ = expected_decision_days(datetime(2026, 3, 8, 22, 0, tzinfo=_UTC))
        assert expected == (date(2026, 3, 5),)
        # before Thursday's own window closes nothing is expected
        assert expected_decision_days(datetime(2026, 3, 5, 12, 0, tzinfo=_UTC)) == ((), ())

    def test_excluded_days_are_removed_and_counted(self, monkeypatch) -> None:
        _activate(monkeypatch, date(2026, 3, 5), excluded=(date(2026, 3, 6), date(2026, 3, 7)))
        expected, excluded = expected_decision_days(datetime(2026, 3, 9, 0, 0, tzinfo=_UTC))
        assert expected == (date(2026, 3, 5),)
        assert excluded == (date(2026, 3, 6),)  # the Saturday is never a candidate

    def test_blocked_reason_order_is_canonical(self) -> None:
        assert GATE_BLOCKED_REASONS == (
            "incomplete_batches",
            "missing_evaluations",
            "incomplete_decisions",
            "missing_decisions",
            "missing_live",
            "duplicate_batches",
        )

    def test_excluded_as_of_entries_are_cohort_candidates(self) -> None:
        """A typo'd exclusion (weekend, or before the marker) would remove nothing: fail CI instead.

        Checks the real constants of ``execution.py`` (not the patched module attributes).
        """
        for day in EXECUTION_EXCLUDED_AS_OF:
            assert day >= EXECUTION_ACTIVATION_AS_OF, day
            assert is_protocol_business_day(_as_of(day)), day

    def test_excluded_days_outside_the_cohort_are_not_counted(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        marker = date(2026, 3, 5)  # Thursday
        before_marker, saturday, friday = date(2026, 3, 3), date(2026, 3, 7), date(2026, 3, 6)
        _activate(monkeypatch, marker, excluded=(before_marker, saturday, friday))
        _write_day(root, marker, {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        generated_at = datetime(2026, 3, 9, 0, 0, tzinfo=_UTC)  # Friday's window has closed

        expected, excluded = expected_decision_days(generated_at)
        assert expected == (marker,)
        assert excluded == (friday,)
        report = _report(root, generated_at)
        assert report["gate"]["cohort"]["excluded_days"] == 1
        assert report["gate"]["cohort"]["excluded_as_of_jst"] == ["2026-03-06"]
        assert report["gate"]["blocked_reasons"] == ()


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


class TestExport:
    @pytest.mark.parametrize(("scope", "date_str"), [("weekly", "20260309"), ("monthly", "202603")])
    def test_three_formats_written(
        self, aggregation_root: tuple[str, datetime], scope: str, date_str: str
    ) -> None:
        root, generated_at = aggregation_root
        report = _report(root, generated_at)
        paths = export_execution_report_artifacts(report, root, scope, date_str)

        out_dir = os.path.join(root, "analytics", "execution", scope, date_str)
        assert paths == {
            f"execution_{scope}_md": os.path.join(out_dir, f"execution_{scope}.md"),
            f"execution_{scope}_csv": os.path.join(out_dir, f"execution_{scope}.csv"),
            f"execution_{scope}_json": os.path.join(out_dir, f"execution_{scope}.json"),
        }
        for path in paths.values():
            assert os.path.isfile(path)

        with open(paths[f"execution_{scope}_json"], encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded["gate"]["blocked_reasons"] == ["missing_live"]
        assert loaded["strata"]["x1"]["books"]["ugh_x1"]["trade_count"] == 5

        with open(paths[f"execution_{scope}_csv"], newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            assert tuple(reader.fieldnames or ()) == EXECUTION_REPORT_BOOK_FIELDNAMES
        assert [r["book_id"] for r in rows] == [b.value for b in EXECUTION_BOOK_ORDER]
        assert rows[0]["execution_version"] == "x1"
        assert rows[0]["skip_counts"] == "shock_filter=1"
        assert rows[0]["signed_bp_live_t"] == ""  # None → blank cell
        assert float(rows[5]["pnl_jpy_live"]) == pytest.approx(42420.80193530256)

        with open(paths[f"execution_{scope}_md"], encoding="utf-8") as fh:
            md = fh.read()
        assert "## Stratum execution_version=x1" in md
        assert "### Books" in md
        assert "### Benchmark deltas" in md
        assert "## Acceptance gate" in md
        assert "| ugh_x1 | 6 | 5 | shock_filter=1 | 50.0% | 80.0% | 400.5 |" in md
        assert "| bench_long |" in md
        assert "Blocked reasons: missing_live" in md
        assert "Passed: no" in md
        assert not os.path.exists(os.path.join(root, "latest", "execution_summary.json"))

    def test_latest_summary_is_window_independent(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        latest_path = os.path.join(root, "latest", "execution_summary.json")

        def _weekly_then_latest(start: date, end: date, date_str: str) -> bytes:
            weekly = _report(root, generated_at, start=_as_of(start), end=_as_of(end))
            export_execution_report_artifacts(weekly, root, "weekly", date_str)
            cumulative = _report(root, generated_at)
            assert export_execution_latest_summary(cumulative, root) == latest_path
            with open(latest_path, "rb") as fh:
                return fh.read()

        first = _weekly_then_latest(_AGG_DAYS[0], _AGG_DAYS[2], "20260304")
        second = _weekly_then_latest(_AGG_DAYS[3], _AGG_DAYS[5], "20260309")
        assert first == second

        with open(latest_path, encoding="utf-8") as fh:
            summary = json.load(fh)
        assert summary["window"] == {"start_as_of_jst": None, "end_as_of_jst": None}
        assert summary["strata"]["x1"]["books"]["ugh_x1"]["decision_count"] == 6
        assert summary["gate"]["cohort"]["trade_count"] == 2

    def test_latest_summary_rejects_windowed_report(
        self, aggregation_root: tuple[str, datetime]
    ) -> None:
        root, generated_at = aggregation_root
        weekly = _report(root, generated_at, start=_as_of(_AGG_DAYS[0]), end=_as_of(_AGG_DAYS[2]))
        with pytest.raises(ValueError, match="cumulative"):
            export_execution_latest_summary(weekly, root)
        assert not os.path.exists(os.path.join(root, "latest", "execution_summary.json"))

    @pytest.mark.parametrize("date_str", ["20260309", "202603"])
    def test_valid_date_str_accepted(
        self, aggregation_root: tuple[str, datetime], date_str: str
    ) -> None:
        root, generated_at = aggregation_root
        paths = export_execution_report_artifacts(
            _report(root, generated_at), root, "weekly", date_str
        )
        expected_dir = os.path.join(root, "analytics", "execution", "weekly", date_str)
        assert all(os.path.dirname(p) == expected_dir for p in paths.values())

    @pytest.mark.parametrize(
        "date_str", ["../../escaped", "2026-03-09", "2026030", "202603a", "", "2026030912"]
    )
    def test_invalid_date_str_rejected(
        self, aggregation_root: tuple[str, datetime], date_str: str
    ) -> None:
        root, generated_at = aggregation_root
        report = _report(root, generated_at)
        with pytest.raises(ValueError, match="date_str"):
            export_execution_report_artifacts(report, root, "weekly", date_str)
        assert not os.path.exists(os.path.join(root, "analytics"))  # nothing written anywhere

    @pytest.mark.parametrize("scope", ["..", "", "daily", "weekly/x", "weekly/../x", "Weekly"])
    def test_invalid_scope_rejected(
        self, aggregation_root: tuple[str, datetime], scope: str
    ) -> None:
        root, generated_at = aggregation_root
        report = _report(root, generated_at)
        with pytest.raises(ValueError, match="scope"):
            export_execution_report_artifacts(report, root, scope, "20260309")
        assert not os.path.exists(os.path.join(root, "analytics"))  # nothing written anywhere

    def test_two_strata_render_two_book_tables(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        days = _business_days(date(2026, 3, 2), date(2026, 3, 3))
        _activate(monkeypatch, days[0])
        _write_day(root, days[0], {BookId.ugh_x1: _trade(1)}, realized_close=101.0)
        _write_day(root, days[1], {BookId.ugh_x1: _trade(1)}, realized_close=102.0, version="x0")
        report = _report(root, _after_close(days[1]))
        paths = export_execution_report_artifacts(report, root, "monthly", "202603")

        with open(paths["execution_monthly_md"], encoding="utf-8") as fh:
            md = fh.read()
        assert md.count("## Stratum execution_version=") == 2
        assert md.count("### Books") == 2
        assert md.count("### Benchmark deltas") == 2
        assert md.count("## Acceptance gate") == 1
        assert md.index("execution_version=x0") < md.index("execution_version=x1")
        with open(paths["execution_monthly_csv"], newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 12
        assert [r["execution_version"] for r in rows] == ["x0"] * 6 + ["x1"] * 6
        assert [r["book_id"] for r in rows[:6]] == [b.value for b in EXECUTION_BOOK_ORDER]
        assert [r["book_id"] for r in rows[6:]] == [b.value for b in EXECUTION_BOOK_ORDER]

    def test_empty_archive_exports(self, tmp_path, monkeypatch) -> None:
        root = str(tmp_path / "csv")
        _activate(monkeypatch, date(2026, 3, 2))
        report = _report(root, _before_close(date(2026, 3, 2)))
        paths = export_execution_report_artifacts(report, root, "weekly", "20260302")
        with open(paths["execution_weekly_md"], encoding="utf-8") as fh:
            md = fh.read()
        assert "No complete batches in the window." in md
        assert "Blocked reasons: none" in md
        assert report["gate"]["passed"] is False


def test_skip_counts_cell_never_contains_a_table_pipe() -> None:
    """Two skip reasons on one book render as ``a=n;b=m``: a ``|`` would split the md cell."""
    rendered = reporting._fmt_skip_counts({"flat": 1, "agree_with_technical": 4})

    assert rendered == "agree_with_technical=4;flat=1"
    assert "|" not in rendered
    assert reporting._fmt_skip_counts({}) == ""


def test_module_importable_without_sqlalchemy() -> None:
    """The module must import when SQLAlchemy is absent (CLAUDE.md import isolation).

    Same idea as the replay import-isolation tests, but in a fresh interpreter so
    no cached module can mask a transitive import: ``sys.modules["sqlalchemy"] =
    None`` makes any ``import sqlalchemy`` raise ``ImportError``.  ``PYTHONPATH``
    points at this checkout's ``src`` so an editable install of another checkout
    is not what gets imported; the printed ``__file__`` verifies that.
    """
    code = (
        "import sys; sys.modules['sqlalchemy'] = None; "
        "import ugh_quantamental.fx_protocol.execution_reporting as m; print(m.__file__)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": _SRC_DIR},
    )
    expected = os.path.join(_SRC_DIR, "ugh_quantamental", "fx_protocol", "execution_reporting.py")
    assert result.stdout.strip() == expected
