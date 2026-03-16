"""Tests for csv_exports.py — deterministic CSV flattening and file writing."""

from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.csv_exports import (
    EVALUATION_FIELDNAMES,
    FORECAST_FIELDNAMES,
    OUTCOME_FIELDNAMES,
    evaluation_records_to_rows,
    export_daily_evaluation_csv,
    export_daily_forecast_csv,
    export_daily_outcome_csv,
    forecast_records_to_rows,
    make_daily_csv_stem,
    outcome_record_to_rows,
    write_csv_rows,
)
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EvaluationRecord,
    EventTag,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test_vendor",
        feed_name="test_feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 16, 0, 0, 0, tzinfo=_UTC),
    )


def _ugh_forecast() -> ForecastRecord:
    from ugh_quantamental.fx_protocol.ids import make_forecast_id
    from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
    from ugh_quantamental.schemas.market_svp import StateProbabilities

    pair = CurrencyPair.USDJPY
    # Friday → next business day is Monday (2026-03-16)
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
    probs = StateProbabilities(
        dormant=0.05, setup=0.50, fire=0.20, expansion=0.10, exhaustion=0.10, failure=0.05
    )
    return ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of, "v1", StrategyKind.ugh),
        forecast_batch_id="fb_test_batch",
        pair=pair,
        strategy_kind=StrategyKind.ugh,
        as_of_jst=as_of,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=_UTC),
        market_data_provenance=_provenance(),
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=10.5,
        expected_range=ExpectedRange(low_price=149.0, high_price=151.5),
        dominant_state=LifecycleState.setup,
        state_probabilities=probs,
        q_dir=QuestionDirection.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.8,
        grv_raw=0.1,
        grv_lock=0.7,
        alignment=0.8,
        e_star=10.5,
        mismatch_px=0.2,
        mismatch_sem=0.1,
        conviction=0.7,
        urgency=0.6,
        input_snapshot_ref="ref/001",
        primary_question="Will USDJPY close higher?",
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _baseline_forecast(strategy_kind: StrategyKind) -> ForecastRecord:
    from ugh_quantamental.fx_protocol.ids import make_forecast_id

    pair = CurrencyPair.USDJPY
    as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
    window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
    if strategy_kind == StrategyKind.baseline_random_walk:
        direction = ForecastDirection.flat
        bp = 0.0
    else:
        direction = ForecastDirection.up
        bp = 5.0
    return ForecastRecord(
        forecast_id=make_forecast_id(pair, as_of, "v1", strategy_kind),
        forecast_batch_id="fb_test_batch",
        pair=pair,
        strategy_kind=strategy_kind,
        as_of_jst=as_of,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=_UTC),
        market_data_provenance=_provenance(),
        forecast_direction=direction,
        expected_close_change_bp=bp,
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _four_forecasts() -> tuple[ForecastRecord, ...]:
    return (
        _ugh_forecast(),
        _baseline_forecast(StrategyKind.baseline_random_walk),
        _baseline_forecast(StrategyKind.baseline_prev_day_direction),
        _baseline_forecast(StrategyKind.baseline_simple_technical),
    )


def _outcome_up() -> OutcomeRecord:
    from ugh_quantamental.fx_protocol.outcome_models import DailyOutcomeWorkflowRequest
    from ugh_quantamental.fx_protocol.outcomes import build_outcome_record

    # Matches the forecast window: Fri 2026-03-13 → Mon 2026-03-16
    return build_outcome_record(
        DailyOutcomeWorkflowRequest(
            pair=CurrencyPair.USDJPY,
            window_start_jst=datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST),
            window_end_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
            market_data_provenance=_provenance(),
            realized_open=150.0,
            realized_high=151.5,
            realized_low=149.5,
            realized_close=150.8,
            schema_version="v1",
            protocol_version="v1",
        )
    )


def _evaluation_ugh(outcome: OutcomeRecord) -> EvaluationRecord:
    from ugh_quantamental.fx_protocol.outcomes import build_evaluation_record

    return build_evaluation_record(
        _ugh_forecast(),
        outcome,
        evaluated_at_utc=datetime(2026, 3, 14, 1, 0, 0, tzinfo=_UTC),
        realized_state_proxy=None,
    )


def _evaluation_baseline(outcome: OutcomeRecord, sk: StrategyKind) -> EvaluationRecord:
    from ugh_quantamental.fx_protocol.outcomes import build_evaluation_record

    return build_evaluation_record(
        _baseline_forecast(sk),
        outcome,
        evaluated_at_utc=datetime(2026, 3, 14, 1, 0, 0, tzinfo=_UTC),
        realized_state_proxy=None,
    )


def _four_evaluations() -> tuple[EvaluationRecord, ...]:
    outcome = _outcome_up()
    return (
        _evaluation_ugh(outcome),
        _evaluation_baseline(outcome, StrategyKind.baseline_random_walk),
        _evaluation_baseline(outcome, StrategyKind.baseline_prev_day_direction),
        _evaluation_baseline(outcome, StrategyKind.baseline_simple_technical),
    )


# ---------------------------------------------------------------------------
# make_daily_csv_stem
# ---------------------------------------------------------------------------


class TestMakeDailyCsvStem:
    def test_basic_date(self) -> None:
        dt = datetime(2026, 3, 16, 8, 0, 0)
        assert make_daily_csv_stem("USDJPY", dt) == "USDJPY_20260316"

    def test_aware_datetime(self) -> None:
        dt = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
        assert make_daily_csv_stem("USDJPY", dt) == "USDJPY_20260316"

    def test_zero_pad(self) -> None:
        dt = datetime(2026, 1, 5, 8, 0, 0)
        assert make_daily_csv_stem("USDJPY", dt) == "USDJPY_20260105"

    def test_pair_in_stem(self) -> None:
        dt = datetime(2026, 3, 16, 8, 0, 0)
        stem = make_daily_csv_stem("EURJPY", dt)
        assert stem.startswith("EURJPY_")


# ---------------------------------------------------------------------------
# forecast_records_to_rows
# ---------------------------------------------------------------------------


class TestForecastRecordsToRows:
    def test_four_rows_for_batch(self) -> None:
        rows = forecast_records_to_rows(_four_forecasts())
        assert len(rows) == 4

    def test_column_names_match_fieldnames(self) -> None:
        rows = forecast_records_to_rows(_four_forecasts())
        for row in rows:
            assert set(row.keys()) == set(FORECAST_FIELDNAMES)

    def test_ugh_row_has_state_probabilities(self) -> None:
        ugh = _ugh_forecast()
        rows = forecast_records_to_rows((ugh,))
        row = rows[0]
        assert row["prob_setup"] == 0.50
        assert row["prob_dormant"] == 0.05
        assert row["dominant_state"] == "setup"

    def test_baseline_row_has_blank_ugh_fields(self) -> None:
        bl = _baseline_forecast(StrategyKind.baseline_random_walk)
        rows = forecast_records_to_rows((bl,))
        row = rows[0]
        assert row["prob_setup"] == ""
        assert row["dominant_state"] == ""
        assert row["alignment"] == ""
        assert row["conviction"] == ""

    def test_expected_range_flattened(self) -> None:
        ugh = _ugh_forecast()
        rows = forecast_records_to_rows((ugh,))
        row = rows[0]
        assert row["expected_range_low"] == 149.0
        assert row["expected_range_high"] == 151.5

    def test_baseline_range_blank(self) -> None:
        bl = _baseline_forecast(StrategyKind.baseline_simple_technical)
        rows = forecast_records_to_rows((bl,))
        row = rows[0]
        assert row["expected_range_low"] == ""
        assert row["expected_range_high"] == ""

    def test_provenance_flattened(self) -> None:
        rows = forecast_records_to_rows((_ugh_forecast(),))
        row = rows[0]
        assert row["market_data_vendor"] == "test_vendor"
        assert row["market_data_feed_name"] == "test_feed"
        assert row["market_data_price_type"] == "mid"
        assert row["market_data_resolution"] == "1d"
        assert row["market_data_timezone"] == "Asia/Tokyo"

    def test_disconfirmer_rule_count_zero(self) -> None:
        rows = forecast_records_to_rows((_ugh_forecast(),))
        assert rows[0]["disconfirmer_rule_count"] == 0

    def test_rows_ordered_by_forecast_id(self) -> None:
        forecasts = _four_forecasts()
        rows = forecast_records_to_rows(forecasts)
        ids = [r["forecast_id"] for r in rows]
        assert ids == sorted(ids)

    def test_column_order_matches_fieldnames(self) -> None:
        rows = forecast_records_to_rows((_ugh_forecast(),))
        assert list(rows[0].keys()) == list(FORECAST_FIELDNAMES)


# ---------------------------------------------------------------------------
# outcome_record_to_rows
# ---------------------------------------------------------------------------


class TestOutcomeRecordToRows:
    def test_single_row(self) -> None:
        rows = outcome_record_to_rows(_outcome_up())
        assert len(rows) == 1

    def test_column_names_match_fieldnames(self) -> None:
        rows = outcome_record_to_rows(_outcome_up())
        assert set(rows[0].keys()) == set(OUTCOME_FIELDNAMES)

    def test_realized_fields_present(self) -> None:
        row = outcome_record_to_rows(_outcome_up())[0]
        assert row["realized_open"] == 150.0
        assert row["realized_close"] == 150.8
        assert row["realized_direction"] == "up"

    def test_event_tags_blank_when_empty(self) -> None:
        row = outcome_record_to_rows(_outcome_up())[0]
        assert row["event_tags"] == ""

    def test_event_tags_pipe_joined(self) -> None:
        from ugh_quantamental.fx_protocol.outcome_models import DailyOutcomeWorkflowRequest
        from ugh_quantamental.fx_protocol.outcomes import build_outcome_record

        outcome = build_outcome_record(
            DailyOutcomeWorkflowRequest(
                pair=CurrencyPair.USDJPY,
                window_start_jst=datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST),
                window_end_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
                market_data_provenance=_provenance(),
                realized_open=150.0,
                realized_high=151.5,
                realized_low=149.5,
                realized_close=150.8,
                schema_version="v1",
                protocol_version="v1",
                event_tags=(EventTag.fomc, EventTag.boj),
            )
        )
        row = outcome_record_to_rows(outcome)[0]
        tags = row["event_tags"]
        assert isinstance(tags, str)
        assert "fomc" in tags
        assert "boj" in tags
        assert "|" in tags

    def test_column_order_matches_fieldnames(self) -> None:
        rows = outcome_record_to_rows(_outcome_up())
        assert list(rows[0].keys()) == list(OUTCOME_FIELDNAMES)


# ---------------------------------------------------------------------------
# evaluation_records_to_rows
# ---------------------------------------------------------------------------


class TestEvaluationRecordsToRows:
    def test_four_rows(self) -> None:
        rows = evaluation_records_to_rows(_four_evaluations())
        assert len(rows) == 4

    def test_column_names_match_fieldnames(self) -> None:
        rows = evaluation_records_to_rows(_four_evaluations())
        for row in rows:
            assert set(row.keys()) == set(EVALUATION_FIELDNAMES)

    def test_direction_hit_present(self) -> None:
        rows = evaluation_records_to_rows(_four_evaluations())
        for row in rows:
            assert isinstance(row["direction_hit"], bool)

    def test_baseline_ugh_only_fields_blank(self) -> None:
        outcome = _outcome_up()
        bl = _baseline_forecast(StrategyKind.baseline_random_walk)
        from ugh_quantamental.fx_protocol.outcomes import build_evaluation_record

        ev = build_evaluation_record(
            bl,
            outcome,
            evaluated_at_utc=datetime(2026, 3, 14, 1, 0, 0, tzinfo=_UTC),
            realized_state_proxy=None,
        )
        rows = evaluation_records_to_rows((ev,))
        row = rows[0]
        assert row["state_proxy_hit"] == ""
        assert row["mismatch_change_bp"] == ""
        assert row["realized_state_proxy"] == ""
        assert row["actual_state_change"] == ""

    def test_disconfirmers_hit_blank_when_empty(self) -> None:
        rows = evaluation_records_to_rows(_four_evaluations())
        for row in rows:
            assert row["disconfirmers_hit"] == ""

    def test_rows_ordered_by_evaluation_id(self) -> None:
        rows = evaluation_records_to_rows(_four_evaluations())
        ids = [r["evaluation_id"] for r in rows]
        assert ids == sorted(ids)

    def test_column_order_matches_fieldnames(self) -> None:
        rows = evaluation_records_to_rows(_four_evaluations())
        assert list(rows[0].keys()) == list(EVALUATION_FIELDNAMES)


# ---------------------------------------------------------------------------
# write_csv_rows
# ---------------------------------------------------------------------------


class TestWriteCsvRows:
    def test_writes_header_and_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "test.csv")
            rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
            returned = write_csv_rows(path, rows, ("a", "b"))
            assert os.path.abspath(path) == returned
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                data = list(reader)
            assert data[0]["a"] == "1"
            assert data[1]["b"] == "4"

    def test_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "deep", "nested", "file.csv")
            write_csv_rows(path, [{"x": 1}], ("x",))
            assert os.path.isfile(path)

    def test_overwrite_on_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "file.csv")
            write_csv_rows(path, [{"col": "first"}], ("col",))
            write_csv_rows(path, [{"col": "second"}], ("col",))
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                data = list(reader)
            assert len(data) == 1
            assert data[0]["col"] == "second"

    def test_returns_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "file.csv")
            result = write_csv_rows(path, [{"col": 1}], ("col",))
            assert os.path.isabs(result)


# ---------------------------------------------------------------------------
# export_daily_forecast_csv
# ---------------------------------------------------------------------------


class TestExportDailyForecastCsv:
    def test_writes_four_row_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_forecast_csv(_four_forecasts(), as_of, "USDJPY", tmpdir)
            assert os.path.isfile(path)
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                data = list(reader)
            assert len(data) == 4

    def test_file_in_forecasts_subdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_forecast_csv(_four_forecasts(), as_of, "USDJPY", tmpdir)
            assert "forecasts" in path

    def test_filename_contains_date_and_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_forecast_csv(_four_forecasts(), as_of, "USDJPY", tmpdir)
            basename = os.path.basename(path)
            assert "USDJPY" in basename
            assert "20260314" in basename
            assert basename.endswith("_forecast.csv")

    def test_rerun_overwrites_same_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            p1 = export_daily_forecast_csv(_four_forecasts(), as_of, "USDJPY", tmpdir)
            p2 = export_daily_forecast_csv(_four_forecasts(), as_of, "USDJPY", tmpdir)
            assert p1 == p2

    def test_header_matches_fieldnames(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_forecast_csv(_four_forecasts(), as_of, "USDJPY", tmpdir)
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
            assert header == list(FORECAST_FIELDNAMES)


# ---------------------------------------------------------------------------
# export_daily_outcome_csv
# ---------------------------------------------------------------------------


class TestExportDailyOutcomeCsv:
    def test_writes_one_row_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_outcome_csv(_outcome_up(), as_of, "USDJPY", tmpdir)
            assert path is not None
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                data = list(reader)
            assert len(data) == 1

    def test_returns_none_when_outcome_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            result = export_daily_outcome_csv(None, as_of, "USDJPY", tmpdir)
            assert result is None

    def test_filename_in_outcomes_subdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_outcome_csv(_outcome_up(), as_of, "USDJPY", tmpdir)
            assert path is not None
            assert "outcomes" in path
            assert os.path.basename(path).endswith("_outcome.csv")

    def test_rerun_overwrites_same_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            p1 = export_daily_outcome_csv(_outcome_up(), as_of, "USDJPY", tmpdir)
            p2 = export_daily_outcome_csv(_outcome_up(), as_of, "USDJPY", tmpdir)
            assert p1 == p2


# ---------------------------------------------------------------------------
# export_daily_evaluation_csv
# ---------------------------------------------------------------------------


class TestExportDailyEvaluationCsv:
    def test_writes_four_row_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_evaluation_csv(_four_evaluations(), as_of, "USDJPY", tmpdir)
            assert path is not None
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                data = list(reader)
            assert len(data) == 4

    def test_returns_none_when_evaluations_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            result = export_daily_evaluation_csv(None, as_of, "USDJPY", tmpdir)
            assert result is None

    def test_returns_none_when_evaluations_empty_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            result = export_daily_evaluation_csv((), as_of, "USDJPY", tmpdir)
            assert result is None

    def test_filename_in_evaluations_subdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_evaluation_csv(_four_evaluations(), as_of, "USDJPY", tmpdir)
            assert path is not None
            assert "evaluations" in path
            assert os.path.basename(path).endswith("_evaluation.csv")

    def test_rerun_overwrites_same_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            p1 = export_daily_evaluation_csv(_four_evaluations(), as_of, "USDJPY", tmpdir)
            p2 = export_daily_evaluation_csv(_four_evaluations(), as_of, "USDJPY", tmpdir)
            assert p1 == p2

    def test_header_matches_fieldnames(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            as_of = datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
            path = export_daily_evaluation_csv(_four_evaluations(), as_of, "USDJPY", tmpdir)
            assert path is not None
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
            assert header == list(EVALUATION_FIELDNAMES)
