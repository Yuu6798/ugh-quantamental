"""Tests for report_window version stratification."""

from __future__ import annotations

import pytest

from ugh_quantamental.fx_protocol.report_window import (
    stratify_observations_by_versions,
)


def test_auto_detect_filters_mixed_engine_version_to_latest(
    caplog: pytest.LogCaptureFixture,
) -> None:
    rows = [
        {"id": "old", "theory_version": "v2", "engine_version": "v2"},
        {"id": "new", "theory_version": "v2", "engine_version": "v2.1"},
        {"id": "missing", "theory_version": "v2"},
    ]

    with caplog.at_level("WARNING"):
        out = stratify_observations_by_versions(rows)

    assert [row["id"] for row in out] == ["new"]
    assert any("mixed engine_versions" in rec.message for rec in caplog.records)


def test_auto_detect_filters_mixed_theory_then_engine_versions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    rows = [
        {"id": "v1-high-engine", "theory_version": "v1", "engine_version": "v9"},
        {"id": "v2-old-engine", "theory_version": "v2", "engine_version": "v2"},
        {"id": "v2-new-engine", "theory_version": "v2", "engine_version": "v2.1"},
    ]

    with caplog.at_level("WARNING"):
        out = stratify_observations_by_versions(rows)

    assert [row["id"] for row in out] == ["v2-new-engine"]
    messages = [rec.message for rec in caplog.records]
    assert "mixed theory_versions" in messages[0]
    assert "mixed engine_versions" in messages[1]


def test_auto_detect_returns_single_or_absent_engine_version_unchanged() -> None:
    rows = [
        {"id": "single", "theory_version": "v2", "engine_version": "v2"},
        {"id": "absent", "theory_version": "v2"},
        {"id": "empty", "theory_version": "v2", "engine_version": ""},
    ]

    out = stratify_observations_by_versions(rows)

    assert out is rows


def test_explicit_version_filters_still_pin_requested_versions() -> None:
    rows = [
        {"id": "v1-e1", "theory_version": "v1", "engine_version": "v1"},
        {"id": "v2-e2", "theory_version": "v2", "engine_version": "v2"},
        {"id": "v2-e21", "theory_version": "v2", "engine_version": "v2.1"},
        {"id": "missing", "theory_version": "v2"},
    ]

    out = stratify_observations_by_versions(
        rows,
        theory_version_filter="v2",
        engine_version_filter="v2",
    )

    assert [row["id"] for row in out] == ["v2-e2"]


def test_stratify_docstring_frames_theory_and_engine_version_symmetrically() -> None:
    doc = stratify_observations_by_versions.__doc__ or ""

    assert "Spec" in doc
    assert "``theory_version`` and ``engine_version``" in doc
    assert "same latest-version stratification" in doc
