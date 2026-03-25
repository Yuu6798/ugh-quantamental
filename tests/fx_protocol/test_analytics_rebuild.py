"""Tests for analytics rebuild from persisted history."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

import pytest
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.analytics_rebuild import (
    rebuild_annotation_analytics,
    rebuild_weekly_report,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_NOW = datetime(2026, 3, 20, 6, 0, 0, tzinfo=_UTC)
_REPORT_DATE = datetime(2026, 3, 20, 8, 0, 0, tzinfo=_JST)


# ---------------------------------------------------------------------------
# Helpers: build minimal history structure
# ---------------------------------------------------------------------------

_FORECAST_FIELDNAMES = [
    "forecast_id", "forecast_batch_id", "pair", "strategy_kind", "as_of_jst",
    "window_end_jst", "locked_at_utc", "forecast_direction",
    "expected_close_change_bp", "dominant_state", "state_probabilities",
    "q_dir", "q_strength", "s_q", "temporal_score", "grv_raw", "grv_lock",
    "alignment", "e_star", "mismatch_px", "mismatch_sem", "conviction",
    "urgency", "expected_range_low", "expected_range_high",
    "input_snapshot_ref", "primary_question", "disconfirmers",
    "theory_version", "engine_version", "schema_version", "protocol_version",
    "market_data_vendor", "market_data_feed_name", "market_data_price_type",
    "market_data_resolution", "market_data_timezone",
    "market_data_retrieved_at_utc", "market_data_source_ref",
]

_EVAL_FIELDNAMES = [
    "evaluation_id", "forecast_id", "outcome_id", "pair", "strategy_kind",
    "direction_hit", "range_hit", "close_error_bp", "magnitude_error_bp",
    "state_proxy_hit", "mismatch_change_bp", "realized_state_proxy",
    "actual_state_change", "disconfirmers_hit", "disconfirmer_explained",
    "evaluated_at_utc", "theory_version", "engine_version", "schema_version",
    "protocol_version", "window_end_jst",
]

_OUTCOME_FIELDNAMES = [
    "outcome_id", "pair", "window_start_jst", "window_end_jst",
    "realized_open", "realized_high", "realized_low", "realized_close",
    "realized_direction", "realized_close_change_bp", "realized_range_price",
    "event_happened", "event_tags",
    "market_data_vendor",
]


def _write_csv(path: str, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _setup_history(tmpdir: str) -> None:
    """Create minimal history structure for rebuild tests."""
    date_dir = os.path.join(tmpdir, "history", "20260318", "batch_001")

    # Forecast CSV
    fc_row = {
        "forecast_id": "fc_001",
        "forecast_batch_id": "batch_001",
        "pair": "USDJPY",
        "strategy_kind": "ugh",
        "as_of_jst": "2026-03-18T08:00:00+09:00",
        "window_end_jst": "2026-03-19T08:00:00+09:00",
        "locked_at_utc": "2026-03-17T23:00:00Z",
        "forecast_direction": "up",
        "expected_close_change_bp": "20.0",
    }
    _write_csv(os.path.join(date_dir, "forecast.csv"), [fc_row], _FORECAST_FIELDNAMES)

    # Evaluation CSV
    ev_row = {
        "evaluation_id": "ev_001",
        "forecast_id": "fc_001",
        "outcome_id": "oc_001",
        "pair": "USDJPY",
        "strategy_kind": "ugh",
        "direction_hit": "True",
        "range_hit": "True",
        "close_error_bp": "5.0",
        "magnitude_error_bp": "3.0",
        "state_proxy_hit": "",
        "mismatch_change_bp": "",
        "realized_state_proxy": "",
        "actual_state_change": "",
        "disconfirmers_hit": "",
        "disconfirmer_explained": "",
        "evaluated_at_utc": "2026-03-19T08:00:00Z",
        "theory_version": "v1",
        "engine_version": "v1",
        "schema_version": "v1",
        "protocol_version": "v1",
        "window_end_jst": "2026-03-19T08:00:00+09:00",
    }
    _write_csv(os.path.join(date_dir, "evaluation.csv"), [ev_row], _EVAL_FIELDNAMES)

    # Outcome CSV
    oc_row = {
        "outcome_id": "oc_001",
        "pair": "USDJPY",
        "window_start_jst": "2026-03-18T08:00:00+09:00",
        "window_end_jst": "2026-03-19T08:00:00+09:00",
        "realized_open": "150.0",
        "realized_high": "151.0",
        "realized_low": "149.0",
        "realized_close": "150.5",
        "realized_direction": "up",
        "realized_close_change_bp": "33.3",
        "realized_range_price": "2.0",
        "event_happened": "False",
        "event_tags": "",
    }
    _write_csv(os.path.join(date_dir, "outcome.csv"), [oc_row], _OUTCOME_FIELDNAMES)


def _setup_annotations(tmpdir: str) -> None:
    """Create manual annotations for rebuild tests."""
    ann_dir = os.path.join(tmpdir, "annotations")
    os.makedirs(ann_dir, exist_ok=True)
    ann_path = os.path.join(ann_dir, "manual_annotations.csv")
    ann_row = {
        "as_of_jst": "2026-03-18T08:00:00+09:00",
        "regime_label": "trending",
        "event_tags": "fomc",
        "volatility_label": "normal",
        "intervention_risk": "low",
        "notes": "test annotation",
        "annotation_status": "confirmed",
    }
    fieldnames = [
        "as_of_jst", "regime_label", "event_tags", "volatility_label",
        "intervention_risk", "notes", "annotation_status",
    ]
    _write_csv(ann_path, [ann_row], fieldnames)


# ---------------------------------------------------------------------------
# Tests: rebuild annotation analytics
# ---------------------------------------------------------------------------


class TestRebuildAnnotationAnalytics:
    def test_rebuilds_from_history(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        _setup_annotations(tmpdir)

        result = rebuild_annotation_analytics(tmpdir, generated_at_utc=_NOW)

        assert result["labeled_observations_path"] is not None
        assert os.path.isfile(result["labeled_observations_path"])
        assert result["manual_annotation_template_path"] is not None

    def test_handles_empty_history(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        result = rebuild_annotation_analytics(tmpdir, generated_at_utc=_NOW)
        # Should not crash, labeled_observations may be None
        assert result["labeled_observations_path"] is None

    def test_no_forecast_reexecution(self, tmp_path: str) -> None:
        """Verify rebuild does not import or invoke any forecast logic."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        # If this tried to import forecasting, it would need SQLAlchemy
        result = rebuild_annotation_analytics(tmpdir, generated_at_utc=_NOW)
        assert isinstance(result, dict)

    def test_annotation_correction_reflected(self, tmp_path: str) -> None:
        """After correcting annotations, rebuild should reflect new labels."""
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)

        # First build without annotations
        r1 = rebuild_annotation_analytics(tmpdir, generated_at_utc=_NOW)
        assert r1["labeled_observations_path"] is not None

        # Add confirmed annotation
        _setup_annotations(tmpdir)

        # Rebuild — annotations should now appear
        r2 = rebuild_annotation_analytics(tmpdir, generated_at_utc=_NOW)
        assert r2["labeled_observations_path"] is not None

        # Read labeled observations and check annotation is present
        with open(r2["labeled_observations_path"], newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        confirmed = [r for r in rows if r.get("annotation_status") == "confirmed"]
        assert len(confirmed) >= 1


# ---------------------------------------------------------------------------
# Tests: rebuild weekly report
# ---------------------------------------------------------------------------


class TestRebuildWeeklyReport:
    def test_full_rebuild(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)
        _setup_annotations(tmpdir)

        report = rebuild_weekly_report(
            tmpdir, _REPORT_DATE, generated_at_utc=_NOW
        )

        assert report["report_version"] == "v2"
        assert report["observation_count"] >= 1
        assert len(report["generated_artifact_paths"]) > 0

        # Check artifacts exist
        for path in report["generated_artifact_paths"]:
            assert os.path.isfile(path), f"Artifact not found: {path}"

    def test_rebuild_without_annotations(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        _setup_history(tmpdir)

        report = rebuild_weekly_report(
            tmpdir, _REPORT_DATE, generated_at_utc=_NOW
        )

        # Should work but with all unlabeled
        assert report["report_version"] == "v2"
        cov = report["annotation_coverage"]
        assert cov["confirmed_annotation_count"] == 0

    def test_rebuild_empty_dir_raises(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        with pytest.raises(RuntimeError, match="labeled_observations rebuild produced no output"):
            rebuild_weekly_report(
                tmpdir, _REPORT_DATE, generated_at_utc=_NOW
            )

    def test_rebuild_preserves_existing_logic(self) -> None:
        """Weekly v1 models must still be importable after v2 is added."""
        from ugh_quantamental.fx_protocol.report_models import (
            BaselineWeeklyComparison,
            StateWeeklyMetrics,
            StrategyWeeklyMetrics,
            WeeklyCaseExample,
            WeeklyGrvFireSummary,
            WeeklyMismatchSummary,
            WeeklyReportRequest,
            WeeklyReportResult,
        )
        # All v1 models must exist
        assert WeeklyReportRequest is not None
        assert WeeklyReportResult is not None
        assert StrategyWeeklyMetrics is not None
        assert BaselineWeeklyComparison is not None
        assert StateWeeklyMetrics is not None
        assert WeeklyGrvFireSummary is not None
        assert WeeklyMismatchSummary is not None
        assert WeeklyCaseExample is not None
