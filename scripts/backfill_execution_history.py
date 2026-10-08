#!/usr/bin/env python3
"""Backfill ``backfill_bar`` execution decisions and evaluations from the history archive.

FX Execution Layer v1 §10 (``docs/specs/fx_execution_layer_v1.md``, brief
FX-EXEC-REPORTING).  Deterministic, no network, no clock, read-only against the
forecast archive: every persisted forecast batch whose window has been
evaluated gets the six book decisions of ``execution.build_execution_decisions``
re-derived from its archived inputs and recorded with
``entry_status = "backfill_bar"`` (no live spot, so ``pnl_live_bp`` /
``cost_live_bp`` stay empty: the rows enter the bar series only and never the
live acceptance gate), plus the six evaluations against the window's outcome.

Inputs are joined across batch directories exactly like
``labeled_observations.collect_evaluated_forecast_rows``: evaluation and
outcome rows live in the *next* day's batch directory (or, for a window
recovered by outcome catch-up, in the window's end-date directory), so global
``forecast_id -> evaluation`` and ``outcome_id -> outcome`` indexes are built
first and every ``forecast_batch_id`` is resolved against them.  A batch's
canonical directory is ``history/{as_of:%Y%m%d}/{forecast_batch_id}/`` (the
``as_of_jst`` of its own forecast rows, never the directory a copy of
``forecast.csv`` happens to sit in), and its ``input_snapshot.json`` is
resolved there by batch id, never by date alone.

Per batch (spec §10):

- ``execution.csv`` and ``execution_evaluation.csv`` both complete: skipped.
- ``execution.csv`` complete but the evaluation file missing or incomplete (an
  interrupted earlier run, or a daily run whose evaluation step failed): the
  archived six decisions are loaded and only the six evaluations are written.
  This repair path needs the window's outcome only; a partial ``forecast.csv``
  or a missing snapshot does not block it.
- otherwise the batch needs (a) its complete seven-row ``forecast.csv`` (the
  four UGH v2 variants and the technical baseline are what the builder reads),
  (b) the outcome its evaluation rows point at and (c) its own
  ``input_snapshot.json``; with all three, six decisions and six evaluations
  are written.  A batch missing any of them is skipped and counted by reason.

Timestamps come from the archive so reruns are byte-identical:
``decided_at_utc`` is the batch's ``as_of_jst`` converted to UTC
(``forecast.csv`` carries no ``locked_at_utc``) and ``evaluated_at_utc`` is the
latest ``evaluated_at_utc`` of the batch's ``evaluation.csv`` rows.

Files go through the real exporters and ``publish_execution_csvs`` (atomic
copies; a complete ``execution.csv`` is never overwritten).  Staging CSVs are
written to a temporary directory and ``latest/execution.csv`` is left exactly
as found (it mirrors the newest live batch, which a closed backfill window
never is), so the checkout only gains ``history/`` archive files.  Nothing is
committed or pushed: review the ``fx-daily-data`` checkout and push by hand.

Usage
-----
    python scripts/backfill_execution_history.py --fxdata-dir /path/to/fx-daily-data
    python scripts/backfill_execution_history.py --fxdata-dir /path/to/fx-daily-data --dry-run

``--fxdata-dir`` is the checkout root (its CSV root is ``<dir>/csv``).  The CSV
root itself (``<dir>/history`` present, the form ``analyze_estar_lag.py``
takes) is accepted too.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import math
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.data_models import FxProtocolMarketSnapshot
from ugh_quantamental.fx_protocol.execution import (
    build_execution_decisions,
    evaluate_execution_decisions,
)
from ugh_quantamental.fx_protocol.execution_exports import (
    export_execution_csv,
    export_execution_evaluation_csv,
    is_complete_decision_file,
    is_complete_evaluation_file,
    load_execution_decisions_csv,
    publish_execution_csvs,
)
from ugh_quantamental.fx_protocol.execution_models import EntryStatus, ExecutionDecision
from ugh_quantamental.fx_protocol.models import (
    EXPECTED_DAILY_BATCH_SIZE,
    CurrencyPair,
    ForecastDirection,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.observability import load_input_snapshot
from ugh_quantamental.fx_protocol.request_builders import build_baseline_context

_JST = ZoneInfo("Asia/Tokyo")

#: Entry status of every backfilled decision row (spec §5.1 / §10).
BACKFILL_ENTRY_STATUS: EntryStatus = "backfill_bar"

#: Directions ``build_execution_decisions`` consumes (``execution._REQUIRED_STRATEGY_KINDS``):
#: the four UGH v2 variants and the technical baseline.  The other two baselines are
#: part of a complete daily batch but are not read by any book.
_REQUIRED_STRATEGY_KINDS: tuple[StrategyKind, ...] = (
    StrategyKind.ugh_v2_alpha,
    StrategyKind.ugh_v2_beta,
    StrategyKind.ugh_v2_gamma,
    StrategyKind.ugh_v2_delta,
    StrategyKind.baseline_simple_technical,
)

# Per-batch outcomes of one pass (the keys of ``BackfillSummary``'s counters).
WRITTEN_DECISIONS_AND_EVALUATIONS = "written_decisions_and_evaluations"
WRITTEN_EVALUATIONS_ONLY = "written_evaluations_only"
ALREADY_COMPLETE = "already_complete"
MISSING_FORECAST = "missing_forecast"
PARTIAL_FORECAST = "partial_forecast"
MISSING_OUTCOME = "missing_outcome"
MISSING_SNAPSHOT = "missing_snapshot"

_SKIP_LABELS: dict[str, str] = {
    MISSING_FORECAST: "missing forecast (no forecast.csv rows for this batch anywhere in history/)",
    PARTIAL_FORECAST: "partial forecast (not the complete 7-row daily batch)",
    MISSING_OUTCOME: "missing outcome (no evaluated window for this batch)",
    MISSING_SNAPSHOT: "missing snapshot (no readable input_snapshot.json in the batch directory)",
}

Log = Callable[[str], None]


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BackfillSummary:
    """What one pass did (or, with ``dry_run``, would have done) to each forecast batch.

    ``batches`` is the number of batches examined; the seven counters below
    partition it.  ``files`` lists the ``history/...`` paths (relative to
    ``csv_output_dir``) written by the pass, or that a dry run would write.
    """

    csv_output_dir: str
    dry_run: bool
    batches: int
    written_decisions_and_evaluations: int
    written_evaluations_only: int
    already_complete: int
    missing_forecast: int
    partial_forecast: int
    missing_outcome: int
    missing_snapshot: int
    files: tuple[str, ...] = field(default=())


# ---------------------------------------------------------------------------
# Archive scanning (collector conventions of ``labeled_observations``)
# ---------------------------------------------------------------------------


@dataclass
class _ForecastBatch:
    """One ``forecast_batch_id`` as its ``forecast.csv`` rows describe it.

    ``rows`` maps ``forecast_id`` to the first copy of the row seen in sorted
    directory order; a batch republished into a catch-up end-date directory
    therefore contributes each forecast exactly once.
    """

    forecast_batch_id: str
    as_of_jst: datetime
    window_end_jst: datetime
    rows: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class _Indexes:
    """Global cross-batch indexes: ``forecast_id -> evaluation`` and ``outcome_id -> outcome``."""

    evaluations_by_forecast_id: dict[str, dict[str, str]]
    outcomes_by_outcome_id: dict[str, dict[str, str]]


@dataclass(frozen=True)
class _Outcome:
    """The evaluated window of one batch, as ``evaluate_execution_decisions`` needs it."""

    outcome_id: str
    pair: str
    window_start_jst: datetime
    realized_open: float
    realized_close: float
    evaluated_at_utc: datetime


@dataclass(frozen=True)
class _Unit:
    """One batch to examine: its canonical ``history/{date_str}/{forecast_batch_id}/`` directory.

    ``forecast`` is ``None`` for a directory that holds an ``execution.csv``
    but whose batch id has no ``forecast.csv`` rows anywhere in the archive.
    """

    forecast_batch_id: str
    date_str: str
    forecast: _ForecastBatch | None


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    """Read every row of a history CSV (same reader as the collectors)."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _batch_dirs(history_dir: str) -> Iterator[tuple[str, str, str]]:
    """Yield ``(date_dir, batch_dir, batch_path)`` for every batch directory, sorted."""
    for date_dir in sorted(os.listdir(history_dir)):
        date_path = os.path.join(history_dir, date_dir)
        if not os.path.isdir(date_path):
            continue
        for batch_dir in sorted(os.listdir(date_path)):
            batch_path = os.path.join(date_path, batch_dir)
            if os.path.isdir(batch_path):
                yield date_dir, batch_dir, batch_path


def _parse_jst(value: str) -> datetime | None:
    """Parse an ISO-8601 cell as a JST-aware datetime (naive cells are JST); ``None`` if invalid."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.astimezone(_JST) if parsed.tzinfo is not None else parsed.replace(tzinfo=_JST)


def _parse_utc(value: str) -> datetime | None:
    """Parse an ISO-8601 cell as a UTC-aware datetime (naive cells are UTC); ``None`` if invalid."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc)
    return parsed.replace(tzinfo=timezone.utc)


def _parse_price(value: str) -> float | None:
    """Parse a price cell; ``None`` unless finite and positive."""
    try:
        price = float(value)
    except ValueError:
        return None
    return price if math.isfinite(price) and price > 0 else None


def build_indexes(history_dir: str) -> _Indexes:
    """Pass 1: index every ``evaluation.csv`` row by ``forecast_id`` and every ``outcome.csv``
    row by ``outcome_id`` across all batch directories (later directories win, as in the
    collectors).
    """
    evaluations: dict[str, dict[str, str]] = {}
    outcomes: dict[str, dict[str, str]] = {}
    for _date_dir, _batch_dir, batch_path in _batch_dirs(history_dir):
        evaluation_csv = os.path.join(batch_path, "evaluation.csv")
        if os.path.isfile(evaluation_csv):
            for row in _read_csv_rows(evaluation_csv):
                forecast_id = row.get("forecast_id", "")
                if forecast_id:
                    evaluations[forecast_id] = row
        outcome_csv = os.path.join(batch_path, "outcome.csv")
        if os.path.isfile(outcome_csv):
            for row in _read_csv_rows(outcome_csv):
                outcome_id = row.get("outcome_id", "")
                if outcome_id:
                    outcomes[outcome_id] = row
    return _Indexes(evaluations_by_forecast_id=evaluations, outcomes_by_outcome_id=outcomes)


def collect_forecast_batches(history_dir: str) -> dict[str, _ForecastBatch]:
    """Pass 2: group every ``forecast.csv`` row by ``forecast_batch_id``, deduplicated by
    ``forecast_id`` so a catch-up copy of ``forecast.csv`` never becomes a second batch.

    A batch's ``as_of_jst`` / ``window_end_jst`` come from its own rows; rows
    whose timestamps do not parse cannot be placed in the archive and are ignored.
    """
    batches: dict[str, _ForecastBatch] = {}
    seen_forecast_ids: set[str] = set()
    for _date_dir, _batch_dir, batch_path in _batch_dirs(history_dir):
        forecast_csv = os.path.join(batch_path, "forecast.csv")
        if not os.path.isfile(forecast_csv):
            continue
        for row in _read_csv_rows(forecast_csv):
            forecast_id = row.get("forecast_id", "")
            batch_id = row.get("forecast_batch_id", "")
            if not forecast_id or not batch_id or forecast_id in seen_forecast_ids:
                continue
            batch = batches.get(batch_id)
            if batch is None:
                as_of_jst = _parse_jst(row.get("as_of_jst", ""))
                window_end_jst = _parse_jst(row.get("window_end_jst", ""))
                if as_of_jst is None or window_end_jst is None:
                    continue
                batch = _ForecastBatch(batch_id, as_of_jst, window_end_jst)
                batches[batch_id] = batch
            seen_forecast_ids.add(forecast_id)
            batch.rows[forecast_id] = row
    return batches


def collect_units(history_dir: str, batches: dict[str, _ForecastBatch]) -> list[_Unit]:
    """Every batch to examine, ordered by ``(date, forecast_batch_id)``.

    Units come from the forecast batches (canonical directory derived from
    their ``as_of_jst``) plus any ``history/*/*/execution.csv`` directory whose
    batch id has no forecast rows, so a decision file without a forecast is
    reported rather than silently ignored.
    """
    units: dict[str, _Unit] = {
        batch_id: _Unit(batch_id, batch.as_of_jst.strftime("%Y%m%d"), batch)
        for batch_id, batch in batches.items()
    }
    for date_dir, batch_dir, batch_path in _batch_dirs(history_dir):
        if batch_dir in units:
            continue
        if os.path.isfile(os.path.join(batch_path, "execution.csv")):
            units[batch_dir] = _Unit(batch_dir, date_dir, None)
    return sorted(units.values(), key=lambda unit: (unit.date_str, unit.forecast_batch_id))


# ---------------------------------------------------------------------------
# Per-batch input resolution
# ---------------------------------------------------------------------------


def _forecast_directions(batch: _ForecastBatch) -> dict[StrategyKind, ForecastDirection] | None:
    """The batch's ``strategy_kind -> forecast_direction`` map, or ``None`` when the batch is
    not the complete daily set (``EXPECTED_DAILY_BATCH_SIZE`` rows holding every required kind).
    """
    if len(batch.rows) != EXPECTED_DAILY_BATCH_SIZE:
        return None
    directions: dict[StrategyKind, ForecastDirection] = {}
    for row in batch.rows.values():
        try:
            kind = StrategyKind(row.get("strategy_kind", ""))
            direction = ForecastDirection(row.get("forecast_direction", ""))
        except ValueError:
            return None
        directions[kind] = direction
    if any(kind not in directions for kind in _REQUIRED_STRATEGY_KINDS):
        return None
    return directions


def _resolve_outcome(batch: _ForecastBatch, indexes: _Indexes, log: Log) -> _Outcome | None:
    """Resolve (b): the outcome the batch's evaluation rows point at, via the global indexes.

    ``evaluated_at_utc`` is the latest value over the batch's evaluation rows.
    Returns ``None`` when no forecast of the batch has been evaluated, when the
    evaluations disagree on the outcome, or when the rows are unusable; the
    latter two are logged because they are archive anomalies, not pending windows.
    """
    evaluations = [
        indexes.evaluations_by_forecast_id[forecast_id]
        for forecast_id in batch.rows
        if forecast_id in indexes.evaluations_by_forecast_id
    ]
    if not evaluations:
        return None
    outcome_ids = sorted({ev.get("outcome_id", "") for ev in evaluations} - {""})
    if len(outcome_ids) != 1:
        log(
            f"[WARN] batch {batch.forecast_batch_id}: its evaluation rows point at "
            f"{len(outcome_ids)} outcomes {outcome_ids}; treated as a missing outcome"
        )
        return None
    outcome_id = outcome_ids[0]
    row = indexes.outcomes_by_outcome_id.get(outcome_id)
    if row is None:
        return None
    window_start_jst = _parse_jst(row.get("window_start_jst", ""))
    realized_open = _parse_price(row.get("realized_open", ""))
    realized_close = _parse_price(row.get("realized_close", ""))
    evaluated_at = [_parse_utc(ev.get("evaluated_at_utc", "")) for ev in evaluations]
    if (
        window_start_jst is None
        or realized_open is None
        or realized_close is None
        or any(value is None for value in evaluated_at)
    ):
        log(
            f"[WARN] batch {batch.forecast_batch_id}: outcome {outcome_id} or its evaluation "
            "rows carry unusable window / price / timestamp cells; treated as a missing outcome"
        )
        return None
    return _Outcome(
        outcome_id=outcome_id,
        pair=row.get("pair", "") or CurrencyPair.USDJPY.value,
        window_start_jst=window_start_jst,
        realized_open=realized_open,
        realized_close=realized_close,
        evaluated_at_utc=max(value for value in evaluated_at if value is not None),
    )


def _load_snapshot(path: str, log: Log) -> FxProtocolMarketSnapshot | None:
    """Resolve (c): the batch's own archived snapshot; a missing or unreadable file is ``None``."""
    if not os.path.isfile(path):
        return None
    try:
        return load_input_snapshot(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        log(f"[WARN] {path}: unreadable input_snapshot.json ({exc}); treated as missing")
        return None


def _check_decisions_belong(
    decisions: tuple[ExecutionDecision, ...], unit: _Unit, history_rel: str
) -> None:
    """Refuse a complete ``execution.csv`` whose rows contradict its directory.

    The same guard as automation Step 4c, but fatal: an archive that
    contradicts itself needs a human before anything is written next to it.
    """
    first = decisions[0]
    actual = (first.as_of_jst.strftime("%Y%m%d"), first.forecast_batch_id)
    if actual != (unit.date_str, unit.forecast_batch_id):
        raise RuntimeError(
            f"{history_rel}/execution.csv holds decisions for {actual[0]}/{actual[1]}; "
            "the archive contradicts itself and is left untouched (fix it by hand, then rerun)"
        )


# ---------------------------------------------------------------------------
# Publication (archive files only)
# ---------------------------------------------------------------------------


def _read_bytes(path: str) -> bytes | None:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def _replace_bytes(path: str, data: bytes) -> None:
    """Atomically put *data* at *path* (temp file in the same directory + ``os.replace``)."""
    fd, tmp = tempfile.mkstemp(
        prefix=f".{os.path.basename(path)}.", suffix=".tmp", dir=os.path.dirname(path)
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


@contextlib.contextmanager
def _latest_execution_preserved(csv_output_dir: str) -> Iterator[None]:
    """Keep ``latest/execution.csv`` exactly as it was across a decision publish.

    ``publish_execution_csvs`` mirrors every decision file it publishes into
    ``latest/execution.csv``, the daily protocol's "batch the run worked on"
    (``fx_daily_csv_exports_v1.md`` § execution/ policy).  A backfill records
    closed windows that are older than the batch ``latest/`` already points at,
    so the mirror must not move: the bytes present before the publish are put
    back afterwards, and a file (and ``latest/`` directory) that did not exist
    before is removed again.
    """
    latest_dir = os.path.join(csv_output_dir, "latest")
    latest_path = os.path.join(latest_dir, "execution.csv")
    had_latest_dir = os.path.isdir(latest_dir)
    before = _read_bytes(latest_path)
    try:
        yield
    finally:
        if before is None:
            with contextlib.suppress(FileNotFoundError):
                os.remove(latest_path)
            if not had_latest_dir:
                with contextlib.suppress(OSError):
                    os.rmdir(latest_dir)
        elif _read_bytes(latest_path) != before:
            _replace_bytes(latest_path, before)


# ---------------------------------------------------------------------------
# Per-batch processing
# ---------------------------------------------------------------------------


def _process_unit(
    unit: _Unit,
    indexes: _Indexes,
    csv_output_dir: str,
    staging_dir: str,
    *,
    dry_run: bool,
    log: Log,
) -> tuple[str, tuple[str, ...]]:
    """Examine one batch and, unless *dry_run*, write what it lacks.

    Returns the batch's outcome key (one of the ``BackfillSummary`` counters)
    and the archive paths written, relative to *csv_output_dir* (for a dry run,
    the paths that would be written).  Decisions and evaluations are built in
    memory in both modes, so a dry run reports exactly what a real run writes.
    """
    history_rel = f"history/{unit.date_str}/{unit.forecast_batch_id}"
    history_dir = os.path.join(csv_output_dir, "history", unit.date_str, unit.forecast_batch_id)
    decision_file = os.path.join(history_dir, "execution.csv")
    evaluation_file = os.path.join(history_dir, "execution_evaluation.csv")
    decisions_complete = is_complete_decision_file(decision_file)
    evaluations_complete = is_complete_evaluation_file(evaluation_file)

    if decisions_complete and evaluations_complete:
        return ALREADY_COMPLETE, ()
    if evaluations_complete:
        raise RuntimeError(
            f"{history_rel}: execution_evaluation.csv is complete but execution.csv is not; "
            "the archive contradicts itself and is left untouched (fix it by hand, then rerun)"
        )
    if unit.forecast is None:
        # Without forecast rows there is nothing to join the outcome through,
        # whichever path the batch would take.
        return MISSING_FORECAST, ()

    if decisions_complete:
        # Repair path: existing decisions, evaluations only.  Needs (b) alone.
        outcome = _resolve_outcome(unit.forecast, indexes, log)
        if outcome is None:
            return MISSING_OUTCOME, ()
        decisions = load_execution_decisions_csv(decision_file)
        _check_decisions_belong(decisions, unit, history_rel)
        rebuild = False
    else:
        # Full path: (a) complete forecast, (b) outcome, (c) the batch's own snapshot.
        directions = _forecast_directions(unit.forecast)
        if directions is None:
            return PARTIAL_FORECAST, ()
        outcome = _resolve_outcome(unit.forecast, indexes, log)
        if outcome is None:
            return MISSING_OUTCOME, ()
        snapshot = _load_snapshot(os.path.join(history_dir, "input_snapshot.json"), log)
        if snapshot is None:
            return MISSING_SNAPSHOT, ()
        decisions = build_execution_decisions(
            forecast_directions=directions,
            baseline_context=build_baseline_context(snapshot),
            completed_closes=tuple(w.close_price for w in snapshot.completed_windows),
            as_of_jst=unit.forecast.as_of_jst,
            window_end_jst=unit.forecast.window_end_jst,
            forecast_batch_id=unit.forecast_batch_id,
            entry_status=BACKFILL_ENTRY_STATUS,
            live_entry=None,
            decided_at_utc=unit.forecast.as_of_jst.astimezone(timezone.utc),
        )
        rebuild = True

    evaluations = evaluate_execution_decisions(
        decisions,
        outcome_id=outcome.outcome_id,
        window_start_jst=outcome.window_start_jst,
        realized_open=outcome.realized_open,
        realized_close=outcome.realized_close,
        evaluated_at_utc=outcome.evaluated_at_utc,
    )
    targets: tuple[str, ...] = (f"{history_rel}/execution_evaluation.csv",)
    if rebuild:
        targets = (f"{history_rel}/execution.csv", *targets)

    if not dry_run:
        as_of_jst = decisions[0].as_of_jst
        decision_path = (
            export_execution_csv(decisions, as_of_jst, outcome.pair, staging_dir)
            if rebuild
            else None
        )
        evaluation_path = export_execution_evaluation_csv(
            evaluations, as_of_jst, outcome.pair, staging_dir
        )
        with _latest_execution_preserved(csv_output_dir):
            publish_execution_csvs(
                csv_output_dir,
                unit.date_str,
                unit.forecast_batch_id,
                decision_path,
                evaluation_path,
            )
    return (WRITTEN_DECISIONS_AND_EVALUATIONS if rebuild else WRITTEN_EVALUATIONS_ONLY), targets


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def resolve_csv_output_dir(fxdata_dir: str) -> str:
    """Return the CSV root (the directory holding ``history/``) for *fxdata_dir*.

    Accepts the ``fx-daily-data`` checkout root (``<dir>/csv/history``) or the
    CSV root itself (``<dir>/history``, the form ``analyze_estar_lag.py`` takes).
    Raises ``FileNotFoundError`` when neither layout is present.
    """
    base = os.path.abspath(fxdata_dir)
    for candidate in (os.path.join(base, "csv"), base):
        if os.path.isdir(os.path.join(candidate, "history")):
            return candidate
    raise FileNotFoundError(
        f"no history/ archive found under {base} (expected {base}/csv/history or {base}/history)"
    )


def run_backfill(csv_output_dir: str, *, dry_run: bool, log: Log = print) -> BackfillSummary:
    """Run one backfill pass over ``{csv_output_dir}/history`` and return its summary.

    Builds the global indexes once, then examines every batch in
    ``(date, forecast_batch_id)`` order.  With *dry_run* nothing is written and
    the summary reports what a real run would write.  Skipped batches are
    logged one per line through *log*; a batch whose archive contradicts
    itself raises ``RuntimeError`` and stops the pass.
    """
    csv_output_dir = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(csv_output_dir, "history")
    if not os.path.isdir(history_dir):
        raise FileNotFoundError(f"no history/ archive under {csv_output_dir}")

    indexes = build_indexes(history_dir)
    batches = collect_forecast_batches(history_dir)
    units = collect_units(history_dir, batches)

    counts: Counter[str] = Counter()
    files: list[str] = []
    with tempfile.TemporaryDirectory(prefix="backfill_execution_history_") as staging_dir:
        for unit in units:
            key, targets = _process_unit(
                unit, indexes, csv_output_dir, staging_dir, dry_run=dry_run, log=log
            )
            counts[key] += 1
            files.extend(targets)
            if key in _SKIP_LABELS:
                log(f"[SKIP] {unit.date_str} {unit.forecast_batch_id}: {_SKIP_LABELS[key]}")

    return BackfillSummary(
        csv_output_dir=csv_output_dir,
        dry_run=dry_run,
        batches=len(units),
        written_decisions_and_evaluations=counts[WRITTEN_DECISIONS_AND_EVALUATIONS],
        written_evaluations_only=counts[WRITTEN_EVALUATIONS_ONLY],
        already_complete=counts[ALREADY_COMPLETE],
        missing_forecast=counts[MISSING_FORECAST],
        partial_forecast=counts[PARTIAL_FORECAST],
        missing_outcome=counts[MISSING_OUTCOME],
        missing_snapshot=counts[MISSING_SNAPSHOT],
        files=tuple(files),
    )


def print_summary(summary: BackfillSummary, log: Log = print) -> None:
    """Print the pass summary: one line per counter, then the manual-push reminder."""
    tag = "[DRY-RUN]" if summary.dry_run else "[OK]"
    verb = "would write" if summary.dry_run else "written"
    log(f"{tag} backfill_execution_history: csv root = {summary.csv_output_dir}")
    log(f"  batches scanned: {summary.batches}")
    log(f"  {verb} (decisions + evaluations): {summary.written_decisions_and_evaluations}")
    log(f"  {verb} (evaluations only): {summary.written_evaluations_only}")
    log(f"  skipped (already complete): {summary.already_complete}")
    log(f"  skipped (missing forecast): {summary.missing_forecast}")
    log(f"  skipped (partial forecast): {summary.partial_forecast}")
    log(f"  skipped (missing outcome): {summary.missing_outcome}")
    log(f"  skipped (missing snapshot): {summary.missing_snapshot}")
    log(f"  archive files {verb}: {len(summary.files)}")
    if summary.dry_run:
        log("  nothing was written (--dry-run).")
    log(
        "[NOTE] This script never commits or pushes: review the fx-daily-data checkout "
        "(git status / git diff) and push it manually."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--fxdata-dir",
        required=True,
        help=(
            "Local checkout of the fx-daily-data branch (its CSV root is <dir>/csv); "
            "the CSV root itself (<dir>/history) is accepted too."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Examine the archive and print the counts without writing anything.",
    )
    args = parser.parse_args(argv)

    try:
        csv_output_dir = resolve_csv_output_dir(args.fxdata_dir)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    summary = run_backfill(csv_output_dir, dry_run=args.dry_run)
    print_summary(summary)


if __name__ == "__main__":
    main()
