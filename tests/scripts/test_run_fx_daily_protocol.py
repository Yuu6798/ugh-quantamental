"""Tests for the execution-layer hooks of ``scripts/run_fx_daily_protocol.py`` (spec §7–§8).

The script is loaded by file path like ``test_backfill_execution_history.py``.
``main()`` needs a database, a market-data provider and Alembic, so the tests
drive the helpers it calls instead: the Friday-block artifact generator and
its non-fatal wrapper (on the ``execution_archive`` fixture of
``conftest.py``) and the result-section printer (on a constructed
``FxDailyAutomationResult``).  No network, no clock.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol import execution_reporting as reporting
from ugh_quantamental.fx_protocol.automation_models import (
    ExecutionEvaluationWindowResult,
    FxDailyAutomationResult,
)

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_fx_daily_protocol.py"
_spec = importlib.util.spec_from_file_location("run_fx_daily_protocol", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
daily = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = daily
_spec.loader.exec_module(daily)

_JST = ZoneInfo("Asia/Tokyo")
_FRIDAY_AS_OF = datetime(2026, 3, 6, 8, tzinfo=_JST)
# The Friday block's report date: as_of_jst + 1 day (a Saturday) at 08:00 JST.
_SATURDAY = (_FRIDAY_AS_OF + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
_WEEK_1 = {"start_as_of_jst": "2026-03-02", "end_as_of_jst": "2026-03-06"}
_WEEK_2 = {"start_as_of_jst": "2026-03-09", "end_as_of_jst": "2026-03-13"}
_CUMULATIVE = {"start_as_of_jst": None, "end_as_of_jst": None}


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _boom(*args: object, **kwargs: object) -> None:
    raise RuntimeError("boom")


def _x1(report: dict) -> dict:
    return report["strata"]["x1"]["books"]["ugh_x1"]


# ---------------------------------------------------------------------------
# Friday block: the weekly artifact for report_date = as_of + 1 day
# ---------------------------------------------------------------------------


class TestGenerateExecutionWeeklyArtifacts:
    def test_saturday_report_date_covers_mon_fri_and_refreshes_latest(
        self, execution_archive: tuple[str, datetime]
    ) -> None:
        root, generated_at = execution_archive

        paths = daily.generate_execution_weekly_artifacts(root, _SATURDAY, generated_at)

        out_dir = os.path.join(root, "analytics", "execution", "weekly", "20260307")
        assert paths == {
            "execution_weekly_md": os.path.join(out_dir, "execution_weekly.md"),
            "execution_weekly_csv": os.path.join(out_dir, "execution_weekly.csv"),
            "execution_weekly_json": os.path.join(out_dir, "execution_weekly.json"),
            "execution_summary_json": os.path.join(root, "latest", "execution_summary.json"),
        }
        for path in paths.values():
            assert os.path.isfile(path)
        report = _load_json(paths["execution_weekly_json"])
        assert report["window"] == _WEEK_1
        assert _x1(report)["decision_count"] == 5
        assert _x1(report)["trade_count"] == 5
        with open(paths["execution_weekly_md"], encoding="utf-8") as fh:
            assert "# FX Execution Report — 2026-03-02 to 2026-03-06" in fh.read()

        latest = _load_json(paths["execution_summary_json"])
        assert "stale" not in latest
        assert latest["window"] == _CUMULATIVE
        assert _x1(latest)["decision_count"] == 10
        assert latest["gate"]["blocked_reasons"] == []

    def test_next_saturday_covers_the_second_week(
        self, execution_archive: tuple[str, datetime]
    ) -> None:
        root, generated_at = execution_archive
        saturday = _SATURDAY + timedelta(days=7)

        paths = daily.generate_execution_weekly_artifacts(root, saturday, generated_at)

        assert paths["execution_weekly_json"].endswith(
            os.path.join("weekly", "20260314", "execution_weekly.json")
        )
        report = _load_json(paths["execution_weekly_json"])
        assert report["window"] == _WEEK_2
        assert _x1(report)["decision_count"] == 5


class TestNonFatalGuard:
    def test_failure_prints_warn_and_leaves_the_archive_untouched(
        self,
        execution_archive: tuple[str, datetime],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root, generated_at = execution_archive
        monkeypatch.setattr(reporting, "run_execution_report", _boom)

        assert daily._run_execution_weekly_non_fatal(root, _SATURDAY, generated_at) is None

        out = capsys.readouterr().out
        assert "--- Execution report (weekly) ---" in out
        assert "[WARN] Execution report generation failed (non-fatal): boom" in out
        assert not os.path.exists(os.path.join(root, "analytics", "execution"))
        assert _load_json(os.path.join(root, "latest", "execution_summary.json")) == {"stale": True}

    def test_success_prints_paths_and_ok(
        self, execution_archive: tuple[str, datetime], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root, generated_at = execution_archive

        paths = daily._run_execution_weekly_non_fatal(root, _SATURDAY, generated_at)

        assert paths is not None
        out = capsys.readouterr().out
        assert "--- Execution report (weekly) ---" in out
        assert f"  execution_md   : {paths['execution_weekly_md']}" in out
        assert f"  latest_summary : {paths['execution_summary_json']}" in out
        assert "[OK] Execution weekly report generated." in out


# ---------------------------------------------------------------------------
# Result section: the three execution-layer lines
# ---------------------------------------------------------------------------


class TestPrintExecutionSummary:
    def test_prints_one_line_per_counter(self, capsys: pytest.CaptureFixture[str]) -> None:
        windows = tuple(
            ExecutionEvaluationWindowResult(
                forecast_batch_id=f"fb_{index}",
                as_of_jst=_FRIDAY_AS_OF - timedelta(days=index),
                evaluation_csv_path=f"/data/history/{index}/execution_evaluation.csv",
                evaluation_count=6,
            )
            for index in range(2)
        )
        result = FxDailyAutomationResult(
            as_of_jst=_FRIDAY_AS_OF,
            execution_decisions_recorded=6,
            execution_evaluations_recorded=12,
            execution_evaluation_windows=windows,
        )

        daily._print_execution_summary(result)

        assert capsys.readouterr().out.splitlines() == [
            "  execution_decisions_recorded   : 6",
            "  execution_evaluations_recorded : 12",
            "  execution_evaluation_windows   : 2",
        ]

    def test_defaults_print_zeros(self, capsys: pytest.CaptureFixture[str]) -> None:
        daily._print_execution_summary(FxDailyAutomationResult(as_of_jst=_FRIDAY_AS_OF))

        assert capsys.readouterr().out.splitlines() == [
            "  execution_decisions_recorded   : 0",
            "  execution_evaluations_recorded : 0",
            "  execution_evaluation_windows   : 0",
        ]


def test_main_wires_both_hooks() -> None:
    """``main()`` cannot run without a database; check the two call sites are in place."""
    source = inspect.getsource(daily.main)
    assert "_print_execution_summary(automation_result)" in source
    assert "_run_execution_weekly_non_fatal(" in source
    assert source.index("export_weekly_report_artifacts(") < source.index(
        "_run_execution_weekly_non_fatal("
    )
