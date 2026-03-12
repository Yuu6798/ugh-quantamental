"""Tests for RegressionSuiteBaselineRepository and the Alembic migration."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None
HAS_ALEMBIC = importlib.util.find_spec("alembic") is not None


def _make_session():
    """Return a fresh in-memory SQLite session with all tables created."""
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine()
    create_all_tables(engine)
    return create_session_factory(engine)()


_SAMPLE_REQUEST_JSON: dict = {
    "projection_cases": [
        {
            "name": "smoke",
            "run_ids": ["r-001"],
            "query": None,
            "deduplicate_run_ids": True,
        }
    ],
    "state_cases": [],
}

_SAMPLE_RESULT_JSON: dict = {
    "aggregate": {
        "projection_case_count": 1,
        "state_case_count": 0,
        "total_case_count": 1,
        "passed_case_count": 1,
        "failed_case_count": 0,
        "total_projection_requested": 1,
        "total_state_requested": 0,
        "total_missing_count": 0,
        "total_error_count": 0,
        "total_mismatch_count": 0,
    },
    "projection_cases": [
        {
            "name": "smoke",
            "passed": True,
            "batch_aggregate": {
                "requested_count": 1,
                "replayed_count": 1,
                "exact_match_count": 1,
                "mismatch_count": 0,
                "missing_count": 0,
                "error_count": 0,
                "max_point_estimate_diff": 0.0,
                "max_confidence_diff": 0.0,
                "max_mismatch_px_diff": 0.0,
                "max_mismatch_sem_diff": 0.0,
                "max_conviction_diff": 0.0,
                "max_urgency_diff": 0.0,
            },
        }
    ],
    "state_cases": [],
}


# ---------------------------------------------------------------------------
# save_baseline / load_baseline round-trip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_save_and_load_baseline_by_id() -> None:
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    with _make_session() as session:
        RegressionSuiteBaselineRepository.save_baseline(
            session,
            baseline_id="base_001",
            baseline_name="golden-v1",
            suite_request_json=_SAMPLE_REQUEST_JSON,
            suite_result_json=_SAMPLE_RESULT_JSON,
        )
        session.flush()

        run = RegressionSuiteBaselineRepository.load_baseline(session, "base_001")

    assert run is not None
    assert run.baseline_id == "base_001"
    assert run.baseline_name == "golden-v1"
    assert run.description is None
    assert run.suite_request_json == _SAMPLE_REQUEST_JSON
    assert run.suite_result_json == _SAMPLE_RESULT_JSON
    # created_at is naive UTC
    assert run.created_at.tzinfo is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_save_and_load_baseline_by_name() -> None:
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    with _make_session() as session:
        RegressionSuiteBaselineRepository.save_baseline(
            session,
            baseline_id="base_002",
            baseline_name="golden-by-name",
            suite_request_json=_SAMPLE_REQUEST_JSON,
            suite_result_json=_SAMPLE_RESULT_JSON,
            description="test description",
        )
        session.flush()

        run = RegressionSuiteBaselineRepository.load_baseline_by_name(
            session, "golden-by-name"
        )

    assert run is not None
    assert run.baseline_id == "base_002"
    assert run.description == "test description"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_load_baseline_missing_returns_none() -> None:
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    with _make_session() as session:
        result = RegressionSuiteBaselineRepository.load_baseline(session, "base_nonexistent")

    assert result is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_load_baseline_by_name_missing_returns_none() -> None:
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    with _make_session() as session:
        result = RegressionSuiteBaselineRepository.load_baseline_by_name(
            session, "does-not-exist"
        )

    assert result is None


# ---------------------------------------------------------------------------
# created_at normalisation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_created_at_aware_input_normalised_to_naive_utc() -> None:
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    aware = datetime(2026, 3, 15, 10, 30, 0, tzinfo=timezone.utc)

    with _make_session() as session:
        RegressionSuiteBaselineRepository.save_baseline(
            session,
            baseline_id="base_tz",
            baseline_name="tz-test",
            created_at=aware,
            suite_request_json=_SAMPLE_REQUEST_JSON,
            suite_result_json=_SAMPLE_RESULT_JSON,
        )
        session.flush()
        run = RegressionSuiteBaselineRepository.load_baseline(session, "base_tz")

    assert run is not None
    assert run.created_at.tzinfo is None
    assert run.created_at == datetime(2026, 3, 15, 10, 30, 0)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_created_at_naive_input_stored_as_is() -> None:
    from ugh_quantamental.persistence.repositories import RegressionSuiteBaselineRepository

    naive = datetime(2026, 3, 15, 10, 30, 0)

    with _make_session() as session:
        RegressionSuiteBaselineRepository.save_baseline(
            session,
            baseline_id="base_naive",
            baseline_name="naive-test",
            created_at=naive,
            suite_request_json=_SAMPLE_REQUEST_JSON,
            suite_result_json=_SAMPLE_RESULT_JSON,
        )
        session.flush()
        run = RegressionSuiteBaselineRepository.load_baseline(session, "base_naive")

    assert run is not None
    assert run.created_at == naive


# ---------------------------------------------------------------------------
# create_all_tables includes baseline table
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_create_all_tables_includes_baseline_table() -> None:
    from sqlalchemy import inspect

    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine

    engine = create_db_engine()
    create_all_tables(engine)
    table_names = set(inspect(engine).get_table_names())
    assert "regression_suite_baselines" in table_names


# ---------------------------------------------------------------------------
# Alembic migration creates the baseline table
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (HAS_SQLALCHEMY and HAS_ALEMBIC), reason="persistence deps not installed"
)
def test_alembic_migration_creates_baseline_table(tmp_path: Path) -> None:
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    from ugh_quantamental.persistence.db import create_db_engine

    db_path = tmp_path / "alembic_baseline.db"
    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(config, "head")

    engine = create_db_engine(f"sqlite:///{db_path}")
    table_names = set(inspect(engine).get_table_names())
    assert {
        "alembic_version",
        "projection_runs",
        "state_runs",
        "regression_suite_baselines",
    }.issubset(table_names)
