"""Tests for the execution-layer hooks of ``scripts/run_fx_analysis_pipeline.py`` (spec §8).

The script is loaded by file path like ``test_backfill_execution_history.py``.
The archive comes from the ``execution_archive`` fixture (``conftest.py``).
``main()`` is driven with its heavy weekly / monthly steps stubbed and a pinned
``FX_REPORT_DATE``, so only the wiring around the execution step is exercised;
the step itself is tested directly with a pinned ``generated_at_utc``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol import execution_reporting as reporting

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_fx_analysis_pipeline.py"
_spec = importlib.util.spec_from_file_location("run_fx_analysis_pipeline", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
pipeline = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = pipeline
_spec.loader.exec_module(pipeline)

_JST = ZoneInfo("Asia/Tokyo")
# Weekly report date: the Monday after the archive's first week (window = that week).
_MONDAY = datetime(2026, 3, 9, 8, tzinfo=_JST)
# Monthly review date: ten business days back cover the whole archive (window = both weeks).
_MID_MARCH = datetime(2026, 3, 16, 8, tzinfo=_JST)
_WEEK_1 = {"start_as_of_jst": "2026-03-02", "end_as_of_jst": "2026-03-06"}
_BOTH_WEEKS = {"start_as_of_jst": "2026-03-02", "end_as_of_jst": "2026-03-13"}
_CUMULATIVE = {"start_as_of_jst": None, "end_as_of_jst": None}
_WEEKLY_STUB = {"observation_count": 28, "annotation_coverage": {"annotation_coverage_rate": 1.0}}


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _boom(*args: object, **kwargs: object) -> None:
    raise RuntimeError("boom")


def _x1(report: dict) -> dict:
    return report["strata"]["x1"]["books"]["ugh_x1"]


# ---------------------------------------------------------------------------
# Window resolution (same resolver as the weekly v2 / monthly review steps)
# ---------------------------------------------------------------------------


class TestResolveExecutionReportWindow:
    def test_weekly_is_previous_week_labelled_by_report_date(self) -> None:
        assert pipeline.resolve_execution_report_window("weekly", _MONDAY, 5) == (
            "20260302",
            "20260306",
            "20260309",
        )

    def test_monthly_is_labelled_by_month_of_window_end(self) -> None:
        april_first = datetime(2026, 4, 1, 8, tzinfo=_JST)
        assert pipeline.resolve_execution_report_window("monthly", april_first, 20) == (
            "20260304",
            "20260331",
            "202603",
        )

    def test_unknown_scope_rejected(self) -> None:
        with pytest.raises(ValueError, match="scope"):
            pipeline.resolve_execution_report_window("daily", _MONDAY, 5)


# ---------------------------------------------------------------------------
# The step: scoped artifact + latest summary refresh
# ---------------------------------------------------------------------------


class TestRunExecutionReportStep:
    def test_weekly_writes_window_artifacts_and_refreshes_latest(
        self, execution_archive: tuple[str, datetime]
    ) -> None:
        root, generated_at = execution_archive
        result = pipeline.run_execution_report_step(root, "weekly", _MONDAY, 5, generated_at)

        assert (result.scope, result.label, result.window_start, result.window_end) == (
            "weekly",
            "20260309",
            "20260302",
            "20260306",
        )
        out_dir = os.path.join(root, "analytics", "execution", "weekly", "20260309")
        for ext in ("md", "csv", "json"):
            path = os.path.join(out_dir, f"execution_weekly.{ext}")
            assert result.paths[f"execution_weekly_{ext}"] == path
            assert os.path.isfile(path)
        report = _load_json(result.paths["execution_weekly_json"])
        assert report["window"] == _WEEK_1
        assert _x1(report)["decision_count"] == 5

        latest_path = os.path.join(root, "latest", "execution_summary.json")
        assert result.paths["execution_summary_json"] == latest_path
        latest = _load_json(latest_path)
        assert "stale" not in latest
        assert latest["window"] == _CUMULATIVE
        assert _x1(latest)["decision_count"] == 10
        assert latest["gate"]["blocked_reasons"] == []

    def test_monthly_writes_month_window_and_refreshes_latest(
        self, execution_archive: tuple[str, datetime]
    ) -> None:
        root, generated_at = execution_archive
        result = pipeline.run_execution_report_step(root, "monthly", _MID_MARCH, 10, generated_at)

        assert (result.scope, result.label, result.window_start, result.window_end) == (
            "monthly",
            "202603",
            "20260302",
            "20260313",
        )
        out_dir = os.path.join(root, "analytics", "execution", "monthly", "202603")
        for ext in ("md", "csv", "json"):
            path = os.path.join(out_dir, f"execution_monthly.{ext}")
            assert result.paths[f"execution_monthly_{ext}"] == path
            assert os.path.isfile(path)
        report = _load_json(result.paths["execution_monthly_json"])
        assert report["window"] == _BOTH_WEEKS
        assert _x1(report)["decision_count"] == 10

        latest = _load_json(os.path.join(root, "latest", "execution_summary.json"))
        assert "stale" not in latest
        assert latest["window"] == _CUMULATIVE

    def test_latest_summary_does_not_depend_on_the_scope_that_ran_last(
        self, execution_archive: tuple[str, datetime]
    ) -> None:
        root, generated_at = execution_archive
        latest_path = os.path.join(root, "latest", "execution_summary.json")

        pipeline.run_execution_report_step(root, "weekly", _MONDAY, 5, generated_at)
        with open(latest_path, "rb") as fh:
            after_weekly = fh.read()
        pipeline.run_execution_report_step(root, "monthly", _MID_MARCH, 10, generated_at)
        with open(latest_path, "rb") as fh:
            after_monthly = fh.read()

        assert after_weekly == after_monthly


# ---------------------------------------------------------------------------
# Non-fatal guard
# ---------------------------------------------------------------------------


class TestNonFatalGuard:
    def test_failure_prints_warn_and_leaves_the_archive_untouched(
        self,
        execution_archive: tuple[str, datetime],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root, generated_at = execution_archive
        monkeypatch.setattr(reporting, "run_execution_report", _boom)

        result = pipeline._run_execution_report_step_non_fatal(
            root, "weekly", _MONDAY, 5, generated_at
        )

        assert result is None
        out = capsys.readouterr().out
        assert "--- Execution report (weekly) ---" in out
        assert "[WARN] Execution weekly report generation failed (non-fatal): boom" in out
        assert not os.path.exists(os.path.join(root, "analytics", "execution"))
        assert _load_json(os.path.join(root, "latest", "execution_summary.json")) == {"stale": True}

    def test_success_prints_window_paths_and_ok(
        self, execution_archive: tuple[str, datetime], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root, generated_at = execution_archive

        result = pipeline._run_execution_report_step_non_fatal(
            root, "monthly", _MID_MARCH, 10, generated_at
        )

        assert result is not None
        out = capsys.readouterr().out
        assert "--- Execution report (monthly) ---" in out
        assert "  window             : 20260302 - 20260313" in out
        assert f"  execution_md       : {result.paths['execution_monthly_md']}" in out
        assert f"  latest_summary     : {result.paths['execution_summary_json']}" in out
        assert "[OK] Execution monthly report generated." in out


# ---------------------------------------------------------------------------
# main(): the hook sits after the existing weekly / monthly step of each mode
# ---------------------------------------------------------------------------


class TestMainWiring:
    @pytest.fixture
    def root(self, execution_archive: tuple[str, datetime], monkeypatch: pytest.MonkeyPatch) -> str:
        csv_output_dir, _generated_at = execution_archive
        monkeypatch.setenv("FX_CSV_OUTPUT_DIR", csv_output_dir)
        for key in ("FX_PIPELINE_MODE", "FX_REPORT_DATE", "FX_WEEK_DAYS", "FX_MONTH_DAYS"):
            monkeypatch.delenv(key, raising=False)
        return csv_output_dir

    @staticmethod
    def _spy(monkeypatch: pytest.MonkeyPatch, calls: list[tuple[object, ...]]) -> None:
        def record(
            csv_output_dir: str,
            scope: str,
            report_date_jst: datetime,
            business_day_count: int,
            generated_at_utc: datetime,
        ) -> object:
            calls.append((csv_output_dir, scope, report_date_jst, business_day_count))
            return pipeline.ExecutionReportStepResult(
                scope,
                "label",
                "start",
                "end",
                {f"execution_{scope}_md": "md", "execution_summary_json": "latest"},
            )

        monkeypatch.setattr(pipeline, "run_execution_report_step", record)

    def test_weekly_mode_runs_the_step_after_the_weekly_step(
        self, root: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("FX_PIPELINE_MODE", "weekly")
        monkeypatch.setenv("FX_REPORT_DATE", "20260309")
        monkeypatch.setattr(pipeline, "run_weekly_pipeline", lambda *a, **k: _WEEKLY_STUB)
        calls: list[tuple[object, ...]] = []
        self._spy(monkeypatch, calls)

        pipeline.main()

        assert calls == [(root, "weekly", _MONDAY, 5)]
        out = capsys.readouterr().out
        summary = out.index("=== Weekly Pipeline Summary ===")
        hook = out.index("--- Execution report (weekly) ---")
        done = out.index("[OK] Weekly pipeline completed successfully.")
        assert summary < hook < done

    def test_monthly_mode_runs_the_step_after_the_monthly_step(
        self, root: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("FX_PIPELINE_MODE", "monthly")
        monkeypatch.setenv("FX_REPORT_DATE", "20260316")
        monkeypatch.setenv("FX_MONTH_DAYS", "10")
        monkeypatch.setattr(pipeline, "run_monthly_pipeline", lambda *a, **k: None)
        calls: list[tuple[object, ...]] = []
        self._spy(monkeypatch, calls)

        pipeline.main()

        assert calls == [(root, "monthly", _MID_MARCH, 10)]
        out = capsys.readouterr().out
        hook = out.index("--- Execution report (monthly) ---")
        done = out.index("[OK] Monthly pipeline completed successfully.")
        assert hook < done

    def test_weekly_mode_end_to_end_writes_the_artifacts(
        self, root: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The real step on the real archive; main() reads its own clock for
        # generated_at_utc, so only clock-independent facts are asserted.
        monkeypatch.setenv("FX_PIPELINE_MODE", "weekly")
        monkeypatch.setenv("FX_REPORT_DATE", "20260309")
        monkeypatch.setattr(pipeline, "run_weekly_pipeline", lambda *a, **k: _WEEKLY_STUB)

        pipeline.main()

        out_dir = os.path.join(root, "analytics", "execution", "weekly", "20260309")
        report = _load_json(os.path.join(out_dir, "execution_weekly.json"))
        assert report["window"] == _WEEK_1
        assert _x1(report)["decision_count"] == 5
        latest = _load_json(os.path.join(root, "latest", "execution_summary.json"))
        assert "stale" not in latest
        assert latest["window"] == _CUMULATIVE

    def test_execution_failure_does_not_fail_the_pipeline(
        self, root: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("FX_PIPELINE_MODE", "weekly")
        monkeypatch.setenv("FX_REPORT_DATE", "20260309")
        monkeypatch.setattr(pipeline, "run_weekly_pipeline", lambda *a, **k: _WEEKLY_STUB)
        monkeypatch.setattr(reporting, "run_execution_report", _boom)

        pipeline.main()  # no SystemExit

        out = capsys.readouterr().out
        assert "[WARN] Execution weekly report generation failed (non-fatal): boom" in out
        assert "[OK] Weekly pipeline completed successfully." in out

    def test_weekly_step_failure_still_fails_before_the_execution_step(
        self, root: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FX_PIPELINE_MODE", "weekly")
        monkeypatch.setenv("FX_REPORT_DATE", "20260309")
        monkeypatch.setattr(pipeline, "run_weekly_pipeline", _boom)
        calls: list[tuple[object, ...]] = []
        self._spy(monkeypatch, calls)

        with pytest.raises(SystemExit):
            pipeline.main()

        assert calls == []
