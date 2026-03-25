"""Tests for monthly review v1 — export helpers and full rebuild orchestrator."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.monthly_review import run_monthly_review
from ugh_quantamental.fx_protocol.monthly_review_exports import (
    _enrich_observations_with_forecast_data,
    _filter_observations_by_pair,
    build_monthly_review_md,
    export_monthly_review_artifacts,
    export_monthly_review_flags_csv,
    export_monthly_review_json,
    export_monthly_review_md,
    export_monthly_strategy_metrics_csv,
    rebuild_monthly_review,
)

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc
_NOW = datetime(2026, 4, 1, 6, 0, 0, tzinfo=_UTC)
_REVIEW_DATE = datetime(2026, 4, 1, 8, 0, 0, tzinfo=_JST)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_obs(
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
    dominant_state: str = "fire",
    forecast_direction: str = "up",
    realized_direction: str = "up",
    expected_close_change_bp: str = "20.0",
    realized_close_change_bp: str = "18.0",
) -> dict[str, str]:
    return {
        "as_of_jst": as_of_jst,
        "strategy_kind": strategy_kind,
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
        "dominant_state": dominant_state,
        "forecast_direction": forecast_direction,
        "realized_direction": realized_direction,
        "expected_close_change_bp": expected_close_change_bp,
        "realized_close_change_bp": realized_close_change_bp,
    }


def _make_health(
    *,
    as_of_jst: str = "2026-03-18T08:00:00+09:00",
    provider_name: str = "alphavantage",
    used_fallback_adjustment: str = "False",
    snapshot_lag_business_days: str = "0",
    run_status: str = "success",
) -> dict[str, str]:
    return {
        "as_of_jst": as_of_jst,
        "provider_name": provider_name,
        "used_fallback_adjustment": used_fallback_adjustment,
        "snapshot_lag_business_days": snapshot_lag_business_days,
        "run_status": run_status,
    }


def _write_csv_file(
    path: str, rows: list[dict[str, str]], fieldnames: list[str]
) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _labeled_observation_fieldnames() -> list[str]:
    return [
        "as_of_jst", "strategy_kind", "direction_hit", "range_hit",
        "state_proxy_hit", "close_error_bp", "magnitude_error_bp",
        "regime_label", "event_tags", "volatility_label", "intervention_risk",
        "annotation_status", "dominant_state", "forecast_direction",
        "realized_direction", "expected_close_change_bp", "realized_close_change_bp",
    ]


def _provider_health_fieldnames() -> list[str]:
    return [
        "as_of_jst", "provider_name", "used_fallback_adjustment",
        "snapshot_lag_business_days", "run_status",
    ]


def _build_review() -> dict:
    obs = [
        _make_obs(as_of_jst="2026-03-18T08:00:00+09:00", strategy_kind="ugh"),
        _make_obs(as_of_jst="2026-03-19T08:00:00+09:00", strategy_kind="ugh"),
        _make_obs(
            as_of_jst="2026-03-18T08:00:00+09:00",
            strategy_kind="baseline_random_walk",
        ),
    ]
    health = [_make_health()]
    return run_monthly_review(
        obs, health,
        review_generated_at_jst=_REVIEW_DATE,
        business_day_count=20,
    )


# ---------------------------------------------------------------------------
# Tests: JSON export
# ---------------------------------------------------------------------------


class TestExportJson:
    def test_json_export(self, tmp_path: str) -> None:
        review = _build_review()
        path = export_monthly_review_json(review, str(tmp_path))
        assert os.path.isfile(path)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["review_version"] == "v1"


# ---------------------------------------------------------------------------
# Tests: Markdown export
# ---------------------------------------------------------------------------


class TestExportMarkdown:
    def test_md_export(self, tmp_path: str) -> None:
        review = _build_review()
        path = export_monthly_review_md(review, str(tmp_path))
        assert os.path.isfile(path)
        content = open(path, encoding="utf-8").read()
        assert "# FX Monthly Review v1" in content
        assert "Strategy Performance" in content
        assert "Review Flags" in content
        assert "Provider Health" in content
        assert "Annotation Coverage" in content

    def test_md_content_sections(self) -> None:
        review = _build_review()
        md = build_monthly_review_md(review)
        assert "Baseline Comparisons" in md
        assert "Recommendation Summary" in md
        assert "No forecast logic was re-executed" in md


# ---------------------------------------------------------------------------
# Tests: CSV export
# ---------------------------------------------------------------------------


class TestExportCsv:
    def test_strategy_metrics_csv(self, tmp_path: str) -> None:
        review = _build_review()
        path = export_monthly_strategy_metrics_csv(review, str(tmp_path))
        assert os.path.isfile(path)
        with open(path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) >= 4
        assert rows[0]["strategy_kind"] in (
            "ugh", "baseline_random_walk",
            "baseline_prev_day_direction", "baseline_simple_technical",
        )

    def test_review_flags_csv(self, tmp_path: str) -> None:
        review = _build_review()
        path = export_monthly_review_flags_csv(review, str(tmp_path))
        assert os.path.isfile(path)
        with open(path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) >= 1
        assert "flag" in rows[0]
        assert "reason" in rows[0]


# ---------------------------------------------------------------------------
# Tests: full artifact export
# ---------------------------------------------------------------------------


class TestExportArtifacts:
    def test_artifact_export_creates_all_files(self, tmp_path: str) -> None:
        review = _build_review()
        paths = export_monthly_review_artifacts(review, str(tmp_path), "202603")

        assert "monthly_review_json" in paths
        assert "monthly_review_md" in paths
        assert "monthly_strategy_metrics_csv" in paths
        assert "monthly_slice_metrics_csv" in paths
        assert "monthly_review_flags_csv" in paths

        for p in paths.values():
            assert os.path.isfile(p)

    def test_latest_mirror(self, tmp_path: str) -> None:
        review = _build_review()
        export_monthly_review_artifacts(review, str(tmp_path), "202603")

        latest_dir = os.path.join(str(tmp_path), "analytics", "monthly", "latest")
        assert os.path.isdir(latest_dir)
        for filename in [
            "monthly_review.json",
            "monthly_review.md",
            "monthly_strategy_metrics.csv",
            "monthly_slice_metrics.csv",
            "monthly_review_flags.csv",
        ]:
            assert os.path.isfile(os.path.join(latest_dir, filename))

    def test_generated_artifact_paths_populated(self, tmp_path: str) -> None:
        review = _build_review()
        export_monthly_review_artifacts(review, str(tmp_path), "202603")
        assert len(review["generated_artifact_paths"]) == 5


# ---------------------------------------------------------------------------
# Tests: rebuild orchestrator
# ---------------------------------------------------------------------------


class TestRebuildMonthlyReview:
    def test_rebuild_with_data(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        obs = [
            _make_obs(as_of_jst="2026-03-18T08:00:00+09:00", strategy_kind="ugh"),
            _make_obs(as_of_jst="2026-03-19T08:00:00+09:00", strategy_kind="ugh"),
            _make_obs(
                as_of_jst="2026-03-18T08:00:00+09:00",
                strategy_kind="baseline_random_walk",
            ),
        ]
        obs_path = os.path.join(tmpdir, "analytics", "labeled_observations.csv")
        _write_csv_file(obs_path, obs, _labeled_observation_fieldnames())

        health = [
            _make_health(as_of_jst="2026-03-18T08:00:00+09:00"),
        ]
        health_path = os.path.join(tmpdir, "latest", "provider_health.csv")
        _write_csv_file(health_path, health, _provider_health_fieldnames())

        review = rebuild_monthly_review(
            tmpdir, _REVIEW_DATE,
            business_day_count=20,
            generated_at_utc=_NOW,
        )

        assert review["review_version"] == "v1"
        assert len(review["generated_artifact_paths"]) == 5

        # Check artifacts exist
        monthly_dir = os.path.join(tmpdir, "analytics", "monthly", "202604")
        assert os.path.isdir(monthly_dir)
        assert os.path.isfile(os.path.join(monthly_dir, "monthly_review.json"))
        assert os.path.isfile(os.path.join(monthly_dir, "monthly_review.md"))

    def test_rebuild_empty_data(self, tmp_path: str) -> None:
        tmpdir = str(tmp_path)
        review = rebuild_monthly_review(
            tmpdir, _REVIEW_DATE,
            business_day_count=20,
            generated_at_utc=_NOW,
        )
        assert review["included_window_count"] == 0
        assert any(f["flag"] == "insufficient_data" for f in review["review_flags"])


# ---------------------------------------------------------------------------
# Tests: observation enrichment and pair filtering
# ---------------------------------------------------------------------------


class TestEnrichObservationsWithForecastData:
    def test_dominant_state_populated(self) -> None:
        obs = [
            {"as_of_jst": "2026-03-18T08:00:00+09:00", "strategy_kind": "ugh",
             "forecast_batch_id": "batch_001", "dominant_state": ""},
        ]
        lookup = {
            ("batch_001", "ugh", "20260318"): {"dominant_state": "fire", "pair": "USDJPY"},
        }
        enriched = _enrich_observations_with_forecast_data(obs, lookup)
        assert enriched[0]["dominant_state"] == "fire"
        assert enriched[0]["pair"] == "USDJPY"

    def test_does_not_overwrite_existing(self) -> None:
        obs = [
            {"as_of_jst": "2026-03-18T08:00:00+09:00", "strategy_kind": "ugh",
             "forecast_batch_id": "batch_001",
             "dominant_state": "dormant", "pair": "USDJPY"},
        ]
        lookup = {
            ("batch_001", "ugh", "20260318"): {"dominant_state": "fire", "pair": "EURUSD"},
        }
        enriched = _enrich_observations_with_forecast_data(obs, lookup)
        assert enriched[0]["dominant_state"] == "dormant"
        assert enriched[0]["pair"] == "USDJPY"

    def test_missing_lookup_entry(self) -> None:
        obs = [
            {"as_of_jst": "2026-03-18T08:00:00+09:00", "strategy_kind": "ugh",
             "forecast_batch_id": "batch_001", "dominant_state": ""},
        ]
        enriched = _enrich_observations_with_forecast_data(obs, {})
        assert enriched[0]["dominant_state"] == ""

    def test_disambiguates_by_batch_id(self) -> None:
        """Different batch IDs on the same date/strategy get correct data."""
        obs = [
            {"as_of_jst": "2026-03-18T08:00:00+09:00", "strategy_kind": "ugh",
             "forecast_batch_id": "batch_A", "dominant_state": ""},
            {"as_of_jst": "2026-03-18T08:00:00+09:00", "strategy_kind": "ugh",
             "forecast_batch_id": "batch_B", "dominant_state": ""},
        ]
        lookup = {
            ("batch_A", "ugh", "20260318"): {
                "dominant_state": "fire", "pair": "USDJPY",
            },
            ("batch_B", "ugh", "20260318"): {
                "dominant_state": "dormant", "pair": "EURUSD",
            },
        }
        enriched = _enrich_observations_with_forecast_data(obs, lookup)
        assert enriched[0]["dominant_state"] == "fire"
        assert enriched[0]["pair"] == "USDJPY"
        assert enriched[1]["dominant_state"] == "dormant"
        assert enriched[1]["pair"] == "EURUSD"


class TestFilterObservationsByPair:
    def test_filters_to_pair(self) -> None:
        obs = [
            {"pair": "USDJPY", "strategy_kind": "ugh"},
            {"pair": "EURUSD", "strategy_kind": "ugh"},
            {"pair": "USDJPY", "strategy_kind": "baseline_random_walk"},
        ]
        filtered = _filter_observations_by_pair(obs, "USDJPY")
        assert len(filtered) == 2
        assert all(r["pair"] == "USDJPY" for r in filtered)

    def test_includes_rows_without_pair(self) -> None:
        obs = [
            {"pair": "", "strategy_kind": "ugh"},
            {"strategy_kind": "ugh"},
            {"pair": "USDJPY", "strategy_kind": "ugh"},
        ]
        filtered = _filter_observations_by_pair(obs, "USDJPY")
        assert len(filtered) == 3

    def test_case_insensitive(self) -> None:
        obs = [
            {"pair": "usdjpy", "strategy_kind": "ugh"},
        ]
        filtered = _filter_observations_by_pair(obs, "USDJPY")
        assert len(filtered) == 1
