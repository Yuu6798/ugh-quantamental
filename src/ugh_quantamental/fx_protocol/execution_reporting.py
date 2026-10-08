"""Aggregation, acceptance gate and artifacts for the FX execution layer v1 (spec §8–§10).

Reads the archived ``history/<date>/<batch>/execution_evaluation.csv`` files
(and inventories the ``execution.csv`` decision files next to them), folds the
per-book equity curves of spec §5.2, computes the spec §8 metrics per
``execution_version`` stratum, evaluates the spec §9 acceptance gate on the
cumulative live cohort, and writes the weekly / monthly / latest artifacts.

Pure read-only except for the explicit ``export_*`` functions.  No clock is
read: ``generated_at_utc`` is always passed in by the caller.  No network.
Importable without SQLAlchemy.

The activation marker ``EXECUTION_ACTIVATION_AS_OF`` and the exclusion set
``EXECUTION_EXCLUDED_AS_OF`` are looked up on this module at call time (they
are imported into its namespace) so a test can patch the boundary cases.
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
import re
import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from ugh_quantamental.fx_protocol.calendar import (
    current_as_of_jst,
    is_protocol_business_day,
    next_as_of_jst,
)
from ugh_quantamental.fx_protocol.csv_exports import _blank
from ugh_quantamental.fx_protocol.csv_utils import write_csv_rows
from ugh_quantamental.fx_protocol.execution import (
    EXECUTION_ACTIVATION_AS_OF,
    EXECUTION_EXCLUDED_AS_OF,
    EXECUTION_INITIAL_EQUITY_JPY,
    EXECUTION_ROUND_TRIP_COST_JPY_PER_USD,
    EXECUTION_VERSION,
)
from ugh_quantamental.fx_protocol.execution_exports import (
    load_execution_decisions_csv,
    load_execution_evaluations_csv,
)
from ugh_quantamental.fx_protocol.execution_models import EXECUTION_BOOK_ORDER, BookId
from ugh_quantamental.fx_protocol.models import _JST, _to_aware_utc, _to_jst
from ugh_quantamental.fx_protocol.weekly_report_exports import _fmt_bp, _fmt_pct

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gate thresholds (spec §9) and blocked-reason identifiers
# ---------------------------------------------------------------------------

#: Criterion 1a: ``ugh_x1`` trades (``side != 0``) in the live cohort.
GATE_MIN_TRADE_COUNT: int = 100
#: Criterion 1b: calendar days from the cohort's first to last ``as_of_jst`` ("six months").
GATE_MIN_CALENDAR_DAYS: int = 182
#: Criterion 2: t-statistic of the size-weighted, cost-deducted live daily return.
GATE_MIN_T_STAT: float = 2.0
#: Criterion 3: maximum drawdown of the live equity curve (positive magnitude, ``<=``).
GATE_MAX_DRAWDOWN: float = 0.10

BLOCKED_INCOMPLETE_BATCHES: str = "incomplete_batches"
BLOCKED_MISSING_EVALUATIONS: str = "missing_evaluations"
BLOCKED_INCOMPLETE_DECISIONS: str = "incomplete_decisions"
BLOCKED_MISSING_DECISIONS: str = "missing_decisions"
BLOCKED_MISSING_LIVE: str = "missing_live"
BLOCKED_DUPLICATE_BATCHES: str = "duplicate_batches"

#: Every ``gate.blocked_reasons`` value, in the order they are reported.
GATE_BLOCKED_REASONS: tuple[str, ...] = (
    BLOCKED_INCOMPLETE_BATCHES,
    BLOCKED_MISSING_EVALUATIONS,
    BLOCKED_INCOMPLETE_DECISIONS,
    BLOCKED_MISSING_DECISIONS,
    BLOCKED_MISSING_LIVE,
    BLOCKED_DUPLICATE_BATCHES,
)

#: Per-book metric columns of ``execution_{scope}.csv`` (spec §8 column definitions).
EXECUTION_REPORT_BOOK_FIELDNAMES: tuple[str, ...] = (
    "execution_version",
    "book_id",
    "decision_count",
    "trade_count",
    "live_trade_count",
    "skip_counts",
    "live_coverage_rate",
    "direction_hit_rate",
    "capture_bp",
    "signed_bp_live_mean",
    "signed_bp_live_sd",
    "signed_bp_live_t",
    "signed_bp_bar_mean",
    "signed_bp_bar_sd",
    "signed_bp_bar_t",
    "pnl_jpy_live",
    "pnl_jpy_bar",
    "final_equity_jpy_live",
    "final_equity_jpy_bar",
    "max_drawdown_live",
    "max_drawdown_bar",
    "profit_factor_live",
    "cost_jpy_live",
    "cost_jpy_bar",
)

_LIVE: str = "live"
_BP_SCALE: float = 10_000.0
_DECISION_FILENAME: str = "execution.csv"
_EVALUATION_FILENAME: str = "execution_evaluation.csv"
_FORECAST_FILENAME: str = "forecast.csv"
_DIR_DATE_FORMAT: str = "%Y%m%d"
_BENCHMARK_BOOKS: tuple[BookId, ...] = (BookId.bench_gpt_m3, BookId.bench_long)
_EXPECTED_BOOK_SET: frozenset[BookId] = frozenset(EXECUTION_BOOK_ORDER)
#: Artifact scopes ``export_execution_report_artifacts`` accepts (``analytics/execution/<scope>/``).
EXECUTION_REPORT_SCOPES: tuple[str, ...] = ("weekly", "monthly")
#: ``date_str`` of an artifact directory: ``YYYYMMDD`` (weekly) or ``YYYYMM`` (monthly).
_DATE_STR_PATTERN: re.Pattern[str] = re.compile(r"\d{6}|\d{8}")
#: Row fields the six rows of one evaluation batch must agree on: the batch identity and the
#: one outcome the batch was evaluated against (``as_of_jst`` is compared as an instant).
_BATCH_METADATA_FIELDS: tuple[str, ...] = (
    "execution_version",
    "as_of_jst",
    "outcome_id",
    "realized_open",
    "realized_close",
)
#: Decimal places the gate compares at: float noise from the equity fold cannot flip an exact
#: boundary case (a 10.00% drawdown, t = 2.00) while 10.01% / 1.99 keep their verdict.
_GATE_DECIMALS: int = 9


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class IncompleteExecutionBatch(BaseModel):
    """A ``forecast_batch_id`` whose evaluation rows are not one usable six-book batch (spec §8).

    Either books are missing (``missing_books``) or the rows disagree on the
    batch metadata every row must share (``inconsistent_fields`` names
    ``execution_version`` / ``as_of_jst``): a version-boundary or partially
    copied batch is not silently reduced to its first row's metadata.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    forecast_batch_id: str
    execution_version: str
    as_of_jst: datetime
    missing_books: tuple[str, ...]
    inconsistent_fields: tuple[str, ...] = ()

    @field_validator("as_of_jst")
    @classmethod
    def _normalize_as_of(cls, v: datetime) -> datetime:
        return _to_jst(v)


class MissingExecutionEvaluation(BaseModel):
    """A complete decision file whose closed window has no complete evaluation file (spec §9)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    forecast_batch_id: str
    execution_version: str
    as_of_jst: datetime
    window_end_jst: datetime

    @field_validator("as_of_jst", "window_end_jst")
    @classmethod
    def _normalize_jst(cls, v: datetime) -> datetime:
        return _to_jst(v)


class MissingExecutionDecision(BaseModel):
    """An expected protocol day without a complete current-version decision file (spec §9).

    ``forecast_batch_id`` is the id found in that day's ``forecast.csv`` when the
    forecast was published, else ``None`` (the day is missing either way).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of_jst: datetime
    forecast_batch_id: str | None

    @field_validator("as_of_jst")
    @classmethod
    def _normalize_as_of(cls, v: datetime) -> datetime:
        return _to_jst(v)


class ExecutionDefectInventory(BaseModel):
    """The six archive-defect inventories of spec §9, one tuple each (all empty when clean)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incomplete_batches: tuple[IncompleteExecutionBatch, ...] = ()
    missing_evaluations: tuple[MissingExecutionEvaluation, ...] = ()
    incomplete_decision_batches: tuple[str, ...] = ()
    missing_decisions: tuple[MissingExecutionDecision, ...] = ()
    missing_live: tuple[date, ...] = ()
    duplicate_batches: tuple[date, ...] = ()

    def blocked_reasons(self) -> tuple[str, ...]:
        """Return the ``GATE_BLOCKED_REASONS`` whose inventory is non-empty, in canonical order."""
        present = (
            (BLOCKED_INCOMPLETE_BATCHES, self.incomplete_batches),
            (BLOCKED_MISSING_EVALUATIONS, self.missing_evaluations),
            (BLOCKED_INCOMPLETE_DECISIONS, self.incomplete_decision_batches),
            (BLOCKED_MISSING_DECISIONS, self.missing_decisions),
            (BLOCKED_MISSING_LIVE, self.missing_live),
            (BLOCKED_DUPLICATE_BATCHES, self.duplicate_batches),
        )
        return tuple(reason for reason, items in present if items)


class CollectedExecutionEvaluations(ExecutionDefectInventory):
    """Result of :func:`collect_execution_evaluation_rows`.

    ``rows`` are the raw ``execution_evaluation.csv`` cells of every complete,
    non-duplicate batch, deduplicated by ``(forecast_batch_id, book_id)`` and
    ordered by ``(as_of_jst, forecast_batch_id, book order)``.  The six
    inherited inventories hold only the defects that block the acceptance gate
    (current ``execution_version``, dated on or after
    ``EXECUTION_ACTIVATION_AS_OF``); every other defect — before the activation
    marker, or tagged with another version — is reported under
    ``archive_defects`` and never blocks.  ``missing_decisions`` and
    ``missing_live`` are derived from the calendar cohort that starts at the
    activation marker, so their ``archive_defects`` counterparts are empty by
    construction.
    """

    rows: tuple[dict[str, str], ...]
    archive_defects: ExecutionDefectInventory


# ---------------------------------------------------------------------------
# Activation / version split and calendar cohort
# ---------------------------------------------------------------------------


def _as_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return _to_jst(value).date()
    return value


def is_gate_blocking_defect(as_of_jst: date | datetime, execution_version: str | None) -> bool:
    """Return ``True`` when a defect dated *as_of_jst* blocks the current version's gate.

    Spec §9: only defects on or after ``EXECUTION_ACTIVATION_AS_OF`` under the
    current ``EXECUTION_VERSION`` block; a defect before the marker (bar-only
    backfill territory) or on another version is reported but never blocks.
    *execution_version* ``None`` means the version could not be read (an
    unreadable decision file): such a defect is treated as the current version.
    """
    if _as_date(as_of_jst) < EXECUTION_ACTIVATION_AS_OF:
        return False
    return execution_version is None or execution_version == EXECUTION_VERSION


def _day_as_of_jst(day: date) -> datetime:
    return current_as_of_jst(datetime(day.year, day.month, day.day, tzinfo=_JST))


def expected_decision_days(generated_at_utc: datetime) -> tuple[tuple[date, ...], tuple[date, ...]]:
    """Return ``(expected_days, excluded_days)`` of the calendar cohort (spec §9).

    Expected days are the protocol business days from ``EXECUTION_ACTIVATION_AS_OF``
    whose window has closed by *generated_at_utc* (``next_as_of_jst(D) <= generated_at_utc``),
    minus ``EXECUTION_EXCLUDED_AS_OF``.  The second tuple holds the excluded days
    that fall inside that range, so the report can show how many were removed;
    an exclusion that is not a candidate (before the marker, on a weekend, or
    whose window has not closed yet) removes nothing and is not counted.
    Naive *generated_at_utc* is treated as UTC.
    """
    generated = _to_aware_utc(generated_at_utc)
    expected: list[date] = []
    excluded: list[date] = []
    day = EXECUTION_ACTIVATION_AS_OF
    while True:
        as_of = _day_as_of_jst(day)
        if is_protocol_business_day(as_of):
            if next_as_of_jst(as_of) > generated:
                break
            if day in EXECUTION_EXCLUDED_AS_OF:
                excluded.append(day)
            else:
                expected.append(day)
        day += timedelta(days=1)
    return tuple(expected), tuple(excluded)


# ---------------------------------------------------------------------------
# Archive scan
# ---------------------------------------------------------------------------


#: ``(forecast_batch_id, execution_version, as_of_jst, window_end_jst)``: the metadata every
#: row of one decision or evaluation file must share, and that an evaluation must share with
#: the decision file it evaluates.
_BatchKey = tuple[str, str, datetime, datetime]


@dataclass(frozen=True, slots=True)
class _DecisionFile:
    """A complete ``execution.csv`` (one row per book) and the metadata the inventory needs."""

    rel_path: str
    dir_date: date | None
    forecast_batch_id: str
    execution_version: str
    as_of_jst: datetime
    window_end_jst: datetime
    ugh_x1_entry_status: str


@dataclass(frozen=True, slots=True)
class _ArchiveScan:
    """Everything one pass over ``history/`` yields, before deduplication.

    ``complete_evaluation_keys`` holds one ``_BatchKey`` per complete evaluation
    file whose six rows share their batch metadata: the key a decision file
    must match to count as evaluated.
    """

    evaluation_rows: tuple[dict[str, str], ...]
    complete_evaluation_keys: frozenset[_BatchKey]
    complete_decisions: tuple[_DecisionFile, ...]
    incomplete_decisions: tuple[tuple[str, date | None], ...]


def _is_complete_book_set(book_ids: Iterable[BookId]) -> bool:
    ids = tuple(book_ids)
    return len(ids) == len(EXECUTION_BOOK_ORDER) and set(ids) == _EXPECTED_BOOK_SET


def _parse_dir_date(name: str) -> date | None:
    try:
        return datetime.strptime(name, _DIR_DATE_FORMAT).date()
    except ValueError:
        return None


def _row_as_of_jst(row: dict[str, str]) -> datetime:
    return _to_jst(datetime.fromisoformat(row["as_of_jst"]))


def _inconsistent_batch_fields(rows: Sequence[dict[str, str]]) -> tuple[str, ...]:
    """The ``_BATCH_METADATA_FIELDS`` whose values differ across *rows* (one batch's rows)."""
    inconsistent: list[str] = []
    for field in _BATCH_METADATA_FIELDS:
        if field == "as_of_jst":
            values: set[object] = {_row_as_of_jst(row) for row in rows}
        else:
            values = {row.get(field, "") for row in rows}
        if len(values) > 1:
            inconsistent.append(field)
    return tuple(inconsistent)


def _read_raw_rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _scan_batch_dir(
    batch_path: str,
    rel_path: str,
    dir_date: date | None,
    evaluation_rows: list[dict[str, str]],
    complete_evaluation_keys: set[_BatchKey],
    complete_decisions: list[_DecisionFile],
    incomplete_decisions: list[tuple[str, date | None]],
) -> None:
    evaluation_path = os.path.join(batch_path, _EVALUATION_FILENAME)
    if os.path.isfile(evaluation_path):
        try:
            evaluations = load_execution_evaluations_csv(evaluation_path)
        except (ValueError, OSError):
            logger.warning("execution evaluation CSV %s is unreadable; skipped", evaluation_path)
        else:
            evaluation_rows.extend(_read_raw_rows(evaluation_path))
            keys = {
                (ev.forecast_batch_id, ev.execution_version, ev.as_of_jst, ev.window_end_jst)
                for ev in evaluations
            }
            outcomes = {
                (ev.outcome_id, ev.realized_open, ev.realized_close, ev.evaluated_at_utc)
                for ev in evaluations
            }
            # Only a six-book file whose rows agree on their batch metadata *and* were
            # evaluated against one outcome evaluates anything; a mixed file is reported by
            # the collector, never credited to a decision file.
            if (
                len(keys) == 1
                and len(outcomes) == 1
                and _is_complete_book_set(ev.book_id for ev in evaluations)
            ):
                complete_evaluation_keys.update(keys)

    decision_path = os.path.join(batch_path, _DECISION_FILENAME)
    if not os.path.isfile(decision_path):
        return
    try:
        decisions = load_execution_decisions_csv(decision_path)
    except (ValueError, OSError):
        decisions = ()
    if not _is_complete_book_set(d.book_id for d in decisions):
        incomplete_decisions.append((rel_path, dir_date))
        return
    keys = {
        (d.forecast_batch_id, d.execution_version, d.as_of_jst, d.window_end_jst) for d in decisions
    }
    if len(keys) != 1:
        # Rows of two batches, versions or windows in one file: not a decision batch, and
        # never reduced to its first row's metadata.
        incomplete_decisions.append((rel_path, dir_date))
        return
    first = decisions[0]
    ugh_x1 = next(d for d in decisions if d.book_id == BookId.ugh_x1)
    complete_decisions.append(
        _DecisionFile(
            rel_path=rel_path,
            dir_date=dir_date,
            forecast_batch_id=first.forecast_batch_id,
            execution_version=first.execution_version,
            as_of_jst=first.as_of_jst,
            window_end_jst=first.window_end_jst,
            ugh_x1_entry_status=ugh_x1.entry_status,
        )
    )


def _scan_history(history_dir: str) -> _ArchiveScan:
    """Walk ``history/<date>/<batch>/`` (sorted, like ``collect_evaluated_forecast_rows``)."""
    evaluation_rows: list[dict[str, str]] = []
    complete_evaluation_keys: set[_BatchKey] = set()
    complete_decisions: list[_DecisionFile] = []
    incomplete_decisions: list[tuple[str, date | None]] = []

    if os.path.isdir(history_dir):
        for date_dir in sorted(os.listdir(history_dir)):
            date_path = os.path.join(history_dir, date_dir)
            if not os.path.isdir(date_path):
                continue
            dir_date = _parse_dir_date(date_dir)
            for batch_dir in sorted(os.listdir(date_path)):
                batch_path = os.path.join(date_path, batch_dir)
                if not os.path.isdir(batch_path):
                    continue
                _scan_batch_dir(
                    batch_path,
                    f"history/{date_dir}/{batch_dir}",
                    dir_date,
                    evaluation_rows,
                    complete_evaluation_keys,
                    complete_decisions,
                    incomplete_decisions,
                )

    return _ArchiveScan(
        evaluation_rows=tuple(evaluation_rows),
        complete_evaluation_keys=frozenset(complete_evaluation_keys),
        complete_decisions=tuple(complete_decisions),
        incomplete_decisions=tuple(incomplete_decisions),
    )


def _lookup_forecast_batch_id(history_dir: str, day: date) -> str | None:
    """Return the ``forecast_batch_id`` published for *day* in its own date dir, else ``None``."""
    date_path = os.path.join(history_dir, day.strftime(_DIR_DATE_FORMAT))
    if not os.path.isdir(date_path):
        return None
    for batch_dir in sorted(os.listdir(date_path)):
        forecast_path = os.path.join(date_path, batch_dir, _FORECAST_FILENAME)
        if not os.path.isfile(forecast_path):
            continue
        try:
            rows = _read_raw_rows(forecast_path)
        except (OSError, ValueError, csv.Error):
            # Best-effort id lookup only: an unreadable forecast.csv (a UnicodeDecodeError is a
            # ValueError) must not break the report; the day is still reported as missing.
            continue
        for row in rows:
            as_of = row.get("as_of_jst") or ""
            try:
                row_day = _to_jst(datetime.fromisoformat(as_of)).date()
            except ValueError:
                continue
            if row_day == day:
                return row.get("forecast_batch_id") or batch_dir
    return None


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


class _InventoryBuilder:
    """Mutable accumulator for one :class:`ExecutionDefectInventory`."""

    def __init__(self) -> None:
        self.incomplete_batches: list[IncompleteExecutionBatch] = []
        self.missing_evaluations: list[MissingExecutionEvaluation] = []
        self.incomplete_decision_batches: list[str] = []
        self.missing_decisions: list[MissingExecutionDecision] = []
        self.missing_live: list[date] = []
        self.duplicate_batches: list[date] = []

    def as_fields(self) -> dict[str, tuple[Any, ...]]:
        return {
            "incomplete_batches": tuple(self.incomplete_batches),
            "missing_evaluations": tuple(self.missing_evaluations),
            "incomplete_decision_batches": tuple(self.incomplete_decision_batches),
            "missing_decisions": tuple(self.missing_decisions),
            "missing_live": tuple(self.missing_live),
            "duplicate_batches": tuple(self.duplicate_batches),
        }

    def build(self) -> ExecutionDefectInventory:
        return ExecutionDefectInventory(**self.as_fields())


_BOOK_RANK: dict[str, int] = {book.value: rank for rank, book in enumerate(EXECUTION_BOOK_ORDER)}


def _row_sort_key(row: dict[str, str]) -> tuple[datetime, str, int]:
    return (_row_as_of_jst(row), row["forecast_batch_id"], _BOOK_RANK[row["book_id"]])


def collect_execution_evaluation_rows(
    history_dir: str,
    *,
    generated_at_utc: datetime,
) -> CollectedExecutionEvaluations:
    """Read every ``history/*/*/execution_evaluation.csv`` and inventory the archive (spec §8–§9).

    Parameters
    ----------
    history_dir:
        The ``history/`` directory (``{csv_output_dir}/history``).  A missing
        directory is an empty archive.
    generated_at_utc:
        The report's generation time, passed through unchanged (this function
        reads no clock).  It closes the calendar cohort and separates pending
        windows (``window_end_jst > generated_at_utc``) from missing evaluations.

    Returns
    -------
    CollectedExecutionEvaluations
        Deduplicated rows of complete, non-duplicate batches plus the blocking
        and archive-only defect inventories.  See the model docstring.
    """
    generated = _to_aware_utc(generated_at_utc)
    scan = _scan_history(history_dir)

    # Deduplicate evaluation rows by (forecast_batch_id, book_id): first occurrence wins.
    rows_by_batch: dict[str, dict[str, dict[str, str]]] = {}
    for row in scan.evaluation_rows:
        books = rows_by_batch.setdefault(row["forecast_batch_id"], {})
        books.setdefault(row["book_id"], row)

    blocking = _InventoryBuilder()
    archive = _InventoryBuilder()

    def _route(as_of: date | datetime, version: str | None) -> _InventoryBuilder:
        return blocking if is_gate_blocking_defect(as_of, version) else archive

    # Six-book completeness per batch (every row carrying the same batch metadata);
    # complete ones also feed duplicate detection.
    complete_batches: dict[str, tuple[datetime, str]] = {}
    for batch_id, books in rows_by_batch.items():
        batch_rows = list(books.values())
        as_of = _row_as_of_jst(batch_rows[0])
        version = batch_rows[0]["execution_version"]
        missing = tuple(b.value for b in EXECUTION_BOOK_ORDER if b.value not in books)
        inconsistent = _inconsistent_batch_fields(batch_rows)
        if inconsistent:
            # Route a mixed batch by its latest day and by the current version whenever any
            # row carries it, so a version-boundary batch blocks the current gate.
            as_of = max(_row_as_of_jst(row) for row in batch_rows)
            if any(row["execution_version"] == EXECUTION_VERSION for row in batch_rows):
                version = EXECUTION_VERSION
        if missing or inconsistent:
            _route(as_of, version).incomplete_batches.append(
                IncompleteExecutionBatch(
                    forecast_batch_id=batch_id,
                    execution_version=version,
                    as_of_jst=as_of,
                    missing_books=missing,
                    inconsistent_fields=inconsistent,
                )
            )
        else:
            complete_batches[batch_id] = (as_of, version)

    # Duplicate detection: >= 2 complete batches (decision or evaluation) on one version-day.
    batches_by_version_day: dict[tuple[str, date], set[str]] = {}
    for decision in scan.complete_decisions:
        key = (decision.execution_version, decision.as_of_jst.date())
        batches_by_version_day.setdefault(key, set()).add(decision.forecast_batch_id)
    for batch_id, (as_of, version) in complete_batches.items():
        batches_by_version_day.setdefault((version, as_of.date()), set()).add(batch_id)
    duplicate_batch_ids: set[str] = set()
    for (version, day), batch_ids in sorted(batches_by_version_day.items()):
        if len(batch_ids) >= 2:
            _route(day, version).duplicate_batches.append(day)
            duplicate_batch_ids.update(batch_ids)

    rows = [
        row
        for batch_id, books in rows_by_batch.items()
        if batch_id in complete_batches and batch_id not in duplicate_batch_ids
        for row in books.values()
    ]
    rows.sort(key=_row_sort_key)

    # Decision inventory: complete decision files whose closed window has no complete evaluation.
    seen_decision_batches: set[str] = set()
    for decision in scan.complete_decisions:
        if decision.forecast_batch_id in seen_decision_batches:
            continue
        seen_decision_batches.add(decision.forecast_batch_id)
        key: _BatchKey = (
            decision.forecast_batch_id,
            decision.execution_version,
            decision.as_of_jst,
            decision.window_end_jst,
        )
        if key in scan.complete_evaluation_keys:
            continue  # evaluated: same batch id *and* the same version / window metadata
        if decision.window_end_jst > generated:
            continue  # pending window: its evaluation is not due yet
        _route(decision.as_of_jst, decision.execution_version).missing_evaluations.append(
            MissingExecutionEvaluation(
                forecast_batch_id=decision.forecast_batch_id,
                execution_version=decision.execution_version,
                as_of_jst=decision.as_of_jst,
                window_end_jst=decision.window_end_jst,
            )
        )
    for rel_path, dir_date in scan.incomplete_decisions:
        target = blocking if dir_date is None else _route(dir_date, None)
        target.incomplete_decision_batches.append(rel_path)

    # Calendar cohort: every expected day needs one complete current-version decision file in
    # its own date dir, and its ugh_x1 decision must be a live row.
    current_by_day: dict[date, list[_DecisionFile]] = {}
    for decision in scan.complete_decisions:
        day = decision.as_of_jst.date()
        if decision.execution_version == EXECUTION_VERSION and decision.dir_date == day:
            current_by_day.setdefault(day, []).append(decision)
    expected, _excluded = expected_decision_days(generated)
    for day in expected:
        files = current_by_day.get(day, [])
        if not files:
            blocking.missing_decisions.append(
                MissingExecutionDecision(
                    as_of_jst=_day_as_of_jst(day),
                    forecast_batch_id=_lookup_forecast_batch_id(history_dir, day),
                )
            )
        if not any(f.ugh_x1_entry_status == _LIVE for f in files):
            blocking.missing_live.append(day)

    return CollectedExecutionEvaluations(
        rows=tuple(rows),
        archive_defects=archive.build(),
        **blocking.as_fields(),
    )


# ---------------------------------------------------------------------------
# Row parsing and metric primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _EvalRow:
    """One evaluation row with typed cells (the CSV was validated by the loader on read)."""

    forecast_batch_id: str
    book_id: str
    execution_version: str
    as_of_jst: datetime
    side: int
    size: float
    skip_reason: str
    entry_status: str
    entry_price_live: float | None
    realized_open: float
    realized_close: float
    pnl_live_bp: float | None
    pnl_bar_bp: float
    cost_live_bp: float | None
    cost_bar_bp: float
    hit: bool | None

    @property
    def is_trade(self) -> bool:
        return self.side != 0

    @property
    def is_live(self) -> bool:
        return self.entry_status == _LIVE

    @property
    def signed_bp_live(self) -> float | None:
        if self.pnl_live_bp is None or self.cost_live_bp is None:
            return None
        return self.size * (self.pnl_live_bp - self.cost_live_bp)

    @property
    def signed_bp_bar(self) -> float:
        return self.size * (self.pnl_bar_bp - self.cost_bar_bp)

    @property
    def capture_bp(self) -> float:
        return (
            self.side * (self.realized_close - self.realized_open) / self.realized_open * _BP_SCALE
        )


def _opt_float(cell: str) -> float | None:
    return float(cell) if cell != "" else None


def _opt_bool(cell: str) -> bool | None:
    if cell == "":
        return None
    return cell.strip().lower() in ("true", "1", "yes")


def _parse_row(row: dict[str, str]) -> _EvalRow:
    return _EvalRow(
        forecast_batch_id=row["forecast_batch_id"],
        book_id=row["book_id"],
        execution_version=row["execution_version"],
        as_of_jst=_row_as_of_jst(row),
        side=int(row["side"]),
        size=float(row["size"]),
        skip_reason=row["skip_reason"],
        entry_status=row["entry_status"],
        entry_price_live=_opt_float(row["entry_price_live"]),
        realized_open=float(row["realized_open"]),
        realized_close=float(row["realized_close"]),
        pnl_live_bp=_opt_float(row["pnl_live_bp"]),
        pnl_bar_bp=float(row["pnl_bar_bp"]),
        cost_live_bp=_opt_float(row["cost_live_bp"]),
        cost_bar_bp=float(row["cost_bar_bp"]),
        hit=_opt_bool(row["hit"]),
    )


@dataclass(frozen=True, slots=True)
class _SeriesStats:
    count: int
    mean: float | None
    sd: float | None
    t: float | None


def _series_stats(values: Sequence[float]) -> _SeriesStats:
    """Mean, sample standard deviation and t-statistic of a trade-return series.

    ``sd`` needs two observations; ``t = mean / (sd / sqrt(n))`` needs three
    and a non-zero ``sd`` (spec §9: ``statistics.stdev``, never ``pstdev``).
    """
    n = len(values)
    if n == 0:
        return _SeriesStats(0, None, None, None)
    mean = statistics.fmean(values)
    if n < 2:
        return _SeriesStats(n, mean, None, None)
    sd = statistics.stdev(values)
    if n < 3 or sd == 0:
        return _SeriesStats(n, mean, sd, None)
    return _SeriesStats(n, mean, sd, mean / (sd / math.sqrt(n)))


@dataclass(frozen=True, slots=True)
class _EquityCurve:
    final_equity_jpy: float
    pnl_jpy: float
    cost_jpy: float
    max_drawdown: float
    trade_pnl_jpy: tuple[float, ...]


def _fold_equity(rows: Sequence[_EvalRow], *, live: bool) -> _EquityCurve:
    """Fold *rows* (ascending ``as_of_jst``) into the compounding equity curve of spec §5.2.

    ``position_usd = equity × size / entry`` and
    ``pnl_jpy = side × position_usd × (exit − entry) − |side| × position_usd × cost``
    with ``entry = entry_price_live`` for the live series and ``realized_open``
    for the bar series; exit is always ``realized_close``.  Skipped rows leave
    equity flat.  The drawdown is the positive magnitude
    ``max_t (peak_t − equity_t) / peak_t`` clamped to ``[0, 1]``.
    """
    initial = float(EXECUTION_INITIAL_EQUITY_JPY)
    equity = initial
    peak = initial
    max_drawdown = 0.0
    cost_total = 0.0
    trade_pnls: list[float] = []
    for row in rows:
        entry = row.entry_price_live if live else row.realized_open
        if row.is_trade:
            if entry is None or entry <= 0:
                raise ValueError(
                    f"execution report requires a positive entry price for trade rows "
                    f"(batch {row.forecast_batch_id!r}, book {row.book_id!r})"
                )
            position_usd = equity * row.size / entry
            gross = row.side * position_usd * (row.realized_close - entry)
            cost = abs(row.side) * position_usd * EXECUTION_ROUND_TRIP_COST_JPY_PER_USD
            pnl = gross - cost
            equity += pnl
            cost_total += cost
            trade_pnls.append(pnl)
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - equity) / peak)
    return _EquityCurve(
        final_equity_jpy=equity,
        pnl_jpy=equity - initial,
        cost_jpy=cost_total,
        max_drawdown=min(max_drawdown, 1.0),
        trade_pnl_jpy=tuple(trade_pnls),
    )


def _profit_factor(trade_pnls: Sequence[float]) -> float | None:
    gains = sum(p for p in trade_pnls if p > 0)
    losses = sum(p for p in trade_pnls if p < 0)
    if losses == 0:
        return None
    return gains / abs(losses)


def _sorted_rows(rows: Iterable[_EvalRow]) -> list[_EvalRow]:
    return sorted(rows, key=lambda r: (r.as_of_jst, r.forecast_batch_id))


# ---------------------------------------------------------------------------
# Per-book metrics, strata and gate
# ---------------------------------------------------------------------------


def _book_metrics(rows: Sequence[_EvalRow]) -> dict[str, Any]:
    """Spec §8 metrics for one book's rows (any order; sorted here)."""
    ordered = _sorted_rows(rows)
    trades = [r for r in ordered if r.is_trade]
    live_rows = [r for r in ordered if r.is_live]
    live_trades = [r for r in trades if r.is_live]

    skip_counts: dict[str, int] = {}
    for row in ordered:
        if not row.is_trade:
            skip_counts[row.skip_reason] = skip_counts.get(row.skip_reason, 0) + 1

    live_values = [v for v in (r.signed_bp_live for r in live_trades) if v is not None]
    live_stats = _series_stats(live_values)
    bar_stats = _series_stats([r.signed_bp_bar for r in trades])
    live_curve = _fold_equity(live_rows, live=True)
    bar_curve = _fold_equity(ordered, live=False)
    hits = sum(1 for r in trades if r.hit)

    return {
        "decision_count": len(ordered),
        "trade_count": len(trades),
        "live_trade_count": live_stats.count,
        "skip_counts": dict(sorted(skip_counts.items())),
        "live_coverage_rate": len(live_rows) / len(ordered) if ordered else None,
        "direction_hit_rate": hits / len(trades) if trades else None,
        "capture_bp": sum(r.capture_bp for r in trades),
        "signed_bp_live_mean": live_stats.mean,
        "signed_bp_live_sd": live_stats.sd,
        "signed_bp_live_t": live_stats.t,
        "signed_bp_bar_mean": bar_stats.mean,
        "signed_bp_bar_sd": bar_stats.sd,
        "signed_bp_bar_t": bar_stats.t,
        "pnl_jpy_live": live_curve.pnl_jpy,
        "pnl_jpy_bar": bar_curve.pnl_jpy,
        "final_equity_jpy_live": live_curve.final_equity_jpy,
        "final_equity_jpy_bar": bar_curve.final_equity_jpy,
        "max_drawdown_live": live_curve.max_drawdown,
        "max_drawdown_bar": bar_curve.max_drawdown,
        "profit_factor_live": _profit_factor(live_curve.trade_pnl_jpy),
        "cost_jpy_live": live_curve.cost_jpy,
        "cost_jpy_bar": bar_curve.cost_jpy,
    }


def _delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def _benchmark_deltas(books: dict[str, dict[str, Any]]) -> dict[str, dict[str, float | None]]:
    """``ugh_x1`` minus each benchmark book on ``pnl_jpy_live`` and ``capture_bp`` (spec §8)."""
    main = books.get(BookId.ugh_x1.value)
    deltas: dict[str, dict[str, float | None]] = {}
    for bench in _BENCHMARK_BOOKS:
        other = books.get(bench.value)
        if main is None or other is None:
            deltas[bench.value] = {"pnl_jpy_live_delta": None, "capture_bp_delta": None}
            continue
        deltas[bench.value] = {
            "pnl_jpy_live_delta": _delta(main["pnl_jpy_live"], other["pnl_jpy_live"]),
            "capture_bp_delta": _delta(main["capture_bp"], other["capture_bp"]),
        }
    return deltas


def _build_strata(rows: Sequence[_EvalRow]) -> dict[str, dict[str, Any]]:
    """Group *rows* by ``execution_version`` and compute per-book metrics; versions never mix."""
    by_version: dict[str, list[_EvalRow]] = {}
    for row in rows:
        by_version.setdefault(row.execution_version, []).append(row)

    strata: dict[str, dict[str, Any]] = {}
    for version in sorted(by_version):
        version_rows = by_version[version]
        books: dict[str, dict[str, Any]] = {}
        for book in EXECUTION_BOOK_ORDER:
            book_rows = [r for r in version_rows if r.book_id == book.value]
            if book_rows:
                books[book.value] = _book_metrics(book_rows)
        as_ofs = sorted({r.as_of_jst for r in version_rows})
        strata[version] = {
            "execution_version": version,
            "row_count": len(version_rows),
            "batch_count": len({r.forecast_batch_id for r in version_rows}),
            "first_as_of_jst": as_ofs[0].isoformat(),
            "last_as_of_jst": as_ofs[-1].isoformat(),
            "books": books,
            "benchmark_deltas": _benchmark_deltas(books),
        }
    return strata


def _gate_value(value: float) -> float:
    """Round a gate statistic to ``_GATE_DECIMALS`` before it is compared with its threshold."""
    return round(value, _GATE_DECIMALS)


def _build_gate(
    all_rows: Sequence[_EvalRow],
    collected: CollectedExecutionEvaluations,
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Spec §9 acceptance gate on the cumulative live cohort of the current version.

    The cohort is every complete, non-duplicate batch in the whole history
    with ``execution_version == EXECUTION_VERSION`` and ``entry_status == live``,
    independent of the report window.  Trade count, t-statistic and drawdown
    come from ``ugh_x1`` rows only; the benchmark books enter only criterion 4.
    """
    cohort = [r for r in all_rows if r.execution_version == EXECUTION_VERSION and r.is_live]
    x1_rows = _sorted_rows(r for r in cohort if r.book_id == BookId.ugh_x1.value)
    x1_trades = [r for r in x1_rows if r.is_trade]
    live_values = [v for v in (r.signed_bp_live for r in x1_trades) if v is not None]
    stats = _series_stats(live_values)
    x1_curve = _fold_equity(x1_rows, live=True) if x1_rows else None
    bench_pnl: dict[str, float | None] = {}
    for bench in _BENCHMARK_BOOKS:
        bench_rows = _sorted_rows(r for r in cohort if r.book_id == bench.value)
        bench_pnl[bench.value] = _fold_equity(bench_rows, live=True).pnl_jpy if bench_rows else None

    as_ofs = sorted({r.as_of_jst for r in cohort})
    first = as_ofs[0] if as_ofs else None
    last = as_ofs[-1] if as_ofs else None
    calendar_days = (last.date() - first.date()).days if first and last else None
    _expected, excluded = expected_decision_days(generated_at_utc)

    trade_count = len(x1_trades)
    x1_pnl = x1_curve.pnl_jpy if x1_curve is not None else None
    max_drawdown = x1_curve.max_drawdown if x1_curve is not None else None
    criteria: dict[str, dict[str, Any]] = {
        "trades_and_duration": {
            "current": {"trade_count": trade_count, "observation_calendar_days": calendar_days},
            "threshold": {
                "trade_count": GATE_MIN_TRADE_COUNT,
                "observation_calendar_days": GATE_MIN_CALENDAR_DAYS,
            },
            "met": trade_count >= GATE_MIN_TRADE_COUNT
            and calendar_days is not None
            and calendar_days >= GATE_MIN_CALENDAR_DAYS,
        },
        "t_stat_live": {
            "current": stats.t,
            "threshold": GATE_MIN_T_STAT,
            "met": stats.t is not None and _gate_value(stats.t) >= GATE_MIN_T_STAT,
        },
        "max_drawdown_live": {
            "current": max_drawdown,
            "threshold": GATE_MAX_DRAWDOWN,
            "met": max_drawdown is not None and _gate_value(max_drawdown) <= GATE_MAX_DRAWDOWN,
        },
        "beats_benchmarks": {
            "current": x1_pnl,
            "threshold": dict(bench_pnl),
            "met": x1_pnl is not None
            and all(pnl is not None and x1_pnl > pnl for pnl in bench_pnl.values()),
        },
    }
    blocked_reasons = collected.blocked_reasons()
    return {
        "execution_version": EXECUTION_VERSION,
        "cohort": {
            "execution_version": EXECUTION_VERSION,
            "first_as_of_jst": first.isoformat() if first else None,
            "last_as_of_jst": last.isoformat() if last else None,
            "trade_count": trade_count,
            "observation_days": len(as_ofs),
            "observation_calendar_days": calendar_days,
            "excluded_days": len(excluded),
            "excluded_as_of_jst": [d.isoformat() for d in excluded],
            "signed_bp_live_mean": stats.mean,
            "signed_bp_live_sd": stats.sd,
        },
        "criteria": criteria,
        "passed": not blocked_reasons and all(c["met"] for c in criteria.values()),
        "blocked_reasons": blocked_reasons,
    }


def _inventory_dict(inventory: ExecutionDefectInventory) -> dict[str, dict[str, Any]]:
    dumped = inventory.model_dump(mode="json", include=set(ExecutionDefectInventory.model_fields))
    return {name: {"count": len(items), "items": items} for name, items in dumped.items()}


def _bound_date(value: datetime | None) -> date | None:
    return None if value is None else _to_jst(value).date()


def run_execution_report(
    csv_output_dir: str,
    *,
    start_as_of_jst: datetime | None,
    end_as_of_jst: datetime | None,
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Aggregate the execution archive under *csv_output_dir* into a JSON-serialisable report.

    Pure read: nothing is written.  ``strata[version].books[book_id]`` carries
    the spec §8 metrics for the rows whose ``as_of_jst`` falls in the window,
    compared on the JST calendar date and inclusive at both ends (a ``None``
    bound is open; both ``None`` is the whole history).  ``gate`` is the spec
    §9 acceptance gate on the cumulative cohort and does not depend on the
    window.  ``inventory`` lists the collected defects (blocking and archive).
    """
    base = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(base, "history")
    generated = _to_aware_utc(generated_at_utc)
    collected = collect_execution_evaluation_rows(history_dir, generated_at_utc=generated)
    parsed = [_parse_row(row) for row in collected.rows]

    start_date = _bound_date(start_as_of_jst)
    end_date = _bound_date(end_as_of_jst)
    windowed = [
        r
        for r in parsed
        if (start_date is None or r.as_of_jst.date() >= start_date)
        and (end_date is None or r.as_of_jst.date() <= end_date)
    ]

    return {
        "report_kind": "fx_execution",
        "execution_version": EXECUTION_VERSION,
        "generated_at_utc": generated.isoformat(),
        "window": {
            "start_as_of_jst": start_date.isoformat() if start_date else None,
            "end_as_of_jst": end_date.isoformat() if end_date else None,
        },
        "row_count": len(windowed),
        "batch_count": len({r.forecast_batch_id for r in windowed}),
        "history_row_count": len(parsed),
        "strata": _build_strata(windowed),
        "gate": _build_gate(parsed, collected, generated),
        "inventory": {
            **_inventory_dict(collected),
            "archive_defects": _inventory_dict(collected.archive_defects),
        },
    }


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


def _fmt_jpy(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return f"{float(value):,.0f}"


def _fmt_t(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return f"{float(value):.2f}"


def _fmt_count(value: Any) -> str:
    return "-" if value is None else str(value)


def _fmt_skip_counts(skip_counts: dict[str, int]) -> str:
    """``reason=count;reason=count`` in reason order (``;`` so the md table cell stays one cell)."""
    return ";".join(f"{reason}={count}" for reason, count in sorted(skip_counts.items()))


def _met(flag: bool) -> str:
    return "yes" if flag else "no"


def _book_table(books: dict[str, dict[str, Any]]) -> list[str]:
    lines = [
        "| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) "
        "| Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t "
        "| P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar "
        "| Max DD live | Max DD bar | PF live | Cost live | Cost bar |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for book_id, m in books.items():
        lines.append(
            f"| {book_id} | {m['decision_count']} | {m['trade_count']} "
            f"| {_fmt_skip_counts(m['skip_counts']) or '-'} "
            f"| {_fmt_pct(m['live_coverage_rate'])} | {_fmt_pct(m['direction_hit_rate'])} "
            f"| {_fmt_bp(m['capture_bp'])} "
            f"| {_fmt_bp(m['signed_bp_live_mean'])} | {_fmt_bp(m['signed_bp_live_sd'])} "
            f"| {_fmt_t(m['signed_bp_live_t'])} "
            f"| {_fmt_bp(m['signed_bp_bar_mean'])} | {_fmt_bp(m['signed_bp_bar_sd'])} "
            f"| {_fmt_t(m['signed_bp_bar_t'])} "
            f"| {_fmt_jpy(m['pnl_jpy_live'])} | {_fmt_jpy(m['pnl_jpy_bar'])} "
            f"| {_fmt_jpy(m['final_equity_jpy_live'])} | {_fmt_jpy(m['final_equity_jpy_bar'])} "
            f"| {_fmt_pct(m['max_drawdown_live'])} | {_fmt_pct(m['max_drawdown_bar'])} "
            f"| {_fmt_t(m['profit_factor_live'])} "
            f"| {_fmt_jpy(m['cost_jpy_live'])} | {_fmt_jpy(m['cost_jpy_bar'])} |"
        )
    return lines


def _gate_table(gate: dict[str, Any]) -> list[str]:
    criteria = gate["criteria"]
    sample = criteria["trades_and_duration"]
    bench = criteria["beats_benchmarks"]
    bench_threshold = ", ".join(
        f"{book} {_fmt_jpy(pnl)}" for book, pnl in sorted(bench["threshold"].items())
    )
    return [
        "| Criterion | Current | Threshold | Met |",
        "|---|---|---|---|",
        f"| 1. ugh_x1 trades and observation span "
        f"| {sample['current']['trade_count']} trades, "
        f"{_fmt_count(sample['current']['observation_calendar_days'])} calendar days "
        f"| >= {sample['threshold']['trade_count']} trades and "
        f">= {sample['threshold']['observation_calendar_days']} calendar days "
        f"| {_met(sample['met'])} |",
        f"| 2. t-statistic of live daily return "
        f"| {_fmt_t(criteria['t_stat_live']['current'])} "
        f"| >= {_fmt_t(criteria['t_stat_live']['threshold'])} "
        f"| {_met(criteria['t_stat_live']['met'])} |",
        f"| 3. max drawdown (live) "
        f"| {_fmt_pct(criteria['max_drawdown_live']['current'])} "
        f"| <= {_fmt_pct(criteria['max_drawdown_live']['threshold'])} "
        f"| {_met(criteria['max_drawdown_live']['met'])} |",
        f"| 4. ugh_x1 live P&L beats both benchmarks "
        f"| {_fmt_jpy(bench['current'])} | > {bench_threshold or '-'} | {_met(bench['met'])} |",
    ]


def _inventory_lines(inventory: dict[str, dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for name in ExecutionDefectInventory.model_fields:
        entry = inventory[name]
        rendered = ", ".join(
            item if isinstance(item, str) else json.dumps(item, ensure_ascii=False, allow_nan=False)
            for item in entry["items"]
        )
        suffix = f": {rendered}" if rendered else ""
        lines.append(f"- {name}: {entry['count']}{suffix}")
    return lines


def build_execution_report_md(report: dict[str, Any]) -> str:
    """Render the report dict as Markdown: per-stratum book and benchmark tables, one gate table."""
    window = report.get("window", {})
    start = window.get("start_as_of_jst")
    end = window.get("end_as_of_jst")
    if start is None and end is None:
        window_label = "cumulative (whole history)"
    else:
        window_label = f"{start or 'open'} to {end or 'open'}"

    lines: list[str] = [
        f"# FX Execution Report — {window_label}",
        "",
        f"Generated: {report.get('generated_at_utc', 'N/A')}",
        f"Current execution_version: {report.get('execution_version', 'N/A')}",
        f"Rows in window: {report.get('row_count', 0)} "
        f"({report.get('batch_count', 0)} complete batches)",
        "",
    ]

    strata = report.get("strata", {})
    if not strata:
        lines.extend(["## Books", "", "No complete batches in the window.", ""])
    for version, stratum in strata.items():
        lines.append(f"## Stratum execution_version={version}")
        lines.append("")
        lines.append(
            f"Windows: {stratum.get('batch_count', 0)} "
            f"({stratum.get('first_as_of_jst', '?')} to {stratum.get('last_as_of_jst', '?')})"
        )
        lines.append("")
        lines.append("### Books")
        lines.append("")
        lines.extend(_book_table(stratum.get("books", {})))
        lines.append("")
        lines.append("### Benchmark deltas (ugh_x1 minus benchmark)")
        lines.append("")
        lines.append("| Benchmark | P&L live delta (JPY) | Capture delta (bp) |")
        lines.append("|---|---|---|")
        for bench, delta in stratum.get("benchmark_deltas", {}).items():
            lines.append(
                f"| {bench} | {_fmt_jpy(delta.get('pnl_jpy_live_delta'))} "
                f"| {_fmt_bp(delta.get('capture_bp_delta'))} |"
            )
        lines.append("")

    gate = report.get("gate")
    if gate is not None:
        cohort = gate["cohort"]
        lines.append(
            f"## Acceptance gate (execution_version={gate['execution_version']}, "
            "cumulative live cohort)"
        )
        lines.append("")
        lines.append(
            f"Cohort: {cohort['first_as_of_jst'] or '-'} to {cohort['last_as_of_jst'] or '-'}, "
            f"{cohort['trade_count']} ugh_x1 trades, {cohort['observation_days']} windows, "
            f"{_fmt_count(cohort['observation_calendar_days'])} calendar days, "
            f"{cohort['excluded_days']} excluded days"
        )
        lines.append("")
        lines.extend(_gate_table(gate))
        lines.append("")
        lines.append(f"Passed: {_met(gate['passed'])}")
        blocked = ", ".join(gate["blocked_reasons"]) or "none"
        lines.append(f"Blocked reasons: {blocked}")
        lines.append("")

    inventory = report.get("inventory")
    if inventory is not None:
        lines.append("## Archive inventory (blocking)")
        lines.append("")
        lines.extend(_inventory_lines(inventory))
        lines.append("")
        lines.append("### Archive defects (report only, never block)")
        lines.append("")
        lines.extend(_inventory_lines(inventory["archive_defects"]))
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- Generated from persisted execution_evaluation.csv archives only.")
    lines.append("- Live series: entry_status == live rows; bar series: every row incl. backfill.")
    lines.append(
        "- Gate cohort: current execution_version, live rows, complete batches, all history."
    )
    lines.append("")
    return "\n".join(lines)


def _book_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for version, stratum in report.get("strata", {}).items():
        for book_id, metrics in stratum.get("books", {}).items():
            row: dict[str, Any] = {"execution_version": version, "book_id": book_id}
            for name in EXECUTION_REPORT_BOOK_FIELDNAMES[2:]:
                value = metrics.get(name)
                row[name] = _fmt_skip_counts(value) if name == "skip_counts" else _blank(value)
            rows.append(row)
    return rows


def _write_json(report: dict[str, Any], path: str) -> str:
    """Write *report* as strict JSON: a stray datetime or a NaN raises instead of being coerced."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2, allow_nan=False)
        fh.write("\n")
    return os.path.abspath(path)


def export_execution_report_artifacts(
    report: dict[str, Any],
    csv_output_dir: str,
    scope: str,
    date_str: str,
) -> dict[str, str]:
    """Write ``analytics/execution/{scope}/{date_str}/execution_{scope}.{md,csv,json}``.

    *scope* is ``weekly`` or ``monthly``; *date_str* the ``YYYYMMDD`` / ``YYYYMM``
    label of the window (anything else raises ``ValueError``).  The layout mirrors
    ``weekly_report_exports.export_weekly_report_artifacts`` under
    *csv_output_dir* (the ``csv/`` root).  Nothing under ``latest/`` is
    touched here — see :func:`export_execution_latest_summary`.

    Returns a dict keyed ``execution_{scope}_md`` / ``_csv`` / ``_json`` with
    absolute paths.
    """
    if scope not in EXECUTION_REPORT_SCOPES:
        raise ValueError(
            f"invalid execution report scope {scope!r}: expected one of {EXECUTION_REPORT_SCOPES}"
        )
    if _DATE_STR_PATTERN.fullmatch(date_str) is None:
        raise ValueError(
            f"invalid execution report date_str {date_str!r}: expected YYYYMMDD or YYYYMM"
        )
    base = os.path.abspath(csv_output_dir)
    out_dir = os.path.join(base, "analytics", "execution", scope, date_str)
    os.makedirs(out_dir, exist_ok=True)
    stem = f"execution_{scope}"

    md_path = os.path.join(out_dir, f"{stem}.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(build_execution_report_md(report))
    csv_path = write_csv_rows(
        os.path.join(out_dir, f"{stem}.csv"),
        _book_rows(report),
        EXECUTION_REPORT_BOOK_FIELDNAMES,
    )
    json_path = _write_json(report, os.path.join(out_dir, f"{stem}.json"))
    return {
        f"{stem}_md": os.path.abspath(md_path),
        f"{stem}_csv": csv_path,
        f"{stem}_json": json_path,
    }


def export_execution_latest_summary(cumulative_report: dict[str, Any], csv_output_dir: str) -> str:
    """Write ``latest/execution_summary.json`` from a whole-history report and return its path.

    *cumulative_report* must come from ``run_execution_report(...,
    start_as_of_jst=None, end_as_of_jst=None, ...)``; a windowed report is
    refused so the latest summary never depends on the scope that ran last.
    """
    window = cumulative_report.get("window", {})
    if window.get("start_as_of_jst") is not None or window.get("end_as_of_jst") is not None:
        raise ValueError(
            "latest/execution_summary.json must be written from the cumulative report "
            f"(whole history), got window {window!r}"
        )
    base = os.path.abspath(csv_output_dir)
    return _write_json(cumulative_report, os.path.join(base, "latest", "execution_summary.json"))


__all__ = [
    "BLOCKED_DUPLICATE_BATCHES",
    "BLOCKED_INCOMPLETE_BATCHES",
    "BLOCKED_INCOMPLETE_DECISIONS",
    "BLOCKED_MISSING_DECISIONS",
    "BLOCKED_MISSING_EVALUATIONS",
    "BLOCKED_MISSING_LIVE",
    "EXECUTION_REPORT_BOOK_FIELDNAMES",
    "GATE_BLOCKED_REASONS",
    "GATE_MAX_DRAWDOWN",
    "GATE_MIN_CALENDAR_DAYS",
    "GATE_MIN_T_STAT",
    "EXECUTION_REPORT_SCOPES",
    "GATE_MIN_TRADE_COUNT",
    "CollectedExecutionEvaluations",
    "ExecutionDefectInventory",
    "IncompleteExecutionBatch",
    "MissingExecutionDecision",
    "MissingExecutionEvaluation",
    "build_execution_report_md",
    "collect_execution_evaluation_rows",
    "expected_decision_days",
    "export_execution_latest_summary",
    "export_execution_report_artifacts",
    "is_gate_blocking_defect",
    "run_execution_report",
]
