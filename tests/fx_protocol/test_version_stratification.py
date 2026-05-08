"""Tests for spec §7.5 theory_version / engine_version stratification.

The v1 → v2 cut-over bumps both ``theory_version`` and ``engine_version``
on every newly-emitted forecast batch. Without stratification, the boundary
week / month would silently mix v1 and v2 records under shared baseline
``strategy_kind`` values (the baselines keep their identifiers across the
boundary), producing per-strategy metrics that span both theory versions
and are not interpretable as either pure-v1 or pure-v2.
"""

from __future__ import annotations

import pytest

# Phase 3a: both _stratify_by_versions (weekly) and _stratify_observations_by_versions
# (monthly) were consolidated into a single canonical helper in report_window.
# Aliases here keep the existing two test classes' calling conventions.
from ugh_quantamental.fx_protocol.report_window import (
    stratify_observations_by_versions as _stratify_by_versions,
)
from ugh_quantamental.fx_protocol.report_window import (
    stratify_observations_by_versions as _stratify_observations_by_versions,
)


@pytest.fixture()
def mixed_rows() -> list[dict[str, str]]:
    """Six rows: 3 v1, 3 v2, mixed across baselines + UGH variants."""
    return [
        {"strategy_kind": "ugh", "theory_version": "v1", "engine_version": "v1"},
        {"strategy_kind": "baseline_random_walk", "theory_version": "v1", "engine_version": "v1"},
        {"strategy_kind": "baseline_simple_technical", "theory_version": "v1", "engine_version": "v1"},
        {"strategy_kind": "ugh_v2_alpha", "theory_version": "v2", "engine_version": "v2"},
        {"strategy_kind": "baseline_random_walk", "theory_version": "v2", "engine_version": "v2"},
        {"strategy_kind": "baseline_simple_technical", "theory_version": "v2", "engine_version": "v2"},
    ]


@pytest.fixture()
def single_version_rows() -> list[dict[str, str]]:
    return [
        {"strategy_kind": "ugh_v2_alpha", "theory_version": "v2", "engine_version": "v2"},
        {"strategy_kind": "baseline_random_walk", "theory_version": "v2", "engine_version": "v2"},
    ]


# ---------------------------------------------------------------------------
# weekly_reports_v2 stratification
# ---------------------------------------------------------------------------


class TestWeeklyStratifyByVersions:
    def test_auto_detect_filters_to_latest_when_mixed(
        self, mixed_rows: list[dict[str, str]], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Auto mode: latest theory_version (v2) wins; v1 rows dropped."""
        with caplog.at_level("WARNING"):
            out = _stratify_by_versions(mixed_rows)
        assert len(out) == 3
        assert {r["theory_version"] for r in out} == {"v2"}
        # Warning log captures the mixed-version diagnostic.
        assert any("auto-stratifying" in rec.message for rec in caplog.records)

    def test_auto_detect_no_op_for_single_version(
        self, single_version_rows: list[dict[str, str]]
    ) -> None:
        """Single-version data must be returned unchanged (no warning, no filtering)."""
        out = _stratify_by_versions(single_version_rows)
        assert out == single_version_rows

    def test_explicit_theory_version_filter(self, mixed_rows: list[dict[str, str]]) -> None:
        out = _stratify_by_versions(mixed_rows, theory_version_filter="v1")
        assert len(out) == 3
        assert {r["theory_version"] for r in out} == {"v1"}

    def test_explicit_engine_version_filter(self, mixed_rows: list[dict[str, str]]) -> None:
        out = _stratify_by_versions(mixed_rows, engine_version_filter="v2")
        assert len(out) == 3
        assert {r["engine_version"] for r in out} == {"v2"}

    def test_explicit_filter_drops_rows_with_missing_column(self) -> None:
        """An explicit filter must not silently keep version-less rows."""
        rows = [
            {"strategy_kind": "ugh_v2_alpha", "theory_version": "v2"},
            {"strategy_kind": "baseline_random_walk"},  # no theory_version
        ]
        out = _stratify_by_versions(rows, theory_version_filter="v2")
        assert len(out) == 1
        assert out[0]["strategy_kind"] == "ugh_v2_alpha"

    def test_empty_input_returns_empty(self) -> None:
        assert _stratify_by_versions([]) == []


# ---------------------------------------------------------------------------
# monthly_review stratification — same contract, separate function
# ---------------------------------------------------------------------------


class TestMonthlyStratifyByVersions:
    def test_auto_detect_filters_to_latest_when_mixed(
        self, mixed_rows: list[dict[str, str]]
    ) -> None:
        out = _stratify_observations_by_versions(mixed_rows)
        assert len(out) == 3
        assert {r["theory_version"] for r in out} == {"v2"}

    def test_auto_detect_no_op_for_single_version(
        self, single_version_rows: list[dict[str, str]]
    ) -> None:
        out = _stratify_observations_by_versions(single_version_rows)
        assert out == single_version_rows

    def test_explicit_theory_version_filter(self, mixed_rows: list[dict[str, str]]) -> None:
        out = _stratify_observations_by_versions(
            mixed_rows, theory_version_filter="v2"
        )
        assert len(out) == 3
        assert {r["theory_version"] for r in out} == {"v2"}


# ---------------------------------------------------------------------------
# Result payload audit fields (spec §7.5 closure clarity)
# ---------------------------------------------------------------------------


def test_run_monthly_review_records_versions_in_window() -> None:
    """``run_monthly_review`` echoes the surviving theory/engine versions."""
    from ugh_quantamental.fx_protocol.monthly_review import run_monthly_review

    observations = [
        {
            "strategy_kind": "ugh_v2_alpha",
            "theory_version": "v2",
            "engine_version": "v2",
            "as_of_jst": "2026-05-04T08:00:00+09:00",
            "direction_hit": "true",
            "close_error_bp": "10",
            "annotation_status": "confirmed",
            "regime_label": "trending",
        },
    ]
    result = run_monthly_review(observations, health_rows=[])
    assert result["theory_versions_in_window"] == ["v2"]
    assert result["engine_versions_in_window"] == ["v2"]


def test_run_weekly_report_v2_records_versions_in_window(tmp_path) -> None:
    """``run_weekly_report_v2`` echoes the surviving theory/engine versions.

    Uses an empty CSV root (no observations); the ``theory_versions_in_window``
    field should be present and empty rather than missing.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from ugh_quantamental.fx_protocol.weekly_reports_v2 import run_weekly_report_v2

    _JST = ZoneInfo("Asia/Tokyo")
    result = run_weekly_report_v2(
        str(tmp_path),
        datetime(2026, 5, 9, 8, 0, 0, tzinfo=_JST),
    )
    assert result["theory_versions_in_window"] == []
    assert result["engine_versions_in_window"] == []
