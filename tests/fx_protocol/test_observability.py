"""Tests for observability.py — pure artifact generation and layout publication."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    EvaluationRecord,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.observability import (
    PROVIDER_HEALTH_FIELDNAMES,
    append_csv_row,
    build_daily_report_md,
    build_input_snapshot,
    build_provider_health_row,
    build_run_summary,
    build_scoreboard_rows,
    collect_all_evaluations_from_history,
    publish_observability_to_layout,
    write_csv_artifact,
    write_json_artifact,
    write_md_artifact,
)

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

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


def _build_windows(n: int) -> tuple[FxCompletedWindow, ...]:
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        windows.append(
            FxCompletedWindow(
                window_start_jst=start,
                window_end_jst=end,
                open_price=149.5,
                high_price=151.5,
                low_price=148.5,
                close_price=150.5,
            )
        )
        start = end
        count += 1
    return tuple(windows)


def _make_snapshot() -> FxProtocolMarketSnapshot:
    wins = _build_windows(20)
    as_of = wins[-1].window_end_jst
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of,
        current_spot=150.0,
        completed_windows=wins,
        market_data_provenance=_provenance(),
    )


def _ugh_forecast(as_of: datetime, window_end: datetime) -> ForecastRecord:
    from ugh_quantamental.fx_protocol.ids import make_forecast_id
    from ugh_quantamental.schemas.enums import LifecycleState, QuestionDirection
    from ugh_quantamental.schemas.market_svp import StateProbabilities

    return ForecastRecord(
        forecast_id=make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", StrategyKind.ugh),
        forecast_batch_id="fb_test_batch",
        pair=CurrencyPair.USDJPY,
        strategy_kind=StrategyKind.ugh,
        as_of_jst=as_of,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=_UTC),
        market_data_provenance=_provenance(),
        forecast_direction=ForecastDirection.up,
        expected_close_change_bp=10.5,
        expected_range=ExpectedRange(low_price=149.0, high_price=151.5),
        dominant_state=LifecycleState.setup,
        state_probabilities=StateProbabilities(
            dormant=0.05, setup=0.50, fire=0.20,
            expansion=0.10, exhaustion=0.10, failure=0.05,
        ),
        q_dir=QuestionDirection.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.8,
        grv_raw=0.5,
        grv_lock=0.55,
        alignment=0.9,
        e_star=12.0,
        mismatch_px=0.01,
        mismatch_sem=0.02,
        conviction=0.75,
        urgency=0.6,
        input_snapshot_ref="auto",
        primary_question="test_q",
        disconfirmers=(),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _baseline_forecast(
    as_of: datetime, window_end: datetime, strategy: StrategyKind
) -> ForecastRecord:
    from ugh_quantamental.fx_protocol.ids import make_forecast_id

    return ForecastRecord(
        forecast_id=make_forecast_id(CurrencyPair.USDJPY, as_of, "v1", strategy),
        forecast_batch_id="fb_test_batch",
        pair=CurrencyPair.USDJPY,
        strategy_kind=strategy,
        as_of_jst=as_of,
        window_end_jst=window_end,
        locked_at_utc=datetime(2026, 3, 12, 22, 0, 0, tzinfo=_UTC),
        market_data_provenance=_provenance(),
        forecast_direction=ForecastDirection.flat,
        expected_close_change_bp=0.0,
        disconfirmers=(),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


def _make_outcome(
    window_start: datetime, window_end: datetime
) -> OutcomeRecord:
    from ugh_quantamental.fx_protocol.ids import make_outcome_id

    # Derive realized_close_change_bp correctly: (close - open) / open * 10000
    realized_open = 149.5
    realized_close = 150.8
    realized_close_change_bp = round((realized_close - realized_open) / realized_open * 10000, 10)
    realized_high = 151.0
    realized_low = 148.5
    realized_range_price = round(realized_high - realized_low, 10)

    return OutcomeRecord(
        outcome_id=make_outcome_id(
            CurrencyPair.USDJPY, window_start, window_end, "v1"
        ),
        pair=CurrencyPair.USDJPY,
        window_start_jst=window_start,
        window_end_jst=window_end,
        market_data_provenance=_provenance(),
        realized_open=realized_open,
        realized_high=realized_high,
        realized_low=realized_low,
        realized_close=realized_close,
        realized_direction=ForecastDirection.up,
        realized_close_change_bp=realized_close_change_bp,
        realized_range_price=realized_range_price,
        event_happened=False,
        event_tags=(),
        schema_version="v1",
        protocol_version="v1",
    )


def _make_evaluation(
    forecast: ForecastRecord,
    outcome: OutcomeRecord,
    direction_hit: bool = True,
) -> EvaluationRecord:
    from ugh_quantamental.fx_protocol.ids import make_evaluation_id

    is_ugh = forecast.strategy_kind == StrategyKind.ugh
    return EvaluationRecord(
        evaluation_id=make_evaluation_id(
            forecast.forecast_id, outcome.outcome_id, "v1"
        ),
        forecast_id=forecast.forecast_id,
        outcome_id=outcome.outcome_id,
        pair=CurrencyPair.USDJPY,
        strategy_kind=forecast.strategy_kind,
        direction_hit=direction_hit,
        range_hit=True if is_ugh else None,
        close_error_bp=1.8,
        magnitude_error_bp=1.2,
        state_proxy_hit=True if is_ugh else None,
        mismatch_change_bp=-1.8 if is_ugh else None,
        realized_state_proxy="setup" if is_ugh else None,
        actual_state_change=False if is_ugh else None,
        disconfirmers_hit=(),
        disconfirmer_explained=False,
        evaluated_at_utc=datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )


# ---------------------------------------------------------------------------
# 1. build_input_snapshot
# ---------------------------------------------------------------------------


class TestBuildInputSnapshot:
    def test_has_required_keys(self) -> None:
        snap = _make_snapshot()
        result = build_input_snapshot(snap, datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC))
        for key in (
            "as_of_jst", "pair", "current_spot", "provider_name",
            "market_data_provenance", "completed_windows",
            "completed_window_count", "newest_completed_window_end_jst",
            "generated_at_utc",
        ):
            assert key in result, f"missing key: {key}"

    def test_window_count_matches(self) -> None:
        snap = _make_snapshot()
        result = build_input_snapshot(snap, datetime.now(_UTC))
        assert result["completed_window_count"] == 20
        assert len(result["completed_windows"]) == 20

    def test_provider_name_from_provenance(self) -> None:
        snap = _make_snapshot()
        result = build_input_snapshot(snap, datetime.now(_UTC))
        assert result["provider_name"] == "test_vendor"

    def test_pair_value(self) -> None:
        snap = _make_snapshot()
        result = build_input_snapshot(snap, datetime.now(_UTC))
        assert result["pair"] == "USDJPY"


# ---------------------------------------------------------------------------
# 2. build_run_summary
# ---------------------------------------------------------------------------


class TestBuildRunSummary:
    def test_has_required_keys(self) -> None:
        result = build_run_summary(
            as_of_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
            provider_name="test_vendor",
            forecast_batch_id="fb_123",
            outcome_id=None,
            forecast_created=True,
            outcome_recorded=False,
            evaluation_count=0,
            forecast_csv_path="/tmp/f.csv",
            outcome_csv_path=None,
            evaluation_csv_path=None,
            manifest_path="/tmp/m.json",
            snapshot_lag_business_days=0,
            used_fallback_adjustment=False,
            run_status="ok",
            theory_version="v1",
            engine_version="v1",
            schema_version="v1",
            protocol_version="v1",
            generated_at_utc=datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC),
        )
        for key in (
            "provider_name", "versions", "forecast_batch_id", "csv_paths",
            "manifest_path", "evaluation_count", "forecast_created",
            "outcome_recorded", "snapshot_lag_business_days",
            "used_fallback_adjustment", "run_status",
        ):
            assert key in result, f"missing key: {key}"

    def test_versions_nested(self) -> None:
        result = build_run_summary(
            as_of_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
            provider_name="v",
            forecast_batch_id="fb",
            outcome_id=None,
            forecast_created=True,
            outcome_recorded=False,
            evaluation_count=0,
            forecast_csv_path=None,
            outcome_csv_path=None,
            evaluation_csv_path=None,
            manifest_path=None,
            snapshot_lag_business_days=0,
            used_fallback_adjustment=False,
            run_status="ok",
            theory_version="v1",
            engine_version="v2",
            schema_version="v1",
            protocol_version="v1",
            generated_at_utc=datetime.now(_UTC),
        )
        assert result["versions"]["engine_version"] == "v2"


# ---------------------------------------------------------------------------
# 3. build_daily_report_md
# ---------------------------------------------------------------------------


class TestBuildDailyReportMd:
    def test_returns_string(self) -> None:
        as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
        window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
        forecasts = (
            _ugh_forecast(as_of, window_end),
            _baseline_forecast(as_of, window_end, StrategyKind.baseline_random_walk),
        )
        md = build_daily_report_md(
            as_of_jst=as_of,
            forecast_batch_id="fb_123",
            forecasts=forecasts,
            outcome=None,
            evaluations=(),
            manifest_data=None,
            generated_at_utc=datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC),
        )
        assert isinstance(md, str)
        assert "# FX Daily Report" in md
        assert "fb_123" in md

    def test_contains_forecast_table(self) -> None:
        as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
        window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
        forecasts = (_ugh_forecast(as_of, window_end),)
        md = build_daily_report_md(
            as_of_jst=as_of,
            forecast_batch_id="fb",
            forecasts=forecasts,
            outcome=None,
            evaluations=(),
            manifest_data=None,
            generated_at_utc=datetime.now(_UTC),
        )
        assert "| ugh |" in md
        assert "UP" in md

    def test_contains_outcome_section(self) -> None:
        as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
        window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
        outcome = _make_outcome(as_of, window_end)
        md = build_daily_report_md(
            as_of_jst=as_of,
            forecast_batch_id="fb",
            forecasts=(),
            outcome=outcome,
            evaluations=(),
            manifest_data=None,
            generated_at_utc=datetime.now(_UTC),
        )
        assert "## Previous Window Outcome" in md
        assert "150.8" in md

    def test_contains_evaluation_table(self) -> None:
        as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
        window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
        fc = _ugh_forecast(as_of, window_end)
        oc = _make_outcome(as_of, window_end)
        ev = _make_evaluation(fc, oc)
        md = build_daily_report_md(
            as_of_jst=as_of,
            forecast_batch_id="fb",
            forecasts=(fc,),
            outcome=oc,
            evaluations=(ev,),
            manifest_data=None,
            generated_at_utc=datetime.now(_UTC),
        )
        assert "## Evaluation Comparison" in md
        assert "| ugh |" in md

    def test_empty_forecasts_handled(self) -> None:
        as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
        md = build_daily_report_md(
            as_of_jst=as_of,
            forecast_batch_id=None,
            forecasts=(),
            outcome=None,
            evaluations=(),
            manifest_data=None,
            generated_at_utc=datetime.now(_UTC),
        )
        assert "No forecasts generated" in md
        assert "No outcome recorded" in md
        assert "No evaluations available" in md


# ---------------------------------------------------------------------------
# 4. build_scoreboard_rows
# ---------------------------------------------------------------------------


class TestBuildScoreboardRows:
    def _make_evals(self) -> tuple[EvaluationRecord, ...]:
        as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
        window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
        oc = _make_outcome(as_of, window_end)
        fc_ugh = _ugh_forecast(as_of, window_end)
        fc_rw = _baseline_forecast(as_of, window_end, StrategyKind.baseline_random_walk)
        return (
            _make_evaluation(fc_ugh, oc, direction_hit=True),
            _make_evaluation(fc_rw, oc, direction_hit=False),
        )

    def test_returns_rows_per_strategy(self) -> None:
        evals = self._make_evals()
        rows = build_scoreboard_rows(evals, datetime.now(_UTC))
        strategies = {r["strategy_kind"] for r in rows}
        assert "ugh" in strategies
        assert "baseline_random_walk" in strategies

    def test_direction_hit_rate(self) -> None:
        evals = self._make_evals()
        rows = build_scoreboard_rows(evals, datetime.now(_UTC))
        ugh_row = next(r for r in rows if r["strategy_kind"] == "ugh")
        assert ugh_row["direction_hit_count"] == 1
        assert ugh_row["direction_hit_rate"] == 1.0

    def test_range_hit_blank_for_baseline(self) -> None:
        evals = self._make_evals()
        rows = build_scoreboard_rows(evals, datetime.now(_UTC))
        rw_row = next(r for r in rows if r["strategy_kind"] == "baseline_random_walk")
        assert rw_row["range_hit_count"] == ""
        assert rw_row["range_hit_rate"] == ""

    def test_empty_evals_returns_empty(self) -> None:
        rows = build_scoreboard_rows((), datetime.now(_UTC))
        assert rows == []

    def test_close_error_metrics(self) -> None:
        evals = self._make_evals()
        rows = build_scoreboard_rows(evals, datetime.now(_UTC))
        ugh_row = next(r for r in rows if r["strategy_kind"] == "ugh")
        assert ugh_row["mean_close_error_bp"] == 1.8
        assert ugh_row["median_close_error_bp"] == 1.8


# ---------------------------------------------------------------------------
# 5. build_provider_health_row
# ---------------------------------------------------------------------------


class TestBuildProviderHealthRow:
    def test_has_required_keys(self) -> None:
        row = build_provider_health_row(
            as_of_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
            generated_at_utc=datetime(2026, 3, 16, 1, 0, 0, tzinfo=_UTC),
            provider_name="yahoo",
            newest_completed_window_end_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
            snapshot_lag_business_days=0,
            used_fallback_adjustment=False,
            run_status="ok",
            notes="",
        )
        for key in PROVIDER_HEALTH_FIELDNAMES:
            assert key in row, f"missing key: {key}"

    def test_lag_value(self) -> None:
        row = build_provider_health_row(
            as_of_jst=datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST),
            generated_at_utc=datetime.now(_UTC),
            provider_name="yahoo",
            newest_completed_window_end_jst=datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST),
            snapshot_lag_business_days=1,
            used_fallback_adjustment=True,
            run_status="ok",
            notes="1-day lag",
        )
        assert row["snapshot_lag_business_days"] == 1
        assert row["used_fallback_adjustment"] is True


# ---------------------------------------------------------------------------
# File write helpers
# ---------------------------------------------------------------------------


class TestWriteHelpers:
    def test_write_json_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "test.json")
            result = write_json_artifact(path, {"key": "value"})
            assert os.path.isfile(result)
            with open(result, encoding="utf-8") as fh:
                data = json.load(fh)
            assert data["key"] == "value"

    def test_write_md_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "test.md")
            result = write_md_artifact(path, "# Hello\n")
            assert os.path.isfile(result)
            with open(result, encoding="utf-8") as fh:
                assert fh.read() == "# Hello\n"

    def test_write_csv_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.csv")
            rows = [{"a": 1, "b": 2}]
            result = write_csv_artifact(path, rows, ("a", "b"))
            assert os.path.isfile(result)
            with open(result, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                parsed = list(reader)
            assert len(parsed) == 1
            assert parsed[0]["a"] == "1"

    def test_append_csv_row_creates_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "health.csv")
            append_csv_row(path, {"a": "1", "b": "2"}, ("a", "b"))
            append_csv_row(path, {"a": "3", "b": "4"}, ("a", "b"))
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["a"] == "1"
            assert rows[1]["a"] == "3"


# ---------------------------------------------------------------------------
# Layout publication
# ---------------------------------------------------------------------------


class TestPublishObservabilityToLayout:
    def test_publishes_to_latest_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source artifacts
            src_json = os.path.join(tmpdir, "snap.json")
            with open(src_json, "w") as fh:
                json.dump({"test": True}, fh)

            result = publish_observability_to_layout(
                tmpdir, "20260316", "fb_123",
                input_snapshot_path=src_json,
            )
            assert result["latest_input_snapshot"] == "latest/input_snapshot.json"
            assert os.path.isfile(os.path.join(tmpdir, "latest", "input_snapshot.json"))
            assert os.path.isfile(
                os.path.join(tmpdir, "history", "20260316", "fb_123", "input_snapshot.json")
            )

    def test_deletes_stale_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a stale file
            latest_dir = os.path.join(tmpdir, "latest")
            os.makedirs(latest_dir, exist_ok=True)
            stale = os.path.join(latest_dir, "scoreboard.csv")
            with open(stale, "w") as fh:
                fh.write("stale")

            # Publish without scoreboard
            result = publish_observability_to_layout(
                tmpdir, "20260316", "fb_123",
                scoreboard_path=None,
            )
            assert result["latest_scoreboard"] is None
            assert not os.path.exists(stale)

    def test_all_five_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {}
            for name, ext in [
                ("snap", ".json"), ("summary", ".json"), ("report", ".md"),
                ("score", ".csv"), ("health", ".csv"),
            ]:
                path = os.path.join(tmpdir, f"{name}{ext}")
                with open(path, "w") as fh:
                    fh.write("data")
                files[name] = path

            result = publish_observability_to_layout(
                tmpdir, "20260316", "fb_123",
                input_snapshot_path=files["snap"],
                run_summary_path=files["summary"],
                daily_report_path=files["report"],
                scoreboard_path=files["score"],
                provider_health_path=files["health"],
            )
            for key in [
                "latest_input_snapshot", "latest_run_summary", "latest_daily_report",
                "latest_scoreboard", "latest_provider_health",
            ]:
                assert result[key] is not None


# ---------------------------------------------------------------------------
# collect_all_evaluations_from_history
# ---------------------------------------------------------------------------


class TestCollectAllEvaluationsFromHistory:
    def test_empty_dir_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = collect_all_evaluations_from_history(tmpdir)
            assert result == ()

    def test_reads_evaluation_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            from ugh_quantamental.fx_protocol.csv_exports import (
                EVALUATION_FIELDNAMES,
                evaluation_records_to_rows,
                write_csv_rows,
            )

            as_of = datetime(2026, 3, 13, 8, 0, 0, tzinfo=_JST)
            window_end = datetime(2026, 3, 16, 8, 0, 0, tzinfo=_JST)
            fc = _ugh_forecast(as_of, window_end)
            oc = _make_outcome(as_of, window_end)
            ev = _make_evaluation(fc, oc)

            # Write evaluation CSV to history layout
            hist_dir = os.path.join(tmpdir, "history", "20260313", "fb_test_batch")
            os.makedirs(hist_dir)
            rows = evaluation_records_to_rows((ev,))
            write_csv_rows(
                os.path.join(hist_dir, "evaluation.csv"),
                rows,
                EVALUATION_FIELDNAMES,
            )

            result = collect_all_evaluations_from_history(tmpdir)
            assert len(result) == 1
            assert result[0].evaluation_id == ev.evaluation_id
            assert result[0].direction_hit == ev.direction_hit


# ---------------------------------------------------------------------------
# Full automation integration — observability artifacts
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestAutomationObservabilityIntegration:
    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def test_observability_artifacts_created(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            # All observability paths should be set
            assert result.input_snapshot_path is not None
            assert os.path.isfile(result.input_snapshot_path)
            assert result.run_summary_path is not None
            assert os.path.isfile(result.run_summary_path)
            assert result.daily_report_path is not None
            assert os.path.isfile(result.daily_report_path)
            assert result.provider_health_path is not None
            assert os.path.isfile(result.provider_health_path)

            # Latest layout should have the artifacts
            assert os.path.isfile(os.path.join(tmpdir, "latest", "input_snapshot.json"))
            assert os.path.isfile(os.path.join(tmpdir, "latest", "run_summary.json"))
            assert os.path.isfile(os.path.join(tmpdir, "latest", "daily_report.md"))

        session.close()

    def test_input_snapshot_json_content(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                run_fx_daily_protocol_once(cfg, provider, session)

            with open(
                os.path.join(tmpdir, "latest", "input_snapshot.json"), encoding="utf-8"
            ) as fh:
                data = json.load(fh)
            assert data["pair"] == "USDJPY"
            assert data["completed_window_count"] == 20

        session.close()

    def test_run_summary_json_content(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                run_fx_daily_protocol_once(cfg, provider, session)

            with open(
                os.path.join(tmpdir, "latest", "run_summary.json"), encoding="utf-8"
            ) as fh:
                data = json.load(fh)
            assert data["provider_name"] == "test_vendor"
            assert data["run_status"] in ("ok", "idempotent_skip")
            assert "versions" in data

        session.close()

    def test_no_observability_when_csv_disabled(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=False,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            assert result.input_snapshot_path is None
            assert result.run_summary_path is None
            assert result.daily_report_path is None

        session.close()

    def test_existing_forecasts_unchanged(self) -> None:
        """Verify that observability artifacts don't modify existing forecast data."""
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                r1 = run_fx_daily_protocol_once(cfg, provider, session)

            # forecast CSV should be identical regardless of observability
            assert r1.forecast_csv_path is not None
            with open(r1.forecast_csv_path, encoding="utf-8") as fh:
                csv1 = fh.read()

            session.commit()

            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                r2 = run_fx_daily_protocol_once(cfg, provider, session)

            assert r2.forecast_csv_path is not None
            with open(r2.forecast_csv_path, encoding="utf-8") as fh:
                csv2 = fh.read()

            assert csv1 == csv2

        session.close()
