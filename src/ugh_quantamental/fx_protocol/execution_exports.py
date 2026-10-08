"""CSV exports for the FX Execution Layer v1 (spec §5 records, §7 Steps 5b / 6b).

Flattens already-built ``ExecutionDecision`` / ``ExecutionEvaluation`` rows to
CSV, publishes them into the ``history/`` + ``latest/`` layout shared with
``csv_exports`` (atomic copies, archived decisions never overwritten once
complete), and loads both files back into models — decisions for next-day
evaluation in automation Step 4c, evaluations for aggregation.  No execution
rule is recomputed here.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import contextlib
import csv
import os
import shutil
import tempfile
from collections.abc import Iterable
from datetime import datetime
from enum import Enum

from ugh_quantamental.fx_protocol.csv_exports import _blank, make_daily_csv_stem, write_csv_rows
from ugh_quantamental.fx_protocol.execution_models import (
    EXECUTION_BOOK_ORDER,
    BookId,
    ExecutionDecision,
    ExecutionEvaluation,
)
from ugh_quantamental.fx_protocol.models import ForecastDirection, StrategyKind

# ---------------------------------------------------------------------------
# Canonical column definitions (spec §5.1 / §5.2; same order as the model fields)
# ---------------------------------------------------------------------------

EXECUTION_FIELDNAMES: tuple[str, ...] = (
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
)

EXECUTION_EVALUATION_FIELDNAMES: tuple[str, ...] = (
    "execution_version",
    "book_id",
    "as_of_jst",
    "window_end_jst",
    "forecast_batch_id",
    "outcome_id",
    "side",
    "size",
    "skip_reason",
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
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _enum_value(v: Enum | None) -> object:
    """Return ``v.value``, or empty string if *v* is ``None`` (``_blank`` policy)."""
    return "" if v is None else v.value


def _opt_str(v: str) -> str | None:
    """Empty CSV cell → ``None``; any other cell unchanged."""
    return v if v != "" else None


def _opt_float(v: str) -> float | None:
    """Empty CSV cell → ``None``; any other cell parsed as ``float``."""
    return float(v) if v != "" else None


def _parse_bool(v: str) -> bool:
    """Parse a boolean cell as written by ``csv`` (``True`` / ``False``); strict."""
    lowered = v.strip().lower()
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    raise ValueError(f"invalid boolean cell {v!r}")


def _opt_bool(v: str) -> bool | None:
    """Empty CSV cell → ``None``; any other cell parsed as a strict boolean."""
    return _parse_bool(v) if v != "" else None


def _atomic_copy(src: str, dst: str) -> None:
    """Copy *src* to *dst* so that readers never observe a partially written file.

    The bytes go to a temporary file in *dst*'s directory first and are moved
    into place with ``os.replace`` (atomic when source and target share a
    filesystem, which a same-directory temp file guarantees).  A failure
    mid-copy leaves any existing *dst* untouched and removes the temp file.
    """
    dst_dir = os.path.dirname(dst)
    fd, tmp = tempfile.mkstemp(prefix=f".{os.path.basename(dst)}.", suffix=".tmp", dir=dst_dir)
    os.close(fd)
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


def _read_rows(path: str, fieldnames: tuple[str, ...], label: str) -> list[dict[str, str]]:
    """Read a CSV strictly, verifying the header carries every *fieldnames* column.

    ``strict=True`` so an archive truncated inside a quoted field raises rather
    than yielding a silently shortened value.  A row that is structurally short
    or long (what an interrupted copy leaves behind) does not raise even then,
    so those are rejected explicitly.

    Raises ``ValueError`` for a missing column, a malformed file or a malformed
    row, and ``OSError`` when the file cannot be opened.
    """
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, strict=True)
            present = tuple(reader.fieldnames or ())
            missing = [name for name in fieldnames if name not in present]
            if missing:
                raise ValueError(f"{label} CSV {path!r} is missing columns: {missing}")
            rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"{label} CSV {path!r} is malformed: {exc}") from exc

    for index, row in enumerate(rows, start=2):
        if None in row or None in row.values():
            raise ValueError(f"{label} CSV {path!r} has a malformed row at line {index}")
    return rows


def _covers_every_book_once(book_ids: Iterable[BookId]) -> bool:
    """True when *book_ids* is exactly ``EXECUTION_BOOK_ORDER`` as a multiset."""
    ids = tuple(book_ids)
    return len(ids) == len(EXECUTION_BOOK_ORDER) and set(ids) == set(EXECUTION_BOOK_ORDER)


# ---------------------------------------------------------------------------
# Row-flattening helpers
# ---------------------------------------------------------------------------


def decisions_to_rows(decisions: tuple[ExecutionDecision, ...]) -> list[dict[str, object]]:
    """Flatten ``ExecutionDecision`` objects to CSV-ready row dicts.

    Datetimes become ISO-8601 strings, enums their ``.value``, and ``None`` an
    empty string (the ``_blank`` convention shared with ``csv_exports``).
    Numbers are passed through unchanged so ``csv`` writes their ``repr``.
    Input order is preserved: ``build_execution_decisions`` already emits rows
    in ``EXECUTION_BOOK_ORDER``.
    """
    rows: list[dict[str, object]] = []
    for d in decisions:
        row: dict[str, object] = {
            "execution_version": d.execution_version,
            "book_id": d.book_id.value,
            "as_of_jst": d.as_of_jst.isoformat(),
            "window_end_jst": d.window_end_jst.isoformat(),
            "forecast_batch_id": d.forecast_batch_id,
            "source_strategy_kind": _enum_value(d.source_strategy_kind),
            "side": d.side,
            "size": d.size,
            "skip_reason": _blank(d.skip_reason),
            "entry_status": d.entry_status,
            "entry_price_live": _blank(d.entry_price_live),
            "entry_time_utc": d.entry_time_utc.isoformat(),
            "entry_vendor": _blank(d.entry_vendor),
            "entry_feed": _blank(d.entry_feed),
            "beta_direction": d.beta_direction.value,
            "consensus_up_count": d.consensus_up_count,
            "consensus_down_count": d.consensus_down_count,
            "technical_direction": d.technical_direction.value,
            "momentum_3d": d.momentum_3d,
            "trailing_mean_abs_close_change_bp": d.trailing_mean_abs_close_change_bp,
            "previous_close_change_bp": _blank(d.previous_close_change_bp),
        }
        rows.append(row)
    return rows


def evaluations_to_rows(evaluations: tuple[ExecutionEvaluation, ...]) -> list[dict[str, object]]:
    """Flatten ``ExecutionEvaluation`` objects to CSV-ready row dicts.

    Same conventions as ``decisions_to_rows``.  ``hit`` is passed through as a
    Python bool (written ``True`` / ``False`` by ``csv``, exactly like
    ``csv_exports.evaluation_records_to_rows`` does for ``direction_hit``) or
    an empty string when ``None`` (``side == 0`` rows).  ``pnl_live_bp`` and
    ``cost_live_bp`` are blank on rows without a live entry price.
    """
    rows: list[dict[str, object]] = []
    for ev in evaluations:
        row: dict[str, object] = {
            "execution_version": ev.execution_version,
            "book_id": ev.book_id.value,
            "as_of_jst": ev.as_of_jst.isoformat(),
            "window_end_jst": ev.window_end_jst.isoformat(),
            "forecast_batch_id": ev.forecast_batch_id,
            "outcome_id": ev.outcome_id,
            "side": ev.side,
            "size": ev.size,
            "skip_reason": _blank(ev.skip_reason),
            "entry_status": ev.entry_status,
            "entry_price_live": _blank(ev.entry_price_live),
            "realized_open": ev.realized_open,
            "realized_close": ev.realized_close,
            "pnl_live_bp": _blank(ev.pnl_live_bp),
            "pnl_bar_bp": ev.pnl_bar_bp,
            "cost_live_bp": _blank(ev.cost_live_bp),
            "cost_bar_bp": ev.cost_bar_bp,
            "hit": _blank(ev.hit),
            "evaluated_at_utc": ev.evaluated_at_utc.isoformat(),
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# High-level export functions
# ---------------------------------------------------------------------------


def export_execution_csv(
    decisions: tuple[ExecutionDecision, ...],
    as_of_jst: datetime,
    pair: str,
    csv_output_dir: str,
) -> str:
    """Write the daily execution-decision CSV and return its absolute path.

    File path: ``{csv_output_dir}/execution/{pair}_{YYYYMMDD}_execution.csv``
    (``YYYYMMDD`` from *as_of_jst* via ``make_daily_csv_stem``).  Existing
    files are overwritten (idempotent rerun policy of ``write_csv_rows``).
    """
    stem = make_daily_csv_stem(pair, as_of_jst)
    path = os.path.join(csv_output_dir, "execution", f"{stem}_execution.csv")
    rows = decisions_to_rows(decisions)
    return write_csv_rows(path, rows, EXECUTION_FIELDNAMES)


def export_execution_evaluation_csv(
    evaluations: tuple[ExecutionEvaluation, ...],
    as_of_jst: datetime,
    pair: str,
    csv_output_dir: str,
) -> str:
    """Write the execution-evaluation CSV and return its absolute path.

    File path:
    ``{csv_output_dir}/execution/{pair}_{YYYYMMDD}_execution_evaluation.csv``.
    *as_of_jst* is the **evaluated** window's ``as_of_jst`` (the batch the
    decisions consumed), not the evaluating run's date.
    """
    stem = make_daily_csv_stem(pair, as_of_jst)
    path = os.path.join(csv_output_dir, "execution", f"{stem}_execution_evaluation.csv")
    rows = evaluations_to_rows(evaluations)
    return write_csv_rows(path, rows, EXECUTION_EVALUATION_FIELDNAMES)


# ---------------------------------------------------------------------------
# CSV → model rehydration (automation Step 4c, aggregation)
# ---------------------------------------------------------------------------


def _parse_decision_row(row: dict[str, str]) -> ExecutionDecision:
    """Parse one ``execution.csv`` row back into an ``ExecutionDecision``.

    Inverse of ``decisions_to_rows``: empty cells become ``None`` for the
    optional columns; enums, ints, floats and datetimes are converted
    explicitly so the strict model receives already-typed values.
    """
    source_kind = row["source_strategy_kind"]
    return ExecutionDecision(
        execution_version=row["execution_version"],
        book_id=BookId(row["book_id"]),
        as_of_jst=datetime.fromisoformat(row["as_of_jst"]),
        window_end_jst=datetime.fromisoformat(row["window_end_jst"]),
        forecast_batch_id=row["forecast_batch_id"],
        source_strategy_kind=StrategyKind(source_kind) if source_kind != "" else None,
        side=int(row["side"]),
        size=float(row["size"]),
        skip_reason=_opt_str(row["skip_reason"]),  # validated against SkipReason by the model
        entry_status=row["entry_status"],  # validated against EntryStatus by the model
        entry_price_live=_opt_float(row["entry_price_live"]),
        entry_time_utc=datetime.fromisoformat(row["entry_time_utc"]),
        entry_vendor=_opt_str(row["entry_vendor"]),
        entry_feed=_opt_str(row["entry_feed"]),
        beta_direction=ForecastDirection(row["beta_direction"]),
        consensus_up_count=int(row["consensus_up_count"]),
        consensus_down_count=int(row["consensus_down_count"]),
        technical_direction=ForecastDirection(row["technical_direction"]),
        momentum_3d=float(row["momentum_3d"]),
        trailing_mean_abs_close_change_bp=float(row["trailing_mean_abs_close_change_bp"]),
        previous_close_change_bp=_opt_float(row["previous_close_change_bp"]),
    )


def load_execution_decisions_csv(path: str) -> tuple[ExecutionDecision, ...]:
    """Load an ``execution.csv`` written by ``export_execution_csv`` back into models.

    The round trip is exact for every field: ``repr`` floats, ISO-8601
    datetimes (offset preserved), enum values, and the ``_blank`` convention
    (empty cell ↔ ``None``).  Row order is kept.

    Raises
    ------
    ValueError
        When a required column is missing, a row is structurally short or long
        (an interrupted copy), the CSV is malformed, or a cell cannot be parsed
        (including a pydantic ``ValidationError``, which is a ``ValueError``).
    OSError
        When the file cannot be opened.
    """
    rows = _read_rows(path, EXECUTION_FIELDNAMES, "execution")
    return tuple(_parse_decision_row(row) for row in rows)


def _parse_evaluation_row(row: dict[str, str]) -> ExecutionEvaluation:
    """Parse one ``execution_evaluation.csv`` row back into an ``ExecutionEvaluation``.

    Inverse of ``evaluations_to_rows``; same conversion rules as
    ``_parse_decision_row``, plus strict ``True`` / ``False`` / blank parsing
    for ``hit``.
    """
    return ExecutionEvaluation(
        execution_version=row["execution_version"],
        book_id=BookId(row["book_id"]),
        as_of_jst=datetime.fromisoformat(row["as_of_jst"]),
        window_end_jst=datetime.fromisoformat(row["window_end_jst"]),
        forecast_batch_id=row["forecast_batch_id"],
        outcome_id=row["outcome_id"],
        side=int(row["side"]),
        size=float(row["size"]),
        skip_reason=_opt_str(row["skip_reason"]),  # validated against SkipReason by the model
        entry_status=row["entry_status"],  # validated against EntryStatus by the model
        entry_price_live=_opt_float(row["entry_price_live"]),
        realized_open=float(row["realized_open"]),
        realized_close=float(row["realized_close"]),
        pnl_live_bp=_opt_float(row["pnl_live_bp"]),
        pnl_bar_bp=float(row["pnl_bar_bp"]),
        cost_live_bp=_opt_float(row["cost_live_bp"]),
        cost_bar_bp=float(row["cost_bar_bp"]),
        hit=_opt_bool(row["hit"]),
        evaluated_at_utc=datetime.fromisoformat(row["evaluated_at_utc"]),
    )


def load_execution_evaluations_csv(path: str) -> tuple[ExecutionEvaluation, ...]:
    """Load an ``execution_evaluation.csv`` back into models; mirrors the decision loader.

    Same exactness guarantees and the same ``ValueError`` / ``OSError``
    contract as ``load_execution_decisions_csv``.
    """
    rows = _read_rows(path, EXECUTION_EVALUATION_FIELDNAMES, "execution evaluation")
    return tuple(_parse_evaluation_row(row) for row in rows)


# ---------------------------------------------------------------------------
# Completeness predicates
# ---------------------------------------------------------------------------


def is_complete_decision_file(path: str) -> bool:
    """Return ``True`` only when *path* holds exactly one decision row per ``BookId``.

    A missing file, a header-only file, a truncated or partial file, and any
    parse / validation error all yield ``False``.  This predicate never
    raises: it is the "already recorded" test behind ``publish_execution_csvs``
    and automation Step 3b, where any unreadable archive simply means the
    decisions still have to be written.
    """
    try:
        decisions = load_execution_decisions_csv(path)
    except Exception:  # predicate contract: whatever went wrong, the file is not complete
        return False
    return _covers_every_book_once(d.book_id for d in decisions)


def is_complete_evaluation_file(path: str) -> bool:
    """Return ``True`` only when *path* holds exactly one evaluation row per ``BookId``.

    Same contract as ``is_complete_decision_file`` (never raises); automation
    Step 4c re-evaluates any window whose archive is not complete.
    """
    try:
        evaluations = load_execution_evaluations_csv(path)
    except Exception:  # predicate contract: whatever went wrong, the file is not complete
        return False
    return _covers_every_book_once(ev.book_id for ev in evaluations)


# ---------------------------------------------------------------------------
# Layout publication
# ---------------------------------------------------------------------------


def sync_latest_execution_csv(csv_output_dir: str, history_execution_path: str) -> bool:
    """Make ``latest/execution.csv`` a byte-identical copy of a complete archive file.

    Used by automation Step 3b when the batch's ``history/.../execution.csv``
    is already complete: an earlier publish may have written the archive and
    then failed before (or while) refreshing ``latest/``, which would otherwise
    leave ``latest/execution.csv`` on an older batch forever.  Nothing is
    written when the bytes already match (so a plain same-day rerun leaves the
    file untouched), and the copy is atomic.

    Returns ``True`` when ``latest/execution.csv`` was (re)written.
    """
    latest_dir = os.path.join(os.path.abspath(csv_output_dir), "latest")
    latest_path = os.path.join(latest_dir, "execution.csv")
    with open(history_execution_path, "rb") as fh:
        archive_bytes = fh.read()
    if os.path.isfile(latest_path):
        with open(latest_path, "rb") as fh:
            if fh.read() == archive_bytes:
                return False
    os.makedirs(latest_dir, exist_ok=True)
    _atomic_copy(history_execution_path, latest_path)
    return True


def publish_execution_csvs(
    csv_output_dir: str,
    date_str: str,
    forecast_batch_id: str,
    decision_path: str | None,
    evaluation_path: str | None,
) -> dict[str, str | None]:
    """Copy execution CSVs into the ``history/`` + ``latest/`` layout (spec §7 5b / 6b).

    Layout written (only the parts whose path argument is not ``None``):

    - ``history/{date_str}/{forecast_batch_id}/execution.csv`` — written
      **only when no complete archive is present** (``is_complete_decision_file``).
      The decision rows are recorded once per batch by the run that built them
      (spec §3): a complete archive is left untouched and its path is still
      returned, while a header-only, truncated or partial one (an interrupted
      earlier publish) is replaced.
    - ``latest/execution.csv`` — copy of *decision_path*; overwritten on each
      publish that passes one.
    - ``history/{date_str}/{forecast_batch_id}/execution_evaluation.csv`` —
      copy of *evaluation_path*; overwrite allowed (evaluation is idempotent
      given the persisted outcome).  Nothing is written under ``latest/`` for
      evaluations.

    Every copy is atomic: the bytes land in a temp file in the target
    directory and are moved into place with ``os.replace``, so a reader (or a
    later completeness check) never sees a half-written file.  Directories are
    created as needed, mirroring ``csv_exports.publish_csv_to_history_only``.
    *date_str* is the batch's own ``as_of_jst`` date, so Step 4c evaluations
    land in the evaluated window's batch directory rather than the current
    run's.

    Returns a ``dict`` keyed ``history_execution`` /
    ``history_execution_evaluation`` / ``latest_execution`` whose values are
    paths **relative to** *csv_output_dir*, or ``None`` for skipped parts.
    """
    base = os.path.abspath(csv_output_dir)
    history_dir = os.path.join(base, "history", date_str, forecast_batch_id)
    os.makedirs(history_dir, exist_ok=True)

    result: dict[str, str | None] = {
        "history_execution": None,
        "history_execution_evaluation": None,
        "latest_execution": None,
    }

    if decision_path is not None:
        history_execution = os.path.join(history_dir, "execution.csv")
        if not is_complete_decision_file(history_execution):
            _atomic_copy(decision_path, history_execution)
        result["history_execution"] = f"history/{date_str}/{forecast_batch_id}/execution.csv"

        latest_dir = os.path.join(base, "latest")
        os.makedirs(latest_dir, exist_ok=True)
        _atomic_copy(decision_path, os.path.join(latest_dir, "execution.csv"))
        result["latest_execution"] = "latest/execution.csv"

    if evaluation_path is not None:
        _atomic_copy(evaluation_path, os.path.join(history_dir, "execution_evaluation.csv"))
        result["history_execution_evaluation"] = (
            f"history/{date_str}/{forecast_batch_id}/execution_evaluation.csv"
        )

    return result


__all__ = [
    "EXECUTION_EVALUATION_FIELDNAMES",
    "EXECUTION_FIELDNAMES",
    "decisions_to_rows",
    "evaluations_to_rows",
    "export_execution_csv",
    "export_execution_evaluation_csv",
    "is_complete_decision_file",
    "is_complete_evaluation_file",
    "load_execution_decisions_csv",
    "load_execution_evaluations_csv",
    "publish_execution_csvs",
    "sync_latest_execution_csv",
]
