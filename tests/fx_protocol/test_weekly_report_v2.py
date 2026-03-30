"""Tests for weekly report v2 — annotation-aware weekly analytics."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
    build_annotation_coverage,
    build_annotation_field_coverage,
    build_event_tag_source_summary,
    build_provider_health_summary,
    build_slice_metrics,
    build_strategy_metrics,
    run_weekly_report_v2,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_NOW = datetime(2026, 3, 20, 6, 0, 0, tzinfo=_UTC)
_REPORT_DATE = datetime(2026, 3, 20, 8, 0, 0, tzinfo=_JST)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_csv(path: str, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_observation(
    *,
    as_of_jst: str = "2026-03-18T08:00:00+09:00",
    strategy_kind: str = "ugh",
    direction_hit: str = "True",
    range_hit: str = "True",
    state_proxy_hit: str = "True",
    close_error_bp: str = "15.0",
    magnitude_error_bp: str = "10.0",
    regime_label: str = "trending",
    volatility_label: str = "normal",
    intervention_risk: str = "low",
    event_tags: str = "fomc",
    annotation_status: str = "confirmed",
) -> dict[str, str]:
    return {
        "as_of_jst": as_of_jst,
        "forecast_batch_id": "batch_001",
        "outcome_id": "outcome_001",
        "strategy_kind": strategy_kind,
        "forecast_direction": "up",
        "expected_close_change_bp": "20.0",
        "realized_direction": "up",
        "realized_close_change_bp": "18.0",
        "direction_hit": direction_hit,
        "range_hit": range_hit,
        "state_proxy_hit": state_proxy_hit,
        "close_error_bp": close_error_bp,
        "magnitude_error_bp": magnitude_error_bp,
        "regime_label": regime_label,
        "volatility_label": volatility_label,
        "intervention_risk": intervention_risk,
        "event_tags": event_tags,
        "annotation_status": annotation_status,
    }


def _labeled_observation_fieldnames() -> list[str]:
    return [
        "as_of_jst", "forecast_batch_id", "outcome_id", "strategy_kind",
        "forecast_direction", "expected_close_change_bp", "realized_direction",
        "realized_close_change_bp", "direction_hit", "range_hit", "state_proxy_hit",
        "close_error_bp", "magnitude_error_bp",
        "ai_regime_label", "ai_volatility_label", "ai_intervention_risk",
        "ai_event_tags", "ai_failure_reason", "ai_annotation_confidence",
        "ai_annotation_model_version", "ai_annotation_prompt_version",
        "ai_evidence_refs", "ai_annotation_status",
        "regime_label", "event_tags", "manual_event_tags", "auto_event_tags",
        "effective_event_tags", "event_tag_source",
        "volatility_label", "intervention_risk", "failure_reason",
        "annotation_source", "annotation_status",
    ]


def _setup_labeled_observations(tmpdir: str, observations: list[dict[str, str]]) -> None:
    path = os.path.join(tmpdir, "analytics", "labeled_observations.csv")
    _write_csv(path, observations, _labeled_observation_fieldnames())


def _provider_health_fieldnames() -> list[str]:
    return [
        "as_of_jst", "generated_at_utc", "provider_name",
        "newest_completed_window_end_jst", "snapshot_lag_business_days",
        "used_fallback_adjustment", "run_status", "notes",
    ]


def _setup_provider_health(tmpdir: str, rows: list[dict[str, str]]) -> None:
    path = os.path.join(tmpdir, "latest", "provider_health.csv")
    _write_csv(path, rows, _provider_health_fieldnames())


# ---------------------------------------------------------------------------
# Tests: annotation coverage
# ---------------------------------------------------------------------------


class TestAnnotationCoverage:
    def test_all_confirmed(self) -> None:
        obs = [
            _make_observation(annotation_status="confirmed"),
            _make_observation(annotation_status="confirmed"),
        ]
        cov = build_annotation_coverage(obs)
        assert cov["confirmed_annotation_count"] == 2
        assert cov["pending_annotation_count"] == 0
        assert cov["unlabeled_count"] == 0
        assert cov["annotation_coverage_rate"] == 1.0

    def test_mixed_statuses(self) -> None:
        obs = [
            _make_observation(annotation_status="confirmed"),
            _make_observation(annotation_status="pending"),
            _make_observation(annotation_status=""),
        ]
        cov = build_annotation_coverage(obs)
        assert cov["confirmed_annotation_count"] == 1
        assert cov["pending_annotation_count"] == 1
        assert cov["unlabeled_count"] == 1
        assert cov["annotation_coverage_rate"] == pytest.approx(1 / 3, abs=0.001)

    def test_empty(self) -> None:
        cov = build_annotation_coverage([])
        assert cov["total_observations"] == 0
        assert cov["annotation_coverage_rate"] == 0.0


class TestAnnotationCoveragePendingOnly:
    def test_all_pending(self) -> None:
        obs = [
            _make_observation(annotation_status="pending"),
            _make_observation(annotation_status="pending"),
        ]
        cov = build_annotation_coverage(obs)
        assert cov["confirmed_annotation_count"] == 0
        assert cov["pending_annotation_count"] == 2
        assert cov["unlabeled_count"] == 0
        assert cov["annotation_coverage_rate"] == 0.0


class TestAnnotationCoverageUnlabeled:
    def test_all_unlabeled(self) -> None:
        obs = [
            _make_observation(annotation_status=""),
            _make_observation(annotation_status=""),
        ]
        cov = build_annotation_coverage(obs)
        assert cov["unlabeled_count"] == 2
        assert cov["annotation_coverage_rate"] == 0.0


# ---------------------------------------------------------------------------
# Tests: strategy metrics
# ---------------------------------------------------------------------------


class TestStrategyMetrics:
    def test_basic_strategy_grouping(self) -> None:
        obs = [
            _make_observation(strategy_kind="ugh", direction_hit="True"),
            _make_observation(strategy_kind="ugh", direction_hit="False"),
            _make_observation(strategy_kind="baseline_random_walk", direction_hit="True"),
        ]
        metrics = build_strategy_metrics(obs)
        assert len(metrics) == 2
        ugh = next(m for m in metrics if m["strategy_kind"] == "ugh")
        assert ugh["observation_count"] == 2
        assert ugh["direction_hit_count"] == 1


# ---------------------------------------------------------------------------
# Tests: slice metrics
# ---------------------------------------------------------------------------


class TestSliceMetrics:
    def test_regime_label_slice(self) -> None:
        obs = [
            _make_observation(
                strategy_kind="ugh", regime_label="trending",
                annotation_status="confirmed",
            ),
            _make_observation(
                strategy_kind="ugh", regime_label="choppy",
                annotation_status="confirmed",
            ),
        ]
        # Add annotation_source so the AI-first gate sees them as annotated
        for o in obs:
            o["annotation_source"] = "ai"
        slices = build_slice_metrics(obs)
        regime_slices = [s for s in slices if s["slice_dimension"] == "regime_label"]
        labels = {s["label"] for s in regime_slices}
        assert "trending" in labels
        assert "choppy" in labels

    def test_unlabeled_observations_separate(self) -> None:
        obs = [
            _make_observation(
                strategy_kind="ugh", regime_label="trending",
                annotation_status="confirmed",
            ),
            _make_observation(
                strategy_kind="ugh", regime_label="", annotation_status=""
            ),
        ]
        obs[0]["annotation_source"] = "ai"
        obs[1]["annotation_source"] = "none"
        slices = build_slice_metrics(obs)
        regime_slices = [s for s in slices if s["slice_dimension"] == "regime_label"]
        unlabeled = [s for s in regime_slices if s["label"] == "unlabeled"]
        assert len(unlabeled) == 1
        assert unlabeled[0]["observation_count"] == 1

    def test_event_tag_expansion(self) -> None:
        obs = [
            _make_observation(
                strategy_kind="ugh", event_tags="fomc|cpi_us",
                annotation_status="confirmed",
            ),
        ]
        obs[0]["annotation_source"] = "ai"
        obs[0]["effective_event_tags"] = "cpi_us|fomc"
        slices = build_slice_metrics(obs)
        tag_slices = [s for s in slices if s["slice_dimension"] == "event_tag"]
        tags = {s["label"] for s in tag_slices}
        assert "fomc" in tags
        assert "cpi_us" in tags

    def test_volatility_slice(self) -> None:
        obs = [
            _make_observation(
                strategy_kind="ugh", volatility_label="high",
                annotation_status="confirmed",
            ),
        ]
        obs[0]["annotation_source"] = "ai"
        slices = build_slice_metrics(obs)
        vol_slices = [s for s in slices if s["slice_dimension"] == "volatility_label"]
        assert len(vol_slices) >= 1
        assert vol_slices[0]["label"] == "high"

    def test_intervention_risk_slice(self) -> None:
        obs = [
            _make_observation(
                strategy_kind="ugh", intervention_risk="high",
                annotation_status="confirmed",
            ),
        ]
        obs[0]["annotation_source"] = "ai"
        slices = build_slice_metrics(obs)
        ir_slices = [s for s in slices if s["slice_dimension"] == "intervention_risk"]
        assert len(ir_slices) >= 1
        assert ir_slices[0]["label"] == "high"

    def test_no_annotations_still_produces_slices(self) -> None:
        """Without any annotations (AI or manual), slice metrics should still be
        generated using an 'all' label per strategy."""
        obs = [
            _make_observation(
                strategy_kind="ugh", direction_hit="True", annotation_status=""
            ),
            _make_observation(
                strategy_kind="ugh", direction_hit="False", annotation_status=""
            ),
            _make_observation(
                strategy_kind="baseline_random_walk", direction_hit="True",
                annotation_status="",
            ),
        ]
        for o in obs:
            o["annotation_source"] = "none"
        slices = build_slice_metrics(obs)
        assert len(slices) > 0
        for dim in ("regime_label", "volatility_label", "intervention_risk"):
            dim_slices = [s for s in slices if s["slice_dimension"] == dim]
            assert len(dim_slices) >= 1
            for s in dim_slices:
                assert s["label"] == "all"
        ugh_regime = [
            s for s in slices
            if s["slice_dimension"] == "regime_label" and s["strategy_kind"] == "ugh"
        ]
        assert ugh_regime[0]["observation_count"] == 2
        assert ugh_regime[0]["direction_hit_count"] == 1


# ---------------------------------------------------------------------------
# Tests: provider health summary
# ---------------------------------------------------------------------------


class TestProviderHealthSummary:
    def test_basic_summary(self) -> None:
        rows = [
            {
                "as_of_jst": "2026-03-18T08:00:00+09:00",
                "provider_name": "alphavantage",
                "used_fallback_adjustment": "False",
                "snapshot_lag_business_days": "0",
                "run_status": "success",
            },
            {
                "as_of_jst": "2026-03-19T08:00:00+09:00",
                "provider_name": "alphavantage",
                "used_fallback_adjustment": "True",
                "snapshot_lag_business_days": "1",
                "run_status": "success",
            },
        ]
        summary = build_provider_health_summary(rows)
        assert summary["total_runs"] == 2
        assert summary["providers"]["alphavantage"] == 2
        assert summary["fallback_adjustment_count"] == 1
        assert summary["lag_count"] == 1
        assert summary["success_count"] == 2

    def test_empty_health(self) -> None:
        summary = build_provider_health_summary([])
        assert summary["total_runs"] == 0

    def test_failed_status(self) -> None:
        rows = [
            {
                "as_of_jst": "2026-03-18T08:00:00+09:00",
                "provider_name": "yahoo",
                "used_fallback_adjustment": "False",
                "snapshot_lag_business_days": "0",
                "run_status": "failed",
            },
        ]
        summary = build_provider_health_summary(rows)
        assert summary["failed_count"] == 1
        assert summary["success_count"] == 0

    def test_ok_and_idempotent_skip_statuses(self) -> None:
        """Verify that actual automation run_status values are counted correctly."""
        rows = [
            {
                "as_of_jst": "2026-03-17T08:00:00+09:00",
                "provider_name": "alphavantage",
                "used_fallback_adjustment": "False",
                "snapshot_lag_business_days": "0",
                "run_status": "ok",
            },
            {
                "as_of_jst": "2026-03-18T08:00:00+09:00",
                "provider_name": "alphavantage",
                "used_fallback_adjustment": "False",
                "snapshot_lag_business_days": "0",
                "run_status": "idempotent_skip",
            },
        ]
        summary = build_provider_health_summary(rows)
        assert summary["total_runs"] == 2
        assert summary["success_count"] == 1
        assert summary["skipped_count"] == 1
        assert summary["failed_count"] == 0


# ---------------------------------------------------------------------------
# Tests: full v2 report
# ---------------------------------------------------------------------------


class TestRunWeeklyReportV2:
    def test_full_report_with_data(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        obs = [
            _make_observation(
                as_of_jst="2026-03-18T08:00:00+09:00",
                strategy_kind="ugh",
                annotation_status="confirmed",
                direction_hit="True",
            ),
            _make_observation(
                as_of_jst="2026-03-19T08:00:00+09:00",
                strategy_kind="ugh",
                annotation_status="pending",
                direction_hit="False",
            ),
            _make_observation(
                as_of_jst="2026-03-18T08:00:00+09:00",
                strategy_kind="baseline_random_walk",
                annotation_status="confirmed",
                direction_hit="True",
            ),
        ]
        _setup_labeled_observations(tmpdir, obs)

        report = run_weekly_report_v2(
            tmpdir, _REPORT_DATE, generated_at_utc=_NOW
        )

        assert report["report_version"] == "v2"
        assert report["observation_count"] == 3
        cov = report["annotation_coverage"]
        assert cov["confirmed_annotation_count"] == 2
        assert cov["pending_annotation_count"] == 1
        assert len(report["strategy_metrics"]) == 2
        assert len(report["slice_metrics"]) > 0

    def test_empty_history(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        report = run_weekly_report_v2(
            tmpdir, _REPORT_DATE, generated_at_utc=_NOW
        )
        assert report["observation_count"] == 0
        assert report["annotation_coverage"]["total_observations"] == 0

    def test_v1_compatibility_not_broken(self) -> None:
        """Verify that v1 weekly report models are still importable."""
        from ugh_quantamental.fx_protocol.report_models import (
            WeeklyReportRequest,
        )
        # v1 models must still exist and be constructible
        req = WeeklyReportRequest(
            pair="USDJPY",
            report_generated_at_jst=_REPORT_DATE,
        )
        assert req.business_day_count == 5

    def test_existing_forecast_logic_unchanged(self) -> None:
        """Verify that existing ForecastRecord model is unchanged."""
        from ugh_quantamental.fx_protocol.models import (
            ForecastRecord,
            StrategyKind,
        )
        # If the model schema changed, this would fail
        assert hasattr(ForecastRecord, "model_fields")
        assert "forecast_id" in ForecastRecord.model_fields
        assert StrategyKind.ugh.value == "ugh"

    def test_core_analysis_ready_with_observations(self, tmp_path: str) -> None:
        """core_analysis_ready should be True when observations exist."""
        tmpdir = str(tmp_path)
        obs = [_make_observation(annotation_status="")]
        _setup_labeled_observations(tmpdir, obs)
        report = run_weekly_report_v2(tmpdir, _REPORT_DATE, generated_at_utc=_NOW)
        assert report["core_analysis_ready"] is True
        assert report["annotated_analysis_ready"] is False

    def test_annotated_analysis_ready_with_ai_source(self, tmp_path: str) -> None:
        """annotated_analysis_ready is True when AI annotations exist."""
        tmpdir = str(tmp_path)
        obs = [_make_observation(annotation_status="")]
        obs[0]["annotation_source"] = "ai"
        _setup_labeled_observations(tmpdir, obs)
        report = run_weekly_report_v2(tmpdir, _REPORT_DATE, generated_at_utc=_NOW)
        assert report["annotated_analysis_ready"] is True

    def test_empty_report_not_ready(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        report = run_weekly_report_v2(tmpdir, _REPORT_DATE, generated_at_utc=_NOW)
        assert report["core_analysis_ready"] is False
        assert report["annotated_analysis_ready"] is False


# ---------------------------------------------------------------------------
# Tests: field-level annotation coverage
# ---------------------------------------------------------------------------


class TestAnnotationFieldCoverage:
    def test_all_unannotated(self) -> None:
        obs = [
            _make_observation(
                regime_label="", event_tags="", volatility_label="",
                intervention_risk="", annotation_status="",
            ),
            _make_observation(
                regime_label="", event_tags="", volatility_label="",
                intervention_risk="", annotation_status="",
            ),
        ]
        for o in obs:
            o["annotation_source"] = "none"
        fc = build_annotation_field_coverage(obs)
        assert fc["regime_label"]["total_observations"] == 2
        assert fc["regime_label"]["effective_populated_count"] == 0
        assert fc["regime_label"]["missing_count"] == 2

    def test_ai_populated(self) -> None:
        obs = [
            _make_observation(regime_label="trending"),
        ]
        obs[0]["annotation_source"] = "ai"
        obs[0]["ai_regime_label"] = "trending"
        fc = build_annotation_field_coverage(obs)
        assert fc["regime_label"]["ai_populated_count"] == 1
        assert fc["regime_label"]["effective_populated_count"] == 1
        assert fc["regime_label"]["missing_count"] == 0

    def test_empty_observations(self) -> None:
        fc = build_annotation_field_coverage([])
        for field in ("regime_label", "event_tags", "volatility_label",
                      "intervention_risk", "failure_reason"):
            assert fc[field]["total_observations"] == 0


# ---------------------------------------------------------------------------
# Tests: event-tag source summary
# ---------------------------------------------------------------------------


class TestEventTagSourceSummary:
    def test_counts_sources(self) -> None:
        obs = [
            {"annotation_source": "ai"},
            {"annotation_source": "auto_only"},
            {"annotation_source": "auto_only"},
            {"annotation_source": "ai_plus_auto"},
            {"annotation_source": "none"},
        ]
        summary = build_event_tag_source_summary(obs)
        assert summary["ai"] == 1
        assert summary["auto_only"] == 2
        assert summary["ai_plus_auto"] == 1
        assert summary["none"] == 1

    def test_empty_defaults_to_none(self) -> None:
        obs = [{"annotation_source": ""}, {}]
        summary = build_event_tag_source_summary(obs)
        assert summary["none"] == 2


# ---------------------------------------------------------------------------
# Tests: event-tag slices from effective_event_tags without annotations
# ---------------------------------------------------------------------------


class TestEventTagSlicesWithoutAnnotations:
    def test_event_tag_slices_from_auto_tags(self) -> None:
        """Event-tag slices should appear from effective_event_tags even when
        manual annotation coverage is zero."""
        obs = [
            _make_observation(
                strategy_kind="ugh",
                direction_hit="True",
                annotation_status="",
                event_tags="fomc",
            ),
            _make_observation(
                strategy_kind="ugh",
                direction_hit="False",
                annotation_status="",
                event_tags="fomc|month_end",
            ),
        ]
        for o in obs:
            o["effective_event_tags"] = o["event_tags"]
            o["annotation_source"] = "auto_only"

        slices = build_slice_metrics(obs)
        tag_slices = [s for s in slices if s["slice_dimension"] == "event_tag"]
        assert len(tag_slices) >= 1
        tags = {s["label"] for s in tag_slices}
        assert "fomc" in tags
