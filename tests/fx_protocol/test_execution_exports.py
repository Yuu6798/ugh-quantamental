"""Tests for execution_exports.py — execution-layer CSV flattening, publishing and reloading.

No network calls; all file I/O goes through ``tmp_path``.
"""

from __future__ import annotations

import csv
import os
import shutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.execution_exports import (
    EXECUTION_EVALUATION_FIELDNAMES,
    EXECUTION_FIELDNAMES,
    decisions_to_rows,
    evaluations_to_rows,
    export_execution_csv,
    export_execution_evaluation_csv,
    is_complete_decision_file,
    is_complete_evaluation_file,
    load_execution_decisions_csv,
    load_execution_evaluations_csv,
    publish_execution_csvs,
)
from ugh_quantamental.fx_protocol.execution_models import (
    EXECUTION_BOOK_ORDER,
    BookId,
    ExecutionDecision,
    ExecutionEvaluation,
)
from ugh_quantamental.fx_protocol.models import ForecastDirection, StrategyKind

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc

_AS_OF = datetime(2026, 3, 17, 8, 0, 0, tzinfo=_JST)  # Tuesday
_WINDOW_END = datetime(2026, 3, 18, 8, 0, 0, tzinfo=_JST)
_BATCH_ID = "fb_test_batch"
_OUTCOME_ID = "oc_test_outcome"
_ENTRY_TIME = datetime(2026, 3, 17, 11, 30, 15, 123456, tzinfo=_UTC)
_EVALUATED_AT = datetime(2026, 3, 18, 0, 5, 0, tzinfo=_UTC)
_DATE_STR = "20260317"

# Pinned literally: spec §5.1 / §5.2 column order is a persisted-CSV contract.
_EXPECTED_EXECUTION_FIELDNAMES = (
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
_EXPECTED_EVALUATION_FIELDNAMES = (
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
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _decision(book_id: BookId, **overrides: object) -> ExecutionDecision:
    """One live-entry decision row; *overrides* tweak the per-book fields."""
    fields: dict[str, object] = {
        "execution_version": "x1",
        "book_id": book_id,
        "as_of_jst": _AS_OF,
        "window_end_jst": _WINDOW_END,
        "forecast_batch_id": _BATCH_ID,
        "source_strategy_kind": StrategyKind.ugh_v2_beta,
        "side": 1,
        "size": 1.0,
        "skip_reason": None,
        "entry_status": "live",
        "entry_price_live": 150.25,
        "entry_time_utc": _ENTRY_TIME,
        "entry_vendor": "yahoo_finance",
        "entry_feed": "chart/USDJPY=X",
        "beta_direction": ForecastDirection.up,
        "consensus_up_count": 2,
        "consensus_down_count": 1,
        "technical_direction": ForecastDirection.up,
        "momentum_3d": 0.42,
        "trailing_mean_abs_close_change_bp": 45.5,
        "previous_close_change_bp": 12.5,
    }
    fields.update(overrides)
    return ExecutionDecision(**fields)


_UNAVAILABLE: dict[str, object] = {
    "entry_status": "live_unavailable",
    "entry_price_live": None,
    "entry_vendor": None,
    "entry_feed": None,
    "previous_close_change_bp": None,
}


def _live_decisions() -> tuple[ExecutionDecision, ...]:
    """Six rows in ``EXECUTION_BOOK_ORDER`` with a live entry: trades, skips and bench books."""
    return (
        _decision(BookId.ugh_x1, size=0.5),
        _decision(BookId.ugh_beta_unit),
        _decision(BookId.ugh_consensus, side=0, size=0.0, skip_reason="no_consensus"),
        _decision(BookId.ugh_divergence, side=0, size=0.0, skip_reason="agree_with_technical"),
        _decision(BookId.bench_gpt_m3, source_strategy_kind=None),
        _decision(BookId.bench_long, source_strategy_kind=None),
    )


def _unavailable_decisions() -> tuple[ExecutionDecision, ...]:
    """The same six books on a day the live spot could not be fetched (optional columns None)."""
    return (
        _decision(BookId.ugh_x1, size=0.5, **_UNAVAILABLE),
        _decision(BookId.ugh_beta_unit, **_UNAVAILABLE),
        _decision(
            BookId.ugh_consensus, side=0, size=0.0, skip_reason="no_consensus", **_UNAVAILABLE
        ),
        _decision(
            BookId.ugh_divergence,
            side=0,
            size=0.0,
            skip_reason="agree_with_technical",
            **_UNAVAILABLE,
        ),
        _decision(BookId.bench_gpt_m3, source_strategy_kind=None, **_UNAVAILABLE),
        _decision(BookId.bench_long, source_strategy_kind=None, **_UNAVAILABLE),
    )


def _evaluation(book_id: BookId, **overrides: object) -> ExecutionEvaluation:
    """One live-entry evaluation row; *overrides* tweak the per-book fields."""
    fields: dict[str, object] = {
        "execution_version": "x1",
        "book_id": book_id,
        "as_of_jst": _AS_OF,
        "window_end_jst": _WINDOW_END,
        "forecast_batch_id": _BATCH_ID,
        "outcome_id": _OUTCOME_ID,
        "side": 1,
        "size": 1.0,
        "entry_status": "live",
        "entry_price_live": 150.25,
        "realized_open": 150.1,
        "realized_close": 150.4,
        "pnl_live_bp": 9.98,
        "pnl_bar_bp": 19.99,
        "cost_live_bp": 0.6656,
        "cost_bar_bp": 0.6662,
        "hit": True,
        "evaluated_at_utc": _EVALUATED_AT,
    }
    fields.update(overrides)
    return ExecutionEvaluation(**fields)


_SKIPPED: dict[str, object] = {
    "side": 0,
    "size": 0.0,
    "pnl_live_bp": 0.0,
    "pnl_bar_bp": 0.0,
    "cost_live_bp": 0.0,
    "cost_bar_bp": 0.0,
    "hit": None,
}


def _evaluations() -> tuple[ExecutionEvaluation, ...]:
    """Six evaluation rows: winners, two skipped books (hit None) and a losing short."""
    return (
        _evaluation(BookId.ugh_x1, size=0.5),
        _evaluation(BookId.ugh_beta_unit),
        _evaluation(BookId.ugh_consensus, **_SKIPPED),
        _evaluation(BookId.ugh_divergence, **_SKIPPED),
        _evaluation(BookId.bench_gpt_m3, side=-1, pnl_live_bp=-9.98, pnl_bar_bp=-19.99, hit=False),
        _evaluation(BookId.bench_long),
    )


def _unavailable_evaluation() -> ExecutionEvaluation:
    """A row evaluated without a live entry: every live-series column is ``None``."""
    return _evaluation(
        BookId.ugh_x1,
        entry_status="live_unavailable",
        entry_price_live=None,
        pnl_live_bp=None,
        cost_live_bp=None,
    )


def _read_csv(path: str) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def _write_text(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _decision_csv(tmp_path, name: str, decisions: tuple[ExecutionDecision, ...]) -> str:
    """Export *decisions* under a scratch dir *name* (so several sources can coexist)."""
    return export_execution_csv(decisions, _AS_OF, "USDJPY", os.path.join(str(tmp_path), name))


def _evaluation_csv(tmp_path, name: str, evaluations: tuple[ExecutionEvaluation, ...]) -> str:
    return export_execution_evaluation_csv(
        evaluations, _AS_OF, "USDJPY", os.path.join(str(tmp_path), name)
    )


def _history_path(out: str, name: str) -> str:
    return os.path.join(out, "history", _DATE_STR, _BATCH_ID, name)


def _plant(path: str, src: str) -> str:
    """Place a pre-existing archive at *path* by copying *src* (directories created)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.copy2(src, path)
    return path


# ---------------------------------------------------------------------------
# Fieldnames
# ---------------------------------------------------------------------------


class TestFieldnames:
    def test_execution_fieldnames_pinned(self) -> None:
        assert EXECUTION_FIELDNAMES == _EXPECTED_EXECUTION_FIELDNAMES

    def test_execution_evaluation_fieldnames_pinned(self) -> None:
        assert EXECUTION_EVALUATION_FIELDNAMES == _EXPECTED_EVALUATION_FIELDNAMES

    def test_execution_fieldnames_match_model_field_order(self) -> None:
        assert EXECUTION_FIELDNAMES == tuple(ExecutionDecision.model_fields)

    def test_execution_evaluation_fieldnames_match_model_field_order(self) -> None:
        assert EXECUTION_EVALUATION_FIELDNAMES == tuple(ExecutionEvaluation.model_fields)

    def test_fieldnames_are_unique(self) -> None:
        assert len(set(EXECUTION_FIELDNAMES)) == len(EXECUTION_FIELDNAMES)
        assert len(set(EXECUTION_EVALUATION_FIELDNAMES)) == len(EXECUTION_EVALUATION_FIELDNAMES)


# ---------------------------------------------------------------------------
# decisions_to_rows
# ---------------------------------------------------------------------------


class TestDecisionsToRows:
    def test_one_row_per_decision_in_input_order(self) -> None:
        rows = decisions_to_rows(_live_decisions())
        assert len(rows) == 6
        assert [r["book_id"] for r in rows] == [b.value for b in EXECUTION_BOOK_ORDER]

    def test_keys_match_fieldnames_in_order(self) -> None:
        for row in decisions_to_rows(_live_decisions()):
            assert tuple(row.keys()) == EXECUTION_FIELDNAMES

    def test_enums_serialised_as_values(self) -> None:
        row = decisions_to_rows(_live_decisions())[0]
        assert row["book_id"] == "ugh_x1"
        assert row["source_strategy_kind"] == "ugh_v2_beta"
        assert row["beta_direction"] == "up"
        assert row["technical_direction"] == "up"
        assert all(isinstance(row[k], str) for k in ("book_id", "beta_direction"))

    def test_datetimes_isoformat(self) -> None:
        row = decisions_to_rows(_live_decisions())[0]
        assert row["as_of_jst"] == "2026-03-17T08:00:00+09:00"
        assert row["window_end_jst"] == "2026-03-18T08:00:00+09:00"
        assert row["entry_time_utc"] == "2026-03-17T11:30:15.123456+00:00"

    def test_none_becomes_blank(self) -> None:
        rows = decisions_to_rows(_unavailable_decisions())
        ugh_x1, bench_long = rows[0], rows[-1]
        for key in ("entry_price_live", "entry_vendor", "entry_feed", "previous_close_change_bp"):
            assert ugh_x1[key] == ""
        assert ugh_x1["skip_reason"] == ""
        assert bench_long["source_strategy_kind"] == ""
        assert ugh_x1["entry_status"] == "live_unavailable"

    def test_present_optionals_pass_through(self) -> None:
        rows = decisions_to_rows(_live_decisions())
        assert rows[0]["entry_price_live"] == 150.25
        assert rows[0]["previous_close_change_bp"] == 12.5
        assert rows[0]["entry_vendor"] == "yahoo_finance"
        assert rows[0]["entry_feed"] == "chart/USDJPY=X"
        assert rows[2]["skip_reason"] == "no_consensus"
        assert rows[3]["skip_reason"] == "agree_with_technical"

    def test_numeric_values_preserved(self) -> None:
        row = decisions_to_rows(_live_decisions())[0]
        assert row["side"] == 1 and isinstance(row["side"], int)
        assert row["size"] == 0.5 and isinstance(row["size"], float)
        assert row["consensus_up_count"] == 2
        assert row["consensus_down_count"] == 1
        assert row["momentum_3d"] == 0.42
        assert row["trailing_mean_abs_close_change_bp"] == 45.5
        assert row["execution_version"] == "x1"
        assert row["forecast_batch_id"] == _BATCH_ID

    def test_empty_input_gives_empty_list(self) -> None:
        assert decisions_to_rows(()) == []


# ---------------------------------------------------------------------------
# evaluations_to_rows
# ---------------------------------------------------------------------------


class TestEvaluationsToRows:
    def test_one_row_per_evaluation_in_input_order(self) -> None:
        rows = evaluations_to_rows(_evaluations())
        assert len(rows) == 6
        assert [r["book_id"] for r in rows] == [b.value for b in EXECUTION_BOOK_ORDER]

    def test_keys_match_fieldnames_in_order(self) -> None:
        for row in evaluations_to_rows(_evaluations()):
            assert tuple(row.keys()) == EXECUTION_EVALUATION_FIELDNAMES

    def test_hit_bool_passthrough_and_none_blank(self) -> None:
        rows = evaluations_to_rows(_evaluations())
        assert rows[0]["hit"] is True
        assert rows[4]["hit"] is False
        assert rows[2]["hit"] == ""
        assert rows[3]["hit"] == ""

    def test_live_series_columns_blank_when_live_unavailable(self) -> None:
        row = evaluations_to_rows((_unavailable_evaluation(),))[0]
        assert row["entry_status"] == "live_unavailable"
        assert row["entry_price_live"] == ""
        assert row["pnl_live_bp"] == ""
        assert row["cost_live_bp"] == ""
        assert row["pnl_bar_bp"] == 19.99
        assert row["cost_bar_bp"] == 0.6662

    def test_skipped_rows_keep_zero_costs(self) -> None:
        row = evaluations_to_rows(_evaluations())[2]
        assert row["side"] == 0
        assert row["size"] == 0.0
        assert row["cost_live_bp"] == 0.0
        assert row["cost_bar_bp"] == 0.0
        assert row["pnl_live_bp"] == 0.0
        assert row["pnl_bar_bp"] == 0.0

    def test_enum_datetime_and_scalars(self) -> None:
        row = evaluations_to_rows(_evaluations())[4]
        assert row["book_id"] == "bench_gpt_m3"
        assert row["as_of_jst"] == "2026-03-17T08:00:00+09:00"
        assert row["window_end_jst"] == "2026-03-18T08:00:00+09:00"
        assert row["evaluated_at_utc"] == "2026-03-18T00:05:00+00:00"
        assert row["outcome_id"] == _OUTCOME_ID
        assert row["side"] == -1
        assert row["size"] == 1.0
        assert row["entry_price_live"] == 150.25
        assert row["realized_open"] == 150.1
        assert row["realized_close"] == 150.4
        assert row["pnl_live_bp"] == -9.98
        assert row["pnl_bar_bp"] == -19.99
        assert row["cost_live_bp"] == 0.6656
        assert row["cost_bar_bp"] == 0.6662

    def test_empty_input_gives_empty_list(self) -> None:
        assert evaluations_to_rows(()) == []


# ---------------------------------------------------------------------------
# export_execution_csv / export_execution_evaluation_csv
# ---------------------------------------------------------------------------


class TestExportExecutionCsv:
    def test_path_pattern(self, tmp_path) -> None:
        out = str(tmp_path)
        path = export_execution_csv(_live_decisions(), _AS_OF, "USDJPY", out)
        assert path == os.path.join(
            os.path.abspath(out), "execution", "USDJPY_20260317_execution.csv"
        )
        assert os.path.isfile(path)

    def test_header_and_row_count(self, tmp_path) -> None:
        path = export_execution_csv(_live_decisions(), _AS_OF, "USDJPY", str(tmp_path))
        header, rows = _read_csv(path)
        assert tuple(header) == EXECUTION_FIELDNAMES
        assert len(rows) == 6
        assert [r["book_id"] for r in rows] == [b.value for b in EXECUTION_BOOK_ORDER]

    def test_blank_cells_for_none(self, tmp_path) -> None:
        path = export_execution_csv(_unavailable_decisions(), _AS_OF, "USDJPY", str(tmp_path))
        _, rows = _read_csv(path)
        assert rows[0]["entry_price_live"] == ""
        assert rows[0]["previous_close_change_bp"] == ""
        assert rows[-1]["source_strategy_kind"] == ""
        assert rows[0]["skip_reason"] == ""

    def test_rerun_overwrites_same_path(self, tmp_path) -> None:
        out = str(tmp_path)
        first = export_execution_csv(_live_decisions(), _AS_OF, "USDJPY", out)
        second = export_execution_csv(_live_decisions()[:1], _AS_OF, "USDJPY", out)
        assert first == second
        _, rows = _read_csv(second)
        assert len(rows) == 1

    def test_empty_tuple_writes_header_only(self, tmp_path) -> None:
        path = export_execution_csv((), _AS_OF, "USDJPY", str(tmp_path))
        header, rows = _read_csv(path)
        assert tuple(header) == EXECUTION_FIELDNAMES
        assert rows == []


class TestExportExecutionEvaluationCsv:
    def test_path_pattern(self, tmp_path) -> None:
        out = str(tmp_path)
        path = export_execution_evaluation_csv(_evaluations(), _AS_OF, "USDJPY", out)
        assert path == os.path.join(
            os.path.abspath(out), "execution", "USDJPY_20260317_execution_evaluation.csv"
        )
        assert os.path.isfile(path)

    def test_header_and_row_count(self, tmp_path) -> None:
        path = export_execution_evaluation_csv(_evaluations(), _AS_OF, "USDJPY", str(tmp_path))
        header, rows = _read_csv(path)
        assert tuple(header) == EXECUTION_EVALUATION_FIELDNAMES
        assert len(rows) == 6

    def test_bools_written_as_true_false_strings_and_none_blank(self, tmp_path) -> None:
        path = export_execution_evaluation_csv(_evaluations(), _AS_OF, "USDJPY", str(tmp_path))
        _, rows = _read_csv(path)
        assert rows[0]["hit"] == "True"
        assert rows[4]["hit"] == "False"
        assert rows[2]["hit"] == ""

    def test_live_series_cells_blank_when_unavailable(self, tmp_path) -> None:
        path = export_execution_evaluation_csv(
            (_unavailable_evaluation(),), _AS_OF, "USDJPY", str(tmp_path)
        )
        _, rows = _read_csv(path)
        assert rows[0]["pnl_live_bp"] == ""
        assert rows[0]["cost_live_bp"] == ""
        assert rows[0]["entry_price_live"] == ""
        assert rows[0]["pnl_bar_bp"] == "19.99"
        assert rows[0]["cost_bar_bp"] == "0.6662"

    def test_rerun_overwrites_same_path(self, tmp_path) -> None:
        out = str(tmp_path)
        first = export_execution_evaluation_csv(_evaluations(), _AS_OF, "USDJPY", out)
        second = export_execution_evaluation_csv(_evaluations()[:2], _AS_OF, "USDJPY", out)
        assert first == second
        _, rows = _read_csv(second)
        assert len(rows) == 2

    def test_decision_and_evaluation_files_coexist(self, tmp_path) -> None:
        out = str(tmp_path)
        dec = export_execution_csv(_live_decisions(), _AS_OF, "USDJPY", out)
        ev = export_execution_evaluation_csv(_evaluations(), _AS_OF, "USDJPY", out)
        assert dec != ev
        assert os.path.dirname(dec) == os.path.dirname(ev)


# ---------------------------------------------------------------------------
# publish_execution_csvs
# ---------------------------------------------------------------------------


class TestPublishExecutionCsvs:
    def test_decision_creates_history_and_latest(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        src = _decision_csv(tmp_path, "src", _live_decisions())

        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)

        assert _read_text(_history_path(out, "execution.csv")) == _read_text(src)
        assert _read_text(os.path.join(out, "latest", "execution.csv")) == _read_text(src)
        assert not os.path.exists(_history_path(out, "execution_evaluation.csv"))
        assert result == {
            "history_execution": f"history/{_DATE_STR}/{_BATCH_ID}/execution.csv",
            "history_execution_evaluation": None,
            "latest_execution": "latest/execution.csv",
        }

    def test_complete_history_execution_is_kept_latest_updated(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        first = _decision_csv(tmp_path, "first", _live_decisions())
        second = _decision_csv(tmp_path, "second", _unavailable_decisions())
        assert _read_text(first) != _read_text(second)

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, first, None)
        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, second, None)

        # The complete archived decision set is immutable (spec §3) ...
        assert _read_text(_history_path(out, "execution.csv")) == _read_text(first)
        # ... while latest/ follows the newest publish and the path is still reported.
        assert _read_text(os.path.join(out, "latest", "execution.csv")) == _read_text(second)
        assert result["history_execution"] == f"history/{_DATE_STR}/{_BATCH_ID}/execution.csv"
        assert result["latest_execution"] == "latest/execution.csv"

    def test_pre_existing_complete_archive_is_not_touched(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        archived = _plant(
            _history_path(out, "execution.csv"), _decision_csv(tmp_path, "a", _live_decisions())
        )
        src = _decision_csv(tmp_path, "b", _unavailable_decisions())
        mtime_before = os.stat(archived).st_mtime_ns
        content_before = _read_text(archived)

        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)

        assert _read_text(archived) == content_before
        assert os.stat(archived).st_mtime_ns == mtime_before
        assert result["history_execution"] == f"history/{_DATE_STR}/{_BATCH_ID}/execution.csv"

    def test_header_only_history_execution_is_replaced(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        _plant(_history_path(out, "execution.csv"), _decision_csv(tmp_path, "empty", ()))
        src = _decision_csv(tmp_path, "src", _live_decisions())

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)

        assert _read_text(_history_path(out, "execution.csv")) == _read_text(src)
        assert load_execution_decisions_csv(_history_path(out, "execution.csv")) == (
            _live_decisions()
        )

    def test_partial_history_execution_is_replaced(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        partial = _decision_csv(tmp_path, "partial", _live_decisions()[:3])
        _plant(_history_path(out, "execution.csv"), partial)
        src = _decision_csv(tmp_path, "src", _live_decisions())

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)

        _, rows = _read_csv(_history_path(out, "execution.csv"))
        assert len(rows) == 6
        assert _read_text(_history_path(out, "execution.csv")) == _read_text(src)

    def test_unparseable_history_execution_is_replaced(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        _write_text(_history_path(out, "execution.csv"), "book_id\nugh_x1\n")
        src = _decision_csv(tmp_path, "src", _live_decisions())

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)

        assert _read_text(_history_path(out, "execution.csv")) == _read_text(src)

    def test_evaluation_written_and_overwritten(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        first = _write_text(os.path.join(str(tmp_path), "src", "ev1.csv"), "hit\nTrue\n")
        second = _write_text(os.path.join(str(tmp_path), "src", "ev2.csv"), "hit\nFalse\n")

        result1 = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, None, first)
        assert _read_text(_history_path(out, "execution_evaluation.csv")) == "hit\nTrue\n"

        result2 = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, None, second)
        assert _read_text(_history_path(out, "execution_evaluation.csv")) == "hit\nFalse\n"

        expected = f"history/{_DATE_STR}/{_BATCH_ID}/execution_evaluation.csv"
        assert result1["history_execution_evaluation"] == expected
        assert result2["history_execution_evaluation"] == expected
        assert result2["history_execution"] is None
        assert result2["latest_execution"] is None

    def test_evaluation_only_publish_never_touches_latest(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        ev = _write_text(os.path.join(str(tmp_path), "src", "ev.csv"), "hit\nTrue\n")

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, None, ev)

        assert not os.path.exists(os.path.join(out, "latest"))
        assert not os.path.exists(_history_path(out, "execution.csv"))

    def test_both_paths_published_together(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        dec = _decision_csv(tmp_path, "src", _live_decisions())
        ev = _evaluation_csv(tmp_path, "src", _evaluations())

        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, dec, ev)

        assert result == {
            "history_execution": f"history/{_DATE_STR}/{_BATCH_ID}/execution.csv",
            "history_execution_evaluation": (
                f"history/{_DATE_STR}/{_BATCH_ID}/execution_evaluation.csv"
            ),
            "latest_execution": "latest/execution.csv",
        }
        for key, value in result.items():
            assert value is not None, key
            assert os.path.isfile(os.path.join(out, value))

    def test_none_arguments_skip_everything(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")

        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, None, None)

        assert result == {
            "history_execution": None,
            "history_execution_evaluation": None,
            "latest_execution": None,
        }
        assert not os.path.exists(_history_path(out, "execution.csv"))
        assert not os.path.exists(_history_path(out, "execution_evaluation.csv"))
        assert not os.path.exists(os.path.join(out, "latest"))

    def test_creates_missing_output_directories(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "nested", "csv")
        src = _decision_csv(tmp_path, "src", _live_decisions())
        assert not os.path.exists(out)

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)

        assert os.path.isfile(_history_path(out, "execution.csv"))
        assert os.path.isfile(os.path.join(out, "latest", "execution.csv"))

    def test_latest_execution_is_replaced_for_a_new_batch(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        day1 = _decision_csv(tmp_path, "d1", _live_decisions())
        day2 = _decision_csv(tmp_path, "d2", _unavailable_decisions())

        publish_execution_csvs(out, "20260317", "fb_day1", day1, None)
        publish_execution_csvs(out, "20260318", "fb_day2", day2, None)

        assert _read_text(os.path.join(out, "latest", "execution.csv")) == _read_text(day2)
        assert _read_text(
            os.path.join(out, "history", "20260317", "fb_day1", "execution.csv")
        ) == _read_text(day1)

    def test_no_temporary_files_left_behind(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        dec = _decision_csv(tmp_path, "src", _live_decisions())
        ev = _evaluation_csv(tmp_path, "src", _evaluations())

        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, dec, ev)
        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, dec, ev)

        history_dir = os.path.dirname(_history_path(out, "execution.csv"))
        assert sorted(os.listdir(history_dir)) == ["execution.csv", "execution_evaluation.csv"]
        assert os.listdir(os.path.join(out, "latest")) == ["execution.csv"]

    def test_failed_copy_leaves_destination_intact_and_no_temp_files(
        self, tmp_path, monkeypatch
    ) -> None:
        """A copy that dies half-way must neither corrupt the target nor leave a temp file."""
        out = os.path.join(str(tmp_path), "csv")
        first = _decision_csv(tmp_path, "first", _live_decisions())
        second = _decision_csv(tmp_path, "second", _unavailable_decisions())
        publish_execution_csvs(out, _DATE_STR, _BATCH_ID, first, None)
        latest = os.path.join(out, "latest", "execution.csv")

        def _half_copy_then_die(src: str, dst: str) -> str:
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write("book_id,partial")  # bytes land in the temp file, never in `latest`
            raise OSError("disk full")

        monkeypatch.setattr(shutil, "copy2", _half_copy_then_die)
        with pytest.raises(OSError, match="disk full"):
            publish_execution_csvs(out, _DATE_STR, _BATCH_ID, second, None)

        assert _read_text(latest) == _read_text(first)
        assert os.listdir(os.path.join(out, "latest")) == ["execution.csv"]
        assert _read_text(_history_path(out, "execution.csv")) == _read_text(first)


# ---------------------------------------------------------------------------
# is_complete_decision_file / is_complete_evaluation_file
# ---------------------------------------------------------------------------


class TestIsCompleteDecisionFile:
    def test_missing_file_is_incomplete(self, tmp_path) -> None:
        assert is_complete_decision_file(os.path.join(str(tmp_path), "nope.csv")) is False

    def test_directory_is_incomplete(self, tmp_path) -> None:
        assert is_complete_decision_file(str(tmp_path)) is False

    def test_zero_byte_file_is_incomplete(self, tmp_path) -> None:
        path = _write_text(os.path.join(str(tmp_path), "execution.csv"), "")
        assert is_complete_decision_file(path) is False

    def test_header_only_file_is_incomplete(self, tmp_path) -> None:
        assert is_complete_decision_file(_decision_csv(tmp_path, "empty", ())) is False

    def test_partial_file_is_incomplete(self, tmp_path) -> None:
        partial = _decision_csv(tmp_path, "partial", _live_decisions()[:3])
        assert is_complete_decision_file(partial) is False

    @pytest.mark.parametrize(
        "make", [_live_decisions, _unavailable_decisions], ids=["live", "live_unavailable"]
    )
    def test_complete_file_is_complete(self, tmp_path, make) -> None:
        assert is_complete_decision_file(_decision_csv(tmp_path, "full", make())) is True

    def test_six_rows_with_a_duplicate_book_is_incomplete(self, tmp_path) -> None:
        rows = _live_decisions()[:5] + (_live_decisions()[0],)  # ugh_x1 twice, bench_long absent
        assert is_complete_decision_file(_decision_csv(tmp_path, "dup", rows)) is False

    def test_seven_rows_is_incomplete(self, tmp_path) -> None:
        rows = _live_decisions() + (_live_decisions()[0],)
        assert is_complete_decision_file(_decision_csv(tmp_path, "seven", rows)) is False

    def test_truncated_mid_row_is_incomplete(self, tmp_path) -> None:
        path = _decision_csv(tmp_path, "cut", _live_decisions())
        text = _read_text(path)
        _write_text(path, text[: len(text) - 40])
        assert is_complete_decision_file(path) is False

    def test_invalid_cell_is_incomplete(self, tmp_path) -> None:
        path = _decision_csv(tmp_path, "bad", _live_decisions())
        _write_text(path, _read_text(path).replace("bench_long", "bench_short"))
        assert is_complete_decision_file(path) is False

    def test_binary_garbage_never_raises(self, tmp_path) -> None:
        path = os.path.join(str(tmp_path), "execution.csv")
        with open(path, "wb") as fh:
            fh.write(b"\xff\xfe\x00garbage\n\x00")
        assert is_complete_decision_file(path) is False

    def test_published_archive_is_complete(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        src = _decision_csv(tmp_path, "src", _live_decisions())
        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, src, None)
        assert is_complete_decision_file(os.path.join(out, result["history_execution"])) is True
        assert is_complete_decision_file(os.path.join(out, result["latest_execution"])) is True


class TestIsCompleteEvaluationFile:
    def test_missing_file_is_incomplete(self, tmp_path) -> None:
        assert is_complete_evaluation_file(os.path.join(str(tmp_path), "nope.csv")) is False

    def test_header_only_file_is_incomplete(self, tmp_path) -> None:
        assert is_complete_evaluation_file(_evaluation_csv(tmp_path, "empty", ())) is False

    def test_partial_file_is_incomplete(self, tmp_path) -> None:
        partial = _evaluation_csv(tmp_path, "partial", _evaluations()[:3])
        assert is_complete_evaluation_file(partial) is False

    def test_complete_file_is_complete(self, tmp_path) -> None:
        assert (
            is_complete_evaluation_file(_evaluation_csv(tmp_path, "full", _evaluations())) is True
        )

    def test_decision_file_is_not_a_complete_evaluation_file(self, tmp_path) -> None:
        assert (
            is_complete_evaluation_file(_decision_csv(tmp_path, "dec", _live_decisions())) is False
        )

    def test_truncated_file_never_raises(self, tmp_path) -> None:
        path = _evaluation_csv(tmp_path, "cut", _evaluations())
        text = _read_text(path)
        _write_text(path, text[: len(text) - 30])
        assert is_complete_evaluation_file(path) is False

    def test_published_archive_is_complete(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        ev = _evaluation_csv(tmp_path, "src", _evaluations())
        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, None, ev)
        archived = os.path.join(out, result["history_execution_evaluation"])
        assert is_complete_evaluation_file(archived) is True


# ---------------------------------------------------------------------------
# load_execution_decisions_csv (CSV → model round trip)
# ---------------------------------------------------------------------------


class TestLoadExecutionDecisionsCsv:
    @pytest.mark.parametrize(
        "make", [_live_decisions, _unavailable_decisions], ids=["live", "live_unavailable"]
    )
    def test_round_trip_is_exact(self, tmp_path, make) -> None:
        decisions = make()
        path = export_execution_csv(decisions, _AS_OF, "USDJPY", str(tmp_path))

        loaded = load_execution_decisions_csv(path)

        assert loaded == decisions
        for got, want in zip(loaded, decisions, strict=True):
            assert got.model_dump() == want.model_dump()
            assert got.as_of_jst.isoformat() == want.as_of_jst.isoformat()
            assert got.window_end_jst.isoformat() == want.window_end_jst.isoformat()
            assert got.entry_time_utc.isoformat() == want.entry_time_utc.isoformat()
            assert got.entry_time_utc.microsecond == 123456

    def test_loaded_values_are_typed(self, tmp_path) -> None:
        path = export_execution_csv(_live_decisions(), _AS_OF, "USDJPY", str(tmp_path))
        loaded = load_execution_decisions_csv(path)

        first, consensus, bench = loaded[0], loaded[2], loaded[-1]
        assert isinstance(first.book_id, BookId) and first.book_id is BookId.ugh_x1
        assert isinstance(first.source_strategy_kind, StrategyKind)
        assert isinstance(first.beta_direction, ForecastDirection)
        assert isinstance(first.side, int) and first.side == 1
        assert isinstance(first.size, float) and first.size == 0.5
        assert isinstance(first.entry_price_live, float) and first.entry_price_live == 150.25
        assert first.skip_reason is None
        assert first.entry_status == "live"
        assert first.previous_close_change_bp == 12.5
        assert first.as_of_jst.tzinfo is not None
        assert first.entry_time_utc.tzinfo is not None
        assert consensus.side == 0 and consensus.size == 0.0
        assert consensus.skip_reason == "no_consensus"
        assert bench.source_strategy_kind is None

    def test_unavailable_optionals_load_as_none(self, tmp_path) -> None:
        path = export_execution_csv(_unavailable_decisions(), _AS_OF, "USDJPY", str(tmp_path))
        loaded = load_execution_decisions_csv(path)

        assert loaded[0].entry_status == "live_unavailable"
        assert loaded[0].entry_price_live is None
        assert loaded[0].entry_vendor is None
        assert loaded[0].entry_feed is None
        assert loaded[0].previous_close_change_bp is None

    def test_round_trip_through_published_history(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        decisions = _live_decisions()
        exported = _decision_csv(tmp_path, "src", decisions)
        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, exported, None)

        history_path = os.path.join(out, result["history_execution"])
        assert load_execution_decisions_csv(history_path) == decisions
        assert load_execution_decisions_csv(os.path.join(out, "latest", "execution.csv")) == (
            decisions
        )

    def test_header_only_file_returns_empty_tuple(self, tmp_path) -> None:
        path = export_execution_csv((), _AS_OF, "USDJPY", str(tmp_path))
        assert load_execution_decisions_csv(path) == ()

    def test_missing_column_raises_value_error(self, tmp_path) -> None:
        path = export_execution_csv(_live_decisions(), _AS_OF, "USDJPY", str(tmp_path))
        header, rows = _read_csv(path)
        truncated = header[:-1]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=truncated, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        with pytest.raises(ValueError, match="previous_close_change_bp"):
            load_execution_decisions_csv(path)

    def test_structurally_long_row_raises_value_error(self, tmp_path) -> None:
        path = export_execution_csv(_live_decisions()[:1], _AS_OF, "USDJPY", str(tmp_path))
        lines = _read_text(path).splitlines()
        lines[1] = lines[1] + ",extra"
        _write_text(path, "\n".join(lines) + "\n")

        with pytest.raises(ValueError, match="malformed row"):
            load_execution_decisions_csv(path)

    def test_structurally_short_row_raises_value_error(self, tmp_path) -> None:
        path = export_execution_csv(_live_decisions()[:1], _AS_OF, "USDJPY", str(tmp_path))
        lines = _read_text(path).splitlines()
        lines[1] = lines[1].rsplit(",", 2)[0]
        _write_text(path, "\n".join(lines) + "\n")

        with pytest.raises(ValueError, match="malformed row"):
            load_execution_decisions_csv(path)

    def test_unknown_enum_value_raises_value_error(self, tmp_path) -> None:
        path = export_execution_csv(_live_decisions()[:1], _AS_OF, "USDJPY", str(tmp_path))
        _write_text(path, _read_text(path).replace("ugh_x1", "ugh_x9"))

        with pytest.raises(ValueError):
            load_execution_decisions_csv(path)

    def test_missing_file_raises_oserror(self, tmp_path) -> None:
        with pytest.raises(OSError):
            load_execution_decisions_csv(os.path.join(str(tmp_path), "nope.csv"))


# ---------------------------------------------------------------------------
# load_execution_evaluations_csv (CSV → model round trip)
# ---------------------------------------------------------------------------


class TestLoadExecutionEvaluationsCsv:
    def test_round_trip_is_exact(self, tmp_path) -> None:
        evaluations = _evaluations()
        path = export_execution_evaluation_csv(evaluations, _AS_OF, "USDJPY", str(tmp_path))

        loaded = load_execution_evaluations_csv(path)

        assert loaded == evaluations
        for got, want in zip(loaded, evaluations, strict=True):
            assert got.model_dump() == want.model_dump()
            assert got.evaluated_at_utc.isoformat() == want.evaluated_at_utc.isoformat()

    def test_round_trip_without_live_entry(self, tmp_path) -> None:
        evaluations = (_unavailable_evaluation(),)
        path = export_execution_evaluation_csv(evaluations, _AS_OF, "USDJPY", str(tmp_path))

        loaded = load_execution_evaluations_csv(path)

        assert loaded == evaluations
        assert loaded[0].entry_price_live is None
        assert loaded[0].pnl_live_bp is None
        assert loaded[0].cost_live_bp is None
        assert loaded[0].cost_bar_bp == 0.6662

    def test_loaded_values_are_typed(self, tmp_path) -> None:
        path = export_execution_evaluation_csv(_evaluations(), _AS_OF, "USDJPY", str(tmp_path))
        loaded = load_execution_evaluations_csv(path)

        winner, skipped, short = loaded[0], loaded[2], loaded[4]
        assert isinstance(winner.book_id, BookId) and winner.book_id is BookId.ugh_x1
        assert winner.hit is True
        assert short.hit is False
        assert skipped.hit is None
        assert isinstance(winner.side, int) and short.side == -1
        assert isinstance(winner.size, float) and winner.size == 0.5
        assert winner.entry_status == "live"
        assert winner.outcome_id == _OUTCOME_ID
        assert winner.realized_open == 150.1 and winner.realized_close == 150.4
        assert winner.pnl_live_bp == 9.98 and winner.cost_live_bp == 0.6656
        assert skipped.cost_live_bp == 0.0 and skipped.cost_bar_bp == 0.0
        assert winner.evaluated_at_utc.tzinfo is not None

    def test_round_trip_through_published_history(self, tmp_path) -> None:
        out = os.path.join(str(tmp_path), "csv")
        evaluations = _evaluations()
        ev = _evaluation_csv(tmp_path, "src", evaluations)
        result = publish_execution_csvs(out, _DATE_STR, _BATCH_ID, None, ev)

        archived = os.path.join(out, result["history_execution_evaluation"])
        assert load_execution_evaluations_csv(archived) == evaluations

    def test_header_only_file_returns_empty_tuple(self, tmp_path) -> None:
        assert load_execution_evaluations_csv(_evaluation_csv(tmp_path, "empty", ())) == ()

    def test_missing_column_raises_value_error(self, tmp_path) -> None:
        path = _evaluation_csv(tmp_path, "src", _evaluations())
        header, rows = _read_csv(path)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=header[:-1], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        with pytest.raises(ValueError, match="evaluated_at_utc"):
            load_execution_evaluations_csv(path)

    def test_invalid_boolean_cell_raises_value_error(self, tmp_path) -> None:
        path = _evaluation_csv(tmp_path, "src", _evaluations()[:1])
        _write_text(path, _read_text(path).replace(",True,", ",maybe,"))

        with pytest.raises(ValueError, match="boolean"):
            load_execution_evaluations_csv(path)

    def test_structurally_short_row_raises_value_error(self, tmp_path) -> None:
        path = _evaluation_csv(tmp_path, "src", _evaluations()[:1])
        lines = _read_text(path).splitlines()
        lines[1] = lines[1].rsplit(",", 1)[0]
        _write_text(path, "\n".join(lines) + "\n")

        with pytest.raises(ValueError, match="malformed row"):
            load_execution_evaluations_csv(path)

    def test_missing_file_raises_oserror(self, tmp_path) -> None:
        with pytest.raises(OSError):
            load_execution_evaluations_csv(os.path.join(str(tmp_path), "nope.csv"))
