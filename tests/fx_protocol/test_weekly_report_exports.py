"""Tests for weekly report v2 artifact exports."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.weekly_report_exports import (
    build_weekly_report_md,
    export_weekly_report_artifacts,
    export_weekly_report_json,
    export_weekly_report_md,
    export_weekly_slice_metrics_csv,
    export_weekly_strategy_metrics_csv,
)
from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
    WEEKLY_SLICE_METRICS_FIELDNAMES,
    WEEKLY_STRATEGY_METRICS_FIELDNAMES,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_NOW = datetime(2026, 3, 20, 6, 0, 0, tzinfo=_UTC)


def _sample_report() -> dict:
    return {
        "report_version": "v2",
        "generated_at_utc": "2026-03-20T06:00:00Z",
        "report_date_jst": "2026-03-20T08:00:00+09:00",
        "week_window": {"start": "20260316", "end": "20260320"},
        "business_day_count": 5,
        "annotation_coverage": {
            "total_observations": 10,
            "confirmed_annotation_count": 7,
            "pending_annotation_count": 2,
            "unlabeled_count": 1,
            "annotation_coverage_rate": 0.7,
        },
        "strategy_metrics": [
            {
                "strategy_kind": "ugh",
                "observation_count": 5,
                "direction_hit_count": 3,
                "direction_hit_rate": "0.6",
                "range_hit_count": 2,
                "range_hit_rate": "0.4",
                "state_proxy_hit_count": 2,
                "state_proxy_hit_rate": "0.4",
                "mean_close_error_bp": "15.5",
                "median_close_error_bp": "12.0",
                "mean_magnitude_error_bp": "10.0",
            },
        ],
        "slice_metrics": [
            {
                "slice_dimension": "regime_label",
                "strategy_kind": "ugh",
                "label": "trending",
                "observation_count": 3,
                "direction_hit_count": 2,
                "direction_hit_rate": "0.6667",
                "range_hit_count": 1,
                "range_hit_rate": "0.3333",
                "state_proxy_hit_count": "",
                "state_proxy_hit_rate": "",
                "mean_close_error_bp": "14.0",
                "median_close_error_bp": "13.0",
                "mean_magnitude_error_bp": "9.0",
            },
        ],
        "provider_health_summary": {
            "total_runs": 5,
            "providers": {"alphavantage": 5},
            "fallback_adjustment_count": 1,
            "lag_count": 0,
            "success_count": 5,
            "failed_count": 0,
            "skipped_count": 0,
        },
        "observation_count": 10,
        "generated_artifact_paths": [],
    }


class TestExportWeeklyReportJson:
    def test_writes_valid_json(self, tmp_path: str) -> None:
        report = _sample_report()
        out_dir = str(tmp_path)
        path = export_weekly_report_json(report, out_dir)
        assert os.path.isfile(path)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["report_version"] == "v2"
        assert data["observation_count"] == 10


class TestExportWeeklyReportMd:
    def test_writes_markdown(self, tmp_path: str) -> None:
        report = _sample_report()
        out_dir = str(tmp_path)
        path = export_weekly_report_md(report, out_dir)
        assert os.path.isfile(path)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        assert "FX Weekly Report v2" in content
        assert "Annotation Coverage" in content
        assert "Strategy Performance" in content
        assert "Provider Health Summary" in content


class TestBuildWeeklyReportMd:
    def test_contains_sections(self) -> None:
        report = _sample_report()
        md = build_weekly_report_md(report)
        assert "## Annotation Coverage" in md
        assert "## Strategy Performance" in md
        assert "## Provider Health Summary" in md
        assert "## Annotation-Aware Slice Analysis" in md
        assert "## Notes" in md

    def test_empty_report(self) -> None:
        report = _sample_report()
        report["strategy_metrics"] = []
        report["slice_metrics"] = []
        md = build_weekly_report_md(report)
        assert "No strategy metrics available." in md


class TestExportStrategyCsv:
    def test_valid_csv(self, tmp_path: str) -> None:
        report = _sample_report()
        out_dir = str(tmp_path)
        path = export_weekly_strategy_metrics_csv(report, out_dir)
        assert os.path.isfile(path)
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["strategy_kind"] == "ugh"
        for col in WEEKLY_STRATEGY_METRICS_FIELDNAMES:
            assert col in rows[0]


class TestExportSliceCsv:
    def test_valid_csv(self, tmp_path: str) -> None:
        report = _sample_report()
        out_dir = str(tmp_path)
        path = export_weekly_slice_metrics_csv(report, out_dir)
        assert os.path.isfile(path)
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 1
        for col in WEEKLY_SLICE_METRICS_FIELDNAMES:
            assert col in rows[0]


class TestExportWeeklyReportArtifacts:
    def test_full_export(self, tmp_path: str) -> None:
        report = _sample_report()
        tmpdir = str(tmp_path)
        paths = export_weekly_report_artifacts(report, tmpdir, "20260320")

        assert "weekly_report_json" in paths
        assert "weekly_report_md" in paths
        assert "weekly_strategy_metrics_csv" in paths
        assert "weekly_slice_metrics_csv" in paths

        # Verify dated directory
        dated_dir = os.path.join(tmpdir, "analytics", "weekly", "20260320")
        assert os.path.isfile(os.path.join(dated_dir, "weekly_report.json"))
        assert os.path.isfile(os.path.join(dated_dir, "weekly_report.md"))
        assert os.path.isfile(os.path.join(dated_dir, "weekly_strategy_metrics.csv"))
        assert os.path.isfile(os.path.join(dated_dir, "weekly_slice_metrics.csv"))

        # Verify latest directory
        latest_dir = os.path.join(tmpdir, "analytics", "weekly", "latest")
        assert os.path.isfile(os.path.join(latest_dir, "weekly_report.json"))
        assert os.path.isfile(os.path.join(latest_dir, "weekly_report.md"))

        # Verify JSON has artifact paths
        with open(os.path.join(dated_dir, "weekly_report.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        assert len(data["generated_artifact_paths"]) > 0
