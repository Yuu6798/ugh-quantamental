"""Tests for ``scripts/backfill_execution_history.py`` (spec §10, brief FX-EXEC-REPORTING).

The script is loaded by file path like the other script tests under ``tests/``.
Every test builds a synthetic ``fx-daily-data`` checkout under ``tmp_path`` in
the production ``csv/history/{YYYYMMDD}/{forecast_batch_id}/`` layout: a batch's
``forecast.csv`` and ``input_snapshot.json`` sit in its own start-date
directory, while its ``outcome.csv`` / ``evaluation.csv`` sit in the *next*
day's batch directory (or, for a window recovered by outcome catch-up, in the
window's end-date directory next to a copy of ``forecast.csv``).  No network,
no clock: every timestamp is pinned.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol import execution as execution_module
from ugh_quantamental.fx_protocol.calendar import next_as_of_jst, prev_as_of_jst
from ugh_quantamental.fx_protocol.csv_exports import (
    EVALUATION_FIELDNAMES,
    FORECAST_FIELDNAMES,
    OUTCOME_FIELDNAMES,
)
from ugh_quantamental.fx_protocol.csv_utils import write_csv_rows
from ugh_quantamental.fx_protocol.data_models import FxCompletedWindow, FxProtocolMarketSnapshot
from ugh_quantamental.fx_protocol.execution import (
    build_execution_decisions,
    evaluate_execution_decisions,
)
from ugh_quantamental.fx_protocol.execution_exports import (
    EXECUTION_EVALUATION_FIELDNAMES,
    EXECUTION_FIELDNAMES,
    decisions_to_rows,
    evaluations_to_rows,
    is_complete_decision_file,
    is_complete_evaluation_file,
    load_execution_decisions_csv,
    load_execution_evaluations_csv,
)
from ugh_quantamental.fx_protocol.execution_models import (
    EXECUTION_BOOK_ORDER,
    EntryStatus,
    ExecutionDecision,
)
from ugh_quantamental.fx_protocol.ids import (
    make_forecast_batch_id,
    make_forecast_id,
    make_outcome_id,
)
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    ForecastDirection,
    MarketDataProvenance,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.observability import build_input_snapshot, write_json_artifact
from ugh_quantamental.fx_protocol.request_builders import build_baseline_context

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "backfill_execution_history.py"
_spec = importlib.util.spec_from_file_location("backfill_execution_history", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
backfill = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = backfill
_spec.loader.exec_module(backfill)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_PAIR = CurrencyPair.USDJPY
_PROTOCOL_VERSION = "v1"
_SCHEMA_VERSION = "v1"

# Protocol business days (2026-05-11 is a Monday; 05-15 Friday; 05-18 Monday).
_D0 = datetime(2026, 5, 7, 8, 0, tzinfo=_JST)  # the day before the first persisted forecast
_D1 = datetime(2026, 5, 11, 8, 0, tzinfo=_JST)  # complete triple
_D2 = datetime(2026, 5, 12, 8, 0, tzinfo=_JST)  # partial forecast (6 rows)
_D3 = datetime(2026, 5, 13, 8, 0, tzinfo=_JST)  # evaluated by outcome catch-up (end-date dir)
_D4 = datetime(2026, 5, 14, 8, 0, tzinfo=_JST)  # complete execution.csv, no evaluation file
_D5 = datetime(2026, 5, 15, 8, 0, tzinfo=_JST)  # window not evaluated yet
_D6 = datetime(2026, 5, 18, 8, 0, tzinfo=_JST)  # no input_snapshot.json
_D7 = datetime(2026, 5, 19, 8, 0, tzinfo=_JST)  # hosts _D6's outcome only (no forecast of its own)
_D8 = datetime(2026, 5, 20, 8, 0, tzinfo=_JST)  # execution.csv without any forecast rows
_D9 = datetime(2026, 5, 21, 8, 0, tzinfo=_JST)  # forecast only in the catch-up end-date dir

#: The seven strategies of a complete daily batch (``EXPECTED_DAILY_BATCH_SIZE``).
_DAILY_KINDS: tuple[StrategyKind, ...] = (
    StrategyKind.ugh_v2_alpha,
    StrategyKind.ugh_v2_beta,
    StrategyKind.ugh_v2_gamma,
    StrategyKind.ugh_v2_delta,
    StrategyKind.baseline_random_walk,
    StrategyKind.baseline_prev_day_direction,
    StrategyKind.baseline_simple_technical,
)
#: Six rows: the dropped baseline is one no book reads, so the 7-row rule itself is tested.
_PARTIAL_KINDS: tuple[StrategyKind, ...] = tuple(
    kind for kind in _DAILY_KINDS if kind != StrategyKind.baseline_random_walk
)
_DIRECTIONS: dict[StrategyKind, ForecastDirection] = {
    StrategyKind.ugh_v2_alpha: ForecastDirection.up,
    StrategyKind.ugh_v2_beta: ForecastDirection.up,
    StrategyKind.ugh_v2_gamma: ForecastDirection.up,
    StrategyKind.ugh_v2_delta: ForecastDirection.flat,
    StrategyKind.baseline_random_walk: ForecastDirection.flat,
    StrategyKind.baseline_prev_day_direction: ForecastDirection.up,
    StrategyKind.baseline_simple_technical: ForecastDirection.down,
}

#: Every per-batch counter of ``BackfillSummary``; together they partition ``batches``.
_COUNTERS: tuple[str, ...] = (
    "written_decisions_and_evaluations",
    "written_evaluations_only",
    "already_complete",
    "before_backfill_start",
    "missing_forecast",
    "partial_forecast",
    "missing_outcome",
    "unusable_outcome",
    "missing_snapshot",
    "unusable_inputs",
    "contradictory_archive",
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _batch_id(as_of: datetime) -> str:
    return make_forecast_batch_id(_PAIR, as_of, _PROTOCOL_VERSION)


def _window_end(as_of: datetime) -> datetime:
    return next_as_of_jst(as_of)


def _batch_dir(csv_root: Path, as_of: datetime, batch_id: str | None = None) -> Path:
    """``history/{as_of:%Y%m%d}/{batch_id}`` (the batch's own id unless another is given)."""
    return csv_root / "history" / as_of.strftime("%Y%m%d") / (batch_id or _batch_id(as_of))


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 5, 1, 0, 0, tzinfo=_UTC),
    )


def _snapshot(as_of: datetime, n: int = 20) -> FxProtocolMarketSnapshot:
    """*n* completed windows ending at *as_of* with varying, valid OHLC."""
    windows: list[FxCompletedWindow] = []
    end = as_of
    for i in range(n):
        start = prev_as_of_jst(end)
        open_price = 150.0 + 0.05 * ((i * 3) % 11)
        close_price = 150.0 + 0.05 * ((i * 7) % 11)
        windows.append(
            FxCompletedWindow(
                window_start_jst=start,
                window_end_jst=end,
                open_price=open_price,
                high_price=max(open_price, close_price) + 0.3,
                low_price=min(open_price, close_price) - 0.3,
                close_price=close_price,
            )
        )
        end = start
    windows.reverse()
    return FxProtocolMarketSnapshot(
        pair=_PAIR,
        as_of_jst=as_of,
        current_spot=150.2,
        completed_windows=tuple(windows),
        market_data_provenance=_provenance(),
    )


def _write_snapshot(batch_dir: Path, snapshot: FxProtocolMarketSnapshot) -> None:
    write_json_artifact(
        str(batch_dir / "input_snapshot.json"),
        build_input_snapshot(snapshot, datetime(2026, 5, 1, 0, 0, tzinfo=_UTC)),
    )


def _write_forecast(
    batch_dir: Path, as_of: datetime, kinds: tuple[StrategyKind, ...] = _DAILY_KINDS
) -> None:
    """``forecast.csv`` for the batch of *as_of* with one row per kind (other columns blank)."""
    rows = [
        {
            "forecast_id": make_forecast_id(_PAIR, as_of, _PROTOCOL_VERSION, kind),
            "forecast_batch_id": _batch_id(as_of),
            "pair": _PAIR.value,
            "strategy_kind": kind.value,
            "as_of_jst": as_of.isoformat(),
            "window_end_jst": _window_end(as_of).isoformat(),
            "forecast_direction": _DIRECTIONS[kind].value,
        }
        for kind in kinds
    ]
    write_csv_rows(str(batch_dir / "forecast.csv"), rows, FORECAST_FIELDNAMES)


def _write_outcome_and_evaluation(
    batch_dir: Path,
    as_of: datetime,
    *,
    realized: tuple[float, float],
    evaluated_at: datetime,
    kinds: tuple[StrategyKind, ...] = _DAILY_KINDS,
) -> str:
    """``outcome.csv`` + ``evaluation.csv`` for the window of *as_of*; returns the outcome id."""
    window_end = _window_end(as_of)
    outcome_id = make_outcome_id(_PAIR, as_of, window_end, _SCHEMA_VERSION)
    realized_open, realized_close = realized
    write_csv_rows(
        str(batch_dir / "outcome.csv"),
        [
            {
                "outcome_id": outcome_id,
                "pair": _PAIR.value,
                "window_start_jst": as_of.isoformat(),
                "window_end_jst": window_end.isoformat(),
                "realized_open": realized_open,
                "realized_high": max(realized) + 0.5,
                "realized_low": min(realized) - 0.5,
                "realized_close": realized_close,
            }
        ],
        OUTCOME_FIELDNAMES,
    )
    write_csv_rows(
        str(batch_dir / "evaluation.csv"),
        [
            {
                "evaluation_id": f"ev_{kind.value}_{as_of:%Y%m%d}",
                "forecast_id": make_forecast_id(_PAIR, as_of, _PROTOCOL_VERSION, kind),
                "outcome_id": outcome_id,
                "pair": _PAIR.value,
                "strategy_kind": kind.value,
                "evaluated_at_utc": evaluated_at.isoformat(),
            }
            for kind in kinds
        ],
        EVALUATION_FIELDNAMES,
    )
    return outcome_id


def _decisions(
    snapshot: FxProtocolMarketSnapshot,
    as_of: datetime,
    *,
    entry_status: EntryStatus,
    decided_at_utc: datetime,
) -> tuple[ExecutionDecision, ...]:
    """The six decisions the real builder derives for *as_of* from *snapshot* + ``_DIRECTIONS``."""
    return build_execution_decisions(
        forecast_directions=_DIRECTIONS,
        baseline_context=build_baseline_context(snapshot),
        completed_closes=tuple(w.close_price for w in snapshot.completed_windows),
        as_of_jst=as_of,
        window_end_jst=_window_end(as_of),
        forecast_batch_id=_batch_id(as_of),
        entry_status=entry_status,
        live_entry=None,
        decided_at_utc=decided_at_utc,
    )


def _write_decisions(batch_dir: Path, decisions: tuple[ExecutionDecision, ...]) -> None:
    write_csv_rows(
        str(batch_dir / "execution.csv"), decisions_to_rows(decisions), EXECUTION_FIELDNAMES
    )


def _truncate_last_row(path: Path, n_fields: int) -> None:
    """Cut the last data row of a CSV to its first *n_fields* cells, like an interrupted copy."""
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[-1] = ",".join(lines[-1].split(",")[:n_fields])
    path.write_text("\r\n".join(lines), encoding="utf-8")


def _edit_csv(path: Path, mutate: Callable[[list[dict[str, str]]], None]) -> None:
    """Rewrite a CSV after applying *mutate* to its rows (header kept)."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@dataclass(frozen=True)
class _Layout:
    root: Path
    csv_root: Path
    realized: dict[str, tuple[float, float]]
    evaluated_at: dict[str, datetime]
    outcome_ids: dict[str, str]
    snapshots: dict[str, FxProtocolMarketSnapshot]
    existing_decisions: dict[str, tuple[ExecutionDecision, ...]]


_AS_OF: dict[str, datetime] = {
    "complete": _D1,
    "partial": _D2,
    "catchup": _D3,
    "repair": _D4,
    "pending": _D5,
    "no_snapshot": _D6,
    "no_forecast": _D8,
}
_EXPECTED_BATCHES = len(_AS_OF)


def _build_checkout(root: Path) -> _Layout:
    """A synthetic ``fx-daily-data`` checkout with one batch per case (see ``_AS_OF``)."""
    csv_root = root / "csv"
    realized = {
        "complete": (150.10, 150.60),
        "partial": (150.60, 150.20),
        "catchup": (150.30, 149.90),
        "repair": (150.40, 150.45),
        "no_snapshot": (149.95, 150.25),
    }
    evaluated_at = {
        label: _window_end(_AS_OF[label]).astimezone(_UTC) + timedelta(hours=1)
        for label in realized
    }
    snapshots = {label: _snapshot(as_of) for label, as_of in _AS_OF.items()}
    outcome_ids: dict[str, str] = {}
    existing: dict[str, tuple[ExecutionDecision, ...]] = {}

    def evaluated(label: str, host_dir: Path) -> None:
        outcome_ids[label] = _write_outcome_and_evaluation(
            host_dir, _AS_OF[label], realized=realized[label], evaluated_at=evaluated_at[label]
        )

    # complete: forecast + snapshot in its own dir; outcome / evaluation in the next day's batch dir.
    own = _batch_dir(csv_root, _D1)
    _write_forecast(own, _D1)
    _write_snapshot(own, snapshots["complete"])
    evaluated("complete", _batch_dir(csv_root, _D2))

    # partial: six forecast rows (+ snapshot); outcome / evaluation in the next day's batch dir.
    own = _batch_dir(csv_root, _D2)
    _write_forecast(own, _D2, kinds=_PARTIAL_KINDS)
    _write_snapshot(own, snapshots["partial"])
    evaluated("partial", _batch_dir(csv_root, _D3))

    # catchup: forecast + snapshot in the start-date dir; the window's END-date dir holds a
    # copy of forecast.csv next to outcome / evaluation, as outcome catch-up publishes it.
    own = _batch_dir(csv_root, _D3)
    _write_forecast(own, _D3)
    _write_snapshot(own, snapshots["catchup"])
    end_dir = _batch_dir(csv_root, _D4, _batch_id(_D3))
    _write_forecast(end_dir, _D3)
    evaluated("catchup", end_dir)

    # repair: a daily run recorded live_unavailable decisions but never evaluated them; the
    # forecast is partial and there is no snapshot, neither of which the repair path needs.
    own = _batch_dir(csv_root, _D4)
    _write_forecast(own, _D4, kinds=_PARTIAL_KINDS)
    existing["repair"] = _decisions(
        snapshots["repair"],
        _D4,
        entry_status="live_unavailable",
        decided_at_utc=datetime(2026, 5, 14, 11, 0, tzinfo=_UTC),
    )
    _write_decisions(own, existing["repair"])
    evaluated("repair", _batch_dir(csv_root, _D5))

    # pending: complete forecast + snapshot, but the window has not been evaluated anywhere.
    own = _batch_dir(csv_root, _D5)
    _write_forecast(own, _D5)
    _write_snapshot(own, snapshots["pending"])

    # no_snapshot: complete forecast, evaluated in a next-day dir that has no forecast of its own.
    own = _batch_dir(csv_root, _D6)
    _write_forecast(own, _D6)
    evaluated("no_snapshot", _batch_dir(csv_root, _D7))

    # no_forecast: a complete execution.csv whose batch has no forecast rows anywhere.
    existing["no_forecast"] = _decisions(
        snapshots["no_forecast"],
        _D8,
        entry_status="live_unavailable",
        decided_at_utc=datetime(2026, 5, 20, 11, 0, tzinfo=_UTC),
    )
    _write_decisions(_batch_dir(csv_root, _D8), existing["no_forecast"])

    return _Layout(
        root=root,
        csv_root=csv_root,
        realized=realized,
        evaluated_at=evaluated_at,
        outcome_ids=outcome_ids,
        snapshots=snapshots,
        existing_decisions=existing,
    )


def _all_files(csv_root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(csv_root)): path.read_bytes()
        for path in sorted(csv_root.rglob("*"))
        if path.is_file()
    }


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _run(layout: _Layout, *, dry_run: bool = False) -> tuple[backfill.BackfillSummary, list[str]]:
    lines: list[str] = []
    summary = backfill.run_backfill(str(layout.csv_root), dry_run=dry_run, log=lines.append)
    return summary, lines


def _counter_sum(summary: backfill.BackfillSummary) -> int:
    return sum(getattr(summary, name) for name in _COUNTERS)


def _assert_first_pass_counts(summary: backfill.BackfillSummary) -> None:
    assert summary.batches == _EXPECTED_BATCHES
    assert summary.written_decisions_and_evaluations == 2  # complete, catchup
    assert summary.written_evaluations_only == 1  # repair
    assert summary.already_complete == 0
    assert summary.before_backfill_start == 0
    assert summary.missing_forecast == 1  # no_forecast
    assert summary.partial_forecast == 1  # partial
    assert summary.missing_outcome == 1  # pending
    assert summary.unusable_outcome == 0
    assert summary.missing_snapshot == 1  # no_snapshot
    assert summary.unusable_inputs == 0
    assert summary.contradictory_archive == 0
    assert _counter_sum(summary) == summary.batches


# ---------------------------------------------------------------------------
# Full path: decisions + evaluations with entry_status = backfill_bar
# ---------------------------------------------------------------------------


def test_first_run_writes_backfill_bar_decisions_and_evaluations(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    summary, _ = _run(layout)

    _assert_first_pass_counts(summary)
    assert summary.dry_run is False
    batch_dir = _batch_dir(layout.csv_root, _D1)
    decision_file = batch_dir / "execution.csv"
    evaluation_file = batch_dir / "execution_evaluation.csv"
    assert is_complete_decision_file(str(decision_file))
    assert is_complete_evaluation_file(str(evaluation_file))
    rel = f"history/{_D1:%Y%m%d}/{_batch_id(_D1)}"
    assert f"{rel}/execution.csv" in summary.files
    assert f"{rel}/execution_evaluation.csv" in summary.files
    assert len(summary.files) == 2 * 2 + 1

    rows = _read_rows(decision_file)
    assert [row["book_id"] for row in rows] == [book.value for book in EXECUTION_BOOK_ORDER]
    assert {row["entry_status"] for row in rows} == {"backfill_bar"}
    assert {row["entry_price_live"] for row in rows} == {""}
    assert {row["entry_vendor"] for row in rows} == {""}
    assert {row["entry_feed"] for row in rows} == {""}
    # decided_at_utc = as_of_jst (08:00 JST) converted to UTC, not a clock reading.
    assert {row["entry_time_utc"] for row in rows} == {"2026-05-10T23:00:00+00:00"}

    expected_decisions = _decisions(
        layout.snapshots["complete"],
        _D1,
        entry_status="backfill_bar",
        decided_at_utc=_D1.astimezone(_UTC),
    )
    assert load_execution_decisions_csv(str(decision_file)) == expected_decisions

    evaluation_rows = _read_rows(evaluation_file)
    assert {row["entry_status"] for row in evaluation_rows} == {"backfill_bar"}
    assert {row["pnl_live_bp"] for row in evaluation_rows} == {""}
    assert {row["cost_live_bp"] for row in evaluation_rows} == {""}
    assert {row["outcome_id"] for row in evaluation_rows} == {layout.outcome_ids["complete"]}
    assert {row["evaluated_at_utc"] for row in evaluation_rows} == {
        layout.evaluated_at["complete"].isoformat()
    }
    traded = [row for row in evaluation_rows if row["side"] != "0"]
    assert traded and all(row["pnl_bar_bp"] != "" for row in traded)

    realized_open, realized_close = layout.realized["complete"]
    expected_evaluations = evaluate_execution_decisions(
        expected_decisions,
        outcome_id=layout.outcome_ids["complete"],
        window_start_jst=_D1,
        realized_open=realized_open,
        realized_close=realized_close,
        evaluated_at_utc=layout.evaluated_at["complete"],
    )
    assert load_execution_evaluations_csv(str(evaluation_file)) == expected_evaluations


def test_staging_files_never_land_in_the_checkout(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    _run(layout)

    assert not (layout.csv_root / "execution").exists()
    written = {
        path for path, _ in _all_files(layout.csv_root).items() if "execution" in Path(path).name
    }
    assert all(path.startswith("history/") for path in written)


# ---------------------------------------------------------------------------
# Skips by reason
# ---------------------------------------------------------------------------


def test_partial_forecast_batch_is_skipped(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    summary, lines = _run(layout)

    assert summary.partial_forecast == 1
    batch_dir = _batch_dir(layout.csv_root, _D2)
    assert not (batch_dir / "execution.csv").exists()
    assert not (batch_dir / "execution_evaluation.csv").exists()
    skip_lines = [line for line in lines if line.startswith("[SKIP]")]
    assert any(_batch_id(_D2) in line and "partial forecast" in line for line in skip_lines)


def test_other_skip_reasons_are_counted_and_logged(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    summary, lines = _run(layout)

    skip_lines = [line for line in lines if line.startswith("[SKIP]")]
    assert len(skip_lines) == 4
    assert any(_batch_id(_D5) in line and "missing outcome" in line for line in skip_lines)
    assert any(_batch_id(_D6) in line and "missing snapshot" in line for line in skip_lines)
    assert any(_batch_id(_D8) in line and "missing forecast" in line for line in skip_lines)
    for as_of in (_D5, _D6):
        assert not (_batch_dir(layout.csv_root, as_of) / "execution.csv").exists()
    # The decision file without a forecast is left exactly as it was.
    assert summary.missing_forecast == 1
    assert (
        load_execution_decisions_csv(str(_batch_dir(layout.csv_root, _D8) / "execution.csv"))
        == layout.existing_decisions["no_forecast"]
    )
    assert not (_batch_dir(layout.csv_root, _D8) / "execution_evaluation.csv").exists()
    # A directory holding only outcome / evaluation rows is not a batch.
    assert summary.batches == _EXPECTED_BATCHES
    assert not (_batch_dir(layout.csv_root, _D7) / "execution.csv").exists()


def test_batches_before_the_backfill_start_are_skipped(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    own = _batch_dir(layout.csv_root, _D0)
    _write_forecast(own, _D0)
    _write_snapshot(own, _snapshot(_D0))
    _write_outcome_and_evaluation(
        _batch_dir(layout.csv_root, _window_end(_D0)),
        _D0,
        realized=(150.0, 150.3),
        evaluated_at=_window_end(_D0).astimezone(_UTC) + timedelta(hours=1),
    )

    summary, lines = _run(layout)

    assert backfill.BACKFILL_START_AS_OF == date(2026, 5, 8)
    assert summary.batches == _EXPECTED_BATCHES + 1
    assert summary.before_backfill_start == 1
    assert summary.written_decisions_and_evaluations == 2
    assert _counter_sum(summary) == summary.batches
    assert not (own / "execution.csv").exists()
    assert not (own / "execution_evaluation.csv").exists()
    assert any(
        line.startswith("[SKIP]") and _batch_id(_D0) in line and "before backfill start" in line
        for line in lines
    )


def test_snapshot_is_resolved_by_batch_id_not_by_date(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    # Another batch directory under the same date holds a snapshot; the batch's own does not.
    other = _batch_dir(layout.csv_root, _D6, "fb_other_batch_same_date")
    _write_snapshot(other, layout.snapshots["no_snapshot"])

    summary, lines = _run(layout)

    assert summary.missing_snapshot == 1
    assert summary.batches == _EXPECTED_BATCHES  # a dir holding only a snapshot is not a batch
    assert not (_batch_dir(layout.csv_root, _D6) / "execution.csv").exists()
    assert not (other / "execution.csv").exists()
    assert any(
        line.startswith("[SKIP]") and _batch_id(_D6) in line and "missing snapshot" in line
        for line in lines
    )


# ---------------------------------------------------------------------------
# Cross-batch join: the catch-up END-date copy is the same batch
# ---------------------------------------------------------------------------


def test_catchup_end_date_copy_is_not_a_second_batch(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    summary, _ = _run(layout)

    assert summary.batches == _EXPECTED_BATCHES
    start_dir = _batch_dir(layout.csv_root, _D3)
    end_dir = _batch_dir(layout.csv_root, _D4, _batch_id(_D3))
    assert is_complete_decision_file(str(start_dir / "execution.csv"))
    assert is_complete_evaluation_file(str(start_dir / "execution_evaluation.csv"))
    assert not (end_dir / "execution.csv").exists()
    assert not (end_dir / "execution_evaluation.csv").exists()
    evaluation_rows = _read_rows(start_dir / "execution_evaluation.csv")
    assert {row["outcome_id"] for row in evaluation_rows} == {layout.outcome_ids["catchup"]}
    assert {row["as_of_jst"] for row in evaluation_rows} == {_D3.isoformat()}


def test_forecast_only_in_the_catchup_end_date_dir_uses_the_canonical_dir(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    end_dir = _batch_dir(layout.csv_root, _window_end(_D9), _batch_id(_D9))
    _write_forecast(end_dir, _D9)
    outcome_id = _write_outcome_and_evaluation(
        end_dir,
        _D9,
        realized=(150.2, 150.0),
        evaluated_at=_window_end(_D9).astimezone(_UTC) + timedelta(hours=1),
    )
    canonical = _batch_dir(layout.csv_root, _D9)

    first, _ = _run(layout)

    assert first.batches == _EXPECTED_BATCHES + 1
    assert first.missing_snapshot == 2  # no_snapshot + this batch
    assert not canonical.exists()
    assert not (end_dir / "execution.csv").exists()
    assert not (end_dir / "execution_evaluation.csv").exists()

    canonical.mkdir(parents=True)
    _write_snapshot(canonical, _snapshot(_D9))
    second, _ = _run(layout)

    assert second.written_decisions_and_evaluations == 1
    assert second.missing_snapshot == 1
    assert is_complete_decision_file(str(canonical / "execution.csv"))
    rows = _read_rows(canonical / "execution_evaluation.csv")
    assert {row["outcome_id"] for row in rows} == {outcome_id}
    assert {row["as_of_jst"] for row in rows} == {_D9.isoformat()}
    assert not (end_dir / "execution.csv").exists()
    assert not (end_dir / "execution_evaluation.csv").exists()


# ---------------------------------------------------------------------------
# Repair path: evaluations only, existing decisions untouched
# ---------------------------------------------------------------------------


def test_evaluation_only_repair_keeps_existing_decisions(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    batch_dir = _batch_dir(layout.csv_root, _D4)
    decision_bytes = (batch_dir / "execution.csv").read_bytes()

    summary, _ = _run(layout)

    assert summary.written_evaluations_only == 1
    assert (batch_dir / "execution.csv").read_bytes() == decision_bytes
    rel = f"history/{_D4:%Y%m%d}/{_batch_id(_D4)}"
    assert f"{rel}/execution_evaluation.csv" in summary.files
    assert f"{rel}/execution.csv" not in summary.files

    evaluation_rows = _read_rows(batch_dir / "execution_evaluation.csv")
    assert len(evaluation_rows) == len(EXECUTION_BOOK_ORDER)
    # Copied from the archived decisions, not rebuilt as backfill_bar.
    assert {row["entry_status"] for row in evaluation_rows} == {"live_unavailable"}
    assert {row["pnl_live_bp"] for row in evaluation_rows} == {""}
    realized_open, realized_close = layout.realized["repair"]
    expected = evaluate_execution_decisions(
        layout.existing_decisions["repair"],
        outcome_id=layout.outcome_ids["repair"],
        window_start_jst=_D4,
        realized_open=realized_open,
        realized_close=realized_close,
        evaluated_at_utc=layout.evaluated_at["repair"],
    )
    assert load_execution_evaluations_csv(str(batch_dir / "execution_evaluation.csv")) == expected


def test_header_only_decision_file_is_replaced(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    batch_dir = _batch_dir(layout.csv_root, _D1)
    write_csv_rows(str(batch_dir / "execution.csv"), [], EXECUTION_FIELDNAMES)

    summary, _ = _run(layout)

    _assert_first_pass_counts(summary)
    assert is_complete_decision_file(str(batch_dir / "execution.csv"))
    assert {row["entry_status"] for row in _read_rows(batch_dir / "execution.csv")} == {
        "backfill_bar"
    }


# ---------------------------------------------------------------------------
# Unusable rows never stop the pass
# ---------------------------------------------------------------------------


def test_truncated_rows_are_skipped_and_the_run_completes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    layout = _build_checkout(tmp_path)
    # The "complete" window's evaluation.csv (next day's batch dir) loses the tail of its last
    # row; the "catchup" window's outcome.csv (END-date dir) loses its realized_close and later.
    _truncate_last_row(_batch_dir(layout.csv_root, _D2) / "evaluation.csv", 3)
    _truncate_last_row(_batch_dir(layout.csv_root, _D4, _batch_id(_D3)) / "outcome.csv", 5)

    backfill.main(["--fxdata-dir", str(layout.root)])

    out = capsys.readouterr().out
    assert "[OK] backfill_execution_history" in out
    assert "skipped (unusable outcome): 2" in out
    assert "written (decisions + evaluations): 0" in out
    assert "written (evaluations only): 1" in out
    warn_lines = [line for line in out.splitlines() if line.startswith("[WARN]")]
    assert any(_batch_id(_D1) in line and "unusable" in line for line in warn_lines)
    assert any(_batch_id(_D3) in line and "unusable" in line for line in warn_lines)
    for as_of in (_D1, _D3):
        assert not (_batch_dir(layout.csv_root, as_of) / "execution.csv").exists()
    assert is_complete_evaluation_file(
        str(_batch_dir(layout.csv_root, _D4) / "execution_evaluation.csv")
    )


def test_evaluations_pointing_at_two_outcomes_are_unusable_outcome(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    def fork(rows: list[dict[str, str]]) -> None:
        rows[0]["outcome_id"] = "oc_some_other_window"

    _edit_csv(_batch_dir(layout.csv_root, _D2) / "evaluation.csv", fork)

    summary, lines = _run(layout)

    assert summary.unusable_outcome == 1
    assert summary.missing_outcome == 1  # the pending window keeps its own reason
    assert summary.written_decisions_and_evaluations == 1
    assert _counter_sum(summary) == summary.batches
    assert any(
        line.startswith("[SKIP]") and _batch_id(_D1) in line and "unusable outcome" in line
        for line in lines
    )
    assert any(
        line.startswith(f"[WARN] {_D1:%Y%m%d} {_batch_id(_D1)}:") and "2 outcomes" in line
        for line in lines
    )
    assert not (_batch_dir(layout.csv_root, _D1) / "execution.csv").exists()


def test_outcome_window_mismatch_is_counted_as_unusable_inputs(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    def shift_window(rows: list[dict[str, str]]) -> None:
        rows[0]["window_start_jst"] = _D2.isoformat()

    _edit_csv(_batch_dir(layout.csv_root, _D2) / "outcome.csv", shift_window)

    summary, lines = _run(layout)

    assert summary.unusable_inputs == 1
    assert summary.written_decisions_and_evaluations == 1  # catchup only
    assert summary.written_evaluations_only == 1
    assert _counter_sum(summary) == summary.batches
    assert any(
        line.startswith(f"[WARN] {_D1:%Y%m%d} {_batch_id(_D1)}: unusable inputs (")
        for line in lines
    )
    assert any(
        line.startswith("[SKIP]") and _batch_id(_D1) in line and "unusable inputs" in line
        for line in lines
    )
    batch_dir = _batch_dir(layout.csv_root, _D1)
    assert not (batch_dir / "execution.csv").exists()
    assert not (batch_dir / "execution_evaluation.csv").exists()


# ---------------------------------------------------------------------------
# Idempotence, dry run, latest/
# ---------------------------------------------------------------------------


def test_rerun_is_byte_identical_and_skips_complete_batches(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)

    first, _ = _run(layout)
    after_first = _all_files(layout.csv_root)
    second, lines = _run(layout)

    _assert_first_pass_counts(first)
    assert _all_files(layout.csv_root) == after_first
    assert second.batches == _EXPECTED_BATCHES
    assert second.already_complete == 3  # complete, catchup, repair
    assert second.written_decisions_and_evaluations == 0
    assert second.written_evaluations_only == 0
    assert second.files == ()
    assert (second.missing_forecast, second.partial_forecast) == (1, 1)
    assert (second.missing_outcome, second.missing_snapshot) == (1, 1)
    assert _counter_sum(second) == second.batches
    assert not any("already complete" in line for line in lines)


def test_dry_run_writes_nothing_and_reports_the_same_counts(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    before = _all_files(layout.csv_root)

    dry, dry_lines = _run(layout, dry_run=True)

    assert dry.dry_run is True
    assert _all_files(layout.csv_root) == before
    assert not (layout.csv_root / "latest").exists()
    assert not (layout.csv_root / "execution").exists()
    _assert_first_pass_counts(dry)
    assert len(dry.files) == 5
    assert sum(line.startswith("[SKIP]") for line in dry_lines) == 4

    real, _ = _run(layout)

    assert real.files == dry.files
    for attr in ("batches", *_COUNTERS):
        assert getattr(real, attr) == getattr(dry, attr), attr


@pytest.mark.parametrize("latest_present", [True, False])
def test_latest_execution_csv_is_left_as_found(tmp_path: Path, latest_present: bool) -> None:
    layout = _build_checkout(tmp_path)
    latest_dir = layout.csv_root / "latest"
    latest_file = latest_dir / "execution.csv"
    if latest_present:
        latest_dir.mkdir()
        latest_file.write_bytes(b"the live batch the daily protocol recorded last\n")
    before = latest_file.read_bytes() if latest_present else None

    summary, _ = _run(layout)

    assert summary.written_decisions_and_evaluations == 2
    if latest_present:
        assert latest_file.read_bytes() == before
    else:
        assert not latest_dir.exists()


@pytest.mark.parametrize("latest_present", [True, False])
def test_latest_execution_csv_is_restored_when_publish_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, latest_present: bool
) -> None:
    layout = _build_checkout(tmp_path)
    latest_dir = layout.csv_root / "latest"
    latest_file = latest_dir / "execution.csv"
    original = b"the live batch the daily protocol recorded last\n"
    if latest_present:
        latest_dir.mkdir()
        latest_file.write_bytes(original)
    real_publish = backfill.publish_execution_csvs
    observed: dict[str, bytes] = {}

    def publish_then_fail(*args: object, **kwargs: object) -> None:
        real_publish(*args, **kwargs)  # type: ignore[arg-type]
        observed["latest_after_publish"] = latest_file.read_bytes()
        raise OSError("simulated failure after the publish")

    monkeypatch.setattr(backfill, "publish_execution_csvs", publish_then_fail)

    with pytest.raises(OSError, match="simulated failure"):
        _run(layout)

    # The real publish did move latest/ onto the backfilled batch before failing ...
    assert observed["latest_after_publish"] != original
    assert observed["latest_after_publish"].startswith(b"execution_version,book_id,")
    # ... and the guard put it back (or removed what did not exist before).
    if latest_present:
        assert latest_file.read_bytes() == original
    else:
        assert not latest_dir.exists()


# ---------------------------------------------------------------------------
# Archive contradictions are counted, left untouched, and never stop the pass
# ---------------------------------------------------------------------------


def _batch_files(csv_root: Path, as_of: datetime) -> dict[str, bytes]:
    prefix = f"history/{as_of:%Y%m%d}/{_batch_id(as_of)}/"
    return {path: data for path, data in _all_files(csv_root).items() if path.startswith(prefix)}


def test_complete_evaluation_without_complete_decisions_is_counted_and_skipped(
    tmp_path: Path,
) -> None:
    layout = _build_checkout(tmp_path)
    batch_dir = _batch_dir(layout.csv_root, _D1)
    decisions = _decisions(
        layout.snapshots["complete"],
        _D1,
        entry_status="backfill_bar",
        decided_at_utc=_D1.astimezone(_UTC),
    )
    realized_open, realized_close = layout.realized["complete"]
    evaluations = evaluate_execution_decisions(
        decisions,
        outcome_id=layout.outcome_ids["complete"],
        window_start_jst=_D1,
        realized_open=realized_open,
        realized_close=realized_close,
        evaluated_at_utc=layout.evaluated_at["complete"],
    )
    write_csv_rows(
        str(batch_dir / "execution_evaluation.csv"),
        evaluations_to_rows(evaluations),
        EXECUTION_EVALUATION_FIELDNAMES,
    )
    write_csv_rows(str(batch_dir / "execution.csv"), [], EXECUTION_FIELDNAMES)
    before = _batch_files(layout.csv_root, _D1)

    summary, lines = _run(layout)

    assert summary.contradictory_archive == 1
    assert _batch_files(layout.csv_root, _D1) == before
    assert any(
        line.startswith(f"[WARN] {_D1:%Y%m%d} {_batch_id(_D1)}:") and "contradicts itself" in line
        for line in lines
    )
    assert any(
        line.startswith("[SKIP]") and _batch_id(_D1) in line and "contradictory archive" in line
        for line in lines
    )
    # The rest of the archive is still processed.
    assert summary.written_decisions_and_evaluations == 1  # catchup
    assert summary.written_evaluations_only == 1  # repair
    assert _counter_sum(summary) == summary.batches


def test_decision_file_belonging_to_another_batch_is_counted_and_skipped(tmp_path: Path) -> None:
    layout = _build_checkout(tmp_path)
    foreign = _batch_dir(layout.csv_root, _D1) / "execution.csv"
    foreign_bytes = (_batch_dir(layout.csv_root, _D4) / "execution.csv").read_bytes()
    foreign.write_bytes(foreign_bytes)

    summary, lines = _run(layout)

    assert summary.contradictory_archive == 1
    assert foreign.read_bytes() == foreign_bytes
    assert not (_batch_dir(layout.csv_root, _D1) / "execution_evaluation.csv").exists()
    assert any(
        line.startswith(f"[WARN] {_D1:%Y%m%d} {_batch_id(_D1)}:")
        and "holds decisions for" in line
        and _batch_id(_D4) in line
        for line in lines
    )
    assert summary.written_decisions_and_evaluations == 1  # catchup
    assert summary.written_evaluations_only == 1  # repair
    assert _counter_sum(summary) == summary.batches


def test_contradiction_on_a_later_unit_does_not_stop_the_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    layout = _build_checkout(tmp_path)
    # Processing order is (date, batch id): complete (05-11), partial (05-12), catchup (05-13),
    # repair (05-14), ...  The foreign decision file sits on the third unit.
    foreign = _batch_dir(layout.csv_root, _D3) / "execution.csv"
    foreign_bytes = (_batch_dir(layout.csv_root, _D4) / "execution.csv").read_bytes()
    foreign.write_bytes(foreign_bytes)

    with pytest.raises(SystemExit) as excinfo:
        backfill.main(["--fxdata-dir", str(layout.root)])

    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    # The earlier batch was written ...
    assert is_complete_decision_file(str(_batch_dir(layout.csv_root, _D1) / "execution.csv"))
    assert is_complete_evaluation_file(
        str(_batch_dir(layout.csv_root, _D1) / "execution_evaluation.csv")
    )
    # ... the contradictory one was counted and left untouched ...
    assert foreign.read_bytes() == foreign_bytes
    assert not (_batch_dir(layout.csv_root, _D3) / "execution_evaluation.csv").exists()
    # ... and the later batches were still processed.
    assert is_complete_evaluation_file(
        str(_batch_dir(layout.csv_root, _D4) / "execution_evaluation.csv")
    )
    assert "[OK] backfill_execution_history" in out
    assert "written (decisions + evaluations): 1" in out
    assert "written (evaluations only): 1" in out
    assert "skipped (contradictory archive): 1" in out
    assert "1 batch(es) hold a self-contradicting archive" in out
    assert "Exit status 1." in out
    assert "push it manually" in out
    assert out.index("[WARN]") < out.index("[OK] backfill_execution_history")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pick_dir",
    [
        pytest.param(lambda layout: layout.root, id="checkout-root"),
        pytest.param(lambda layout: layout.csv_root, id="csv-root"),
    ],
)
def test_main_accepts_checkout_root_and_csv_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], pick_dir: Callable[[_Layout], Path]
) -> None:
    layout = _build_checkout(tmp_path)

    backfill.main(["--fxdata-dir", str(pick_dir(layout))])

    out = capsys.readouterr().out
    assert f"[OK] backfill_execution_history: csv root = {layout.csv_root}" in out
    assert f"batches scanned: {_EXPECTED_BATCHES}" in out
    assert "written (decisions + evaluations): 2" in out
    assert "written (evaluations only): 1" in out
    assert "skipped (partial forecast): 1" in out
    assert "skipped (contradictory archive): 0" in out
    assert "Exit status 1." not in out
    assert "push it manually" in out
    assert is_complete_decision_file(str(_batch_dir(layout.csv_root, _D1) / "execution.csv"))


def test_main_dry_run_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    layout = _build_checkout(tmp_path)
    before = _all_files(layout.csv_root)

    backfill.main(["--fxdata-dir", str(layout.root), "--dry-run"])

    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "would write (decisions + evaluations): 2" in out
    assert "nothing was written (--dry-run)." in out
    assert _all_files(layout.csv_root) == before


def test_main_rejects_a_directory_without_history(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        backfill.main(["--fxdata-dir", str(tmp_path)])

    assert excinfo.value.code == 1
    assert "[ERROR] no history/ archive found" in capsys.readouterr().err


def test_resolve_csv_output_dir_prefers_the_csv_subdirectory(tmp_path: Path) -> None:
    (tmp_path / "csv" / "history").mkdir(parents=True)
    (tmp_path / "history").mkdir()

    assert backfill.resolve_csv_output_dir(str(tmp_path)) == str(tmp_path / "csv")
    assert backfill.resolve_csv_output_dir(str(tmp_path / "csv")) == str(tmp_path / "csv")


# ---------------------------------------------------------------------------
# Contract pins
# ---------------------------------------------------------------------------


def test_required_strategy_kinds_match_the_builder() -> None:
    assert backfill._REQUIRED_STRATEGY_KINDS == execution_module._REQUIRED_STRATEGY_KINDS


def test_backfill_entry_status_is_the_reserved_literal() -> None:
    assert backfill.BACKFILL_ENTRY_STATUS == "backfill_bar"


def test_duplicate_strategy_rows_are_a_partial_forecast(tmp_path: Path) -> None:
    """Seven rows with a duplicated kind are not the daily set even when every required kind
    is present: the absent baseline makes it partial_forecast, nothing is backfilled."""
    layout = _build_checkout(tmp_path)
    required = set(backfill._REQUIRED_STRATEGY_KINDS)

    def duplicate_a_required_kind(rows: list[dict[str, str]]) -> None:
        spare = next(r for r in rows if StrategyKind(r["strategy_kind"]) not in required)
        spare["strategy_kind"] = StrategyKind.ugh_v2_alpha.value

    _edit_csv(_batch_dir(layout.csv_root, _D1) / "forecast.csv", duplicate_a_required_kind)

    summary, _lines = _run(layout)

    assert summary.partial_forecast == 2  # the built-in partial batch plus this one
    assert summary.written_decisions_and_evaluations == 1  # the catch-up window only
    assert not (_batch_dir(layout.csv_root, _D1) / "execution.csv").exists()
    assert _counter_sum(summary) == summary.batches


@pytest.mark.parametrize(
    ("as_of", "filename"),
    [(_D2, "evaluation.csv"), (_D2, "outcome.csv"), (_D1, "forecast.csv")],
    ids=["evaluation", "outcome", "forecast"],
)
def test_unreadable_archive_csv_is_skipped_with_a_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], as_of: datetime, filename: str
) -> None:
    """An undecodable archive file costs only the batches that depend on it and the pass still
    prints its summary (the "complete" window's evaluation and outcome live in the next day's
    directory, its forecast in its own)."""
    layout = _build_checkout(tmp_path)
    (_batch_dir(layout.csv_root, as_of) / filename).write_bytes(b"\xff\xfe\x00\x80not,utf8\n")

    backfill.main(["--fxdata-dir", str(layout.root)])

    out = capsys.readouterr().out
    assert "[OK] backfill_execution_history" in out
    assert "written (decisions + evaluations): 1" in out  # the catch-up window only
    warn_lines = [line for line in out.splitlines() if line.startswith("[WARN]")]
    assert any(filename in line and "unreadable" in line for line in warn_lines)
    assert not (_batch_dir(layout.csv_root, _D1) / "execution.csv").exists()


def test_forecast_rows_of_another_window_are_a_partial_forecast(tmp_path: Path) -> None:
    """Seven distinct kinds, but one row for the next window: not this batch's forecast, so the
    batch is partial_forecast rather than a hybrid of two windows in the bar series."""
    layout = _build_checkout(tmp_path)
    required = set(backfill._REQUIRED_STRATEGY_KINDS)

    def move_a_spare_row_to_the_next_window(rows: list[dict[str, str]]) -> None:
        spare = next(r for r in rows if StrategyKind(r["strategy_kind"]) not in required)
        spare["as_of_jst"] = _D2.isoformat()
        spare["window_end_jst"] = _window_end(_D2).isoformat()

    _edit_csv(
        _batch_dir(layout.csv_root, _D1) / "forecast.csv", move_a_spare_row_to_the_next_window
    )

    summary, _lines = _run(layout)

    assert summary.partial_forecast == 2  # the built-in partial batch plus this one
    assert summary.written_decisions_and_evaluations == 1  # the catch-up window only
    assert not (_batch_dir(layout.csv_root, _D1) / "execution.csv").exists()
    assert _counter_sum(summary) == summary.batches
