"""Tests for query model validation (no SQLAlchemy required)."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from ugh_quantamental.query.models import (
    CreatedAtRange,
    ProjectionRunQuery,
    ProjectionRunSummary,
    StateRunQuery,
    StateRunSummary,
)


# ---------------------------------------------------------------------------
# CreatedAtRange
# ---------------------------------------------------------------------------


def test_created_at_range_defaults_to_none() -> None:
    r = CreatedAtRange()
    assert r.created_at_from is None
    assert r.created_at_to is None


def test_created_at_range_with_both_bounds() -> None:
    lo = datetime(2026, 1, 1)
    hi = datetime(2026, 3, 1)
    r = CreatedAtRange(created_at_from=lo, created_at_to=hi)
    assert r.created_at_from == lo
    assert r.created_at_to == hi


def test_created_at_range_is_frozen() -> None:
    r = CreatedAtRange()
    with pytest.raises(Exception):
        r.created_at_from = datetime(2026, 1, 1)  # type: ignore[misc]


def test_created_at_range_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        CreatedAtRange(unknown="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ProjectionRunQuery
# ---------------------------------------------------------------------------


def test_projection_run_query_defaults() -> None:
    q = ProjectionRunQuery()
    assert q.projection_id is None
    assert q.created_at_from is None
    assert q.created_at_to is None
    assert q.limit == 100
    assert q.offset == 0


def test_projection_run_query_limit_ge_1() -> None:
    with pytest.raises(ValidationError):
        ProjectionRunQuery(limit=0)


def test_projection_run_query_limit_le_1000() -> None:
    with pytest.raises(ValidationError):
        ProjectionRunQuery(limit=1001)


def test_projection_run_query_limit_1000_is_valid() -> None:
    q = ProjectionRunQuery(limit=1000)
    assert q.limit == 1000


def test_projection_run_query_offset_ge_0() -> None:
    with pytest.raises(ValidationError):
        ProjectionRunQuery(offset=-1)


def test_projection_run_query_all_fields() -> None:
    lo = datetime(2026, 1, 1)
    hi = datetime(2026, 6, 1)
    q = ProjectionRunQuery(
        projection_id="proj-x",
        created_at_from=lo,
        created_at_to=hi,
        limit=50,
        offset=10,
    )
    assert q.projection_id == "proj-x"
    assert q.created_at_from == lo
    assert q.created_at_to == hi
    assert q.limit == 50
    assert q.offset == 10


def test_projection_run_query_is_frozen() -> None:
    q = ProjectionRunQuery()
    with pytest.raises(Exception):
        q.limit = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# StateRunQuery
# ---------------------------------------------------------------------------


def test_state_run_query_defaults() -> None:
    q = StateRunQuery()
    assert q.snapshot_id is None
    assert q.omega_id is None
    assert q.projection_id is None
    assert q.dominant_state is None
    assert q.created_at_from is None
    assert q.created_at_to is None
    assert q.limit == 100
    assert q.offset == 0


def test_state_run_query_limit_le_1000() -> None:
    with pytest.raises(ValidationError):
        StateRunQuery(limit=1001)


def test_state_run_query_offset_ge_0() -> None:
    with pytest.raises(ValidationError):
        StateRunQuery(offset=-1)


def test_state_run_query_all_fields() -> None:
    lo = datetime(2026, 1, 1)
    q = StateRunQuery(
        snapshot_id="snap-1",
        omega_id="omega-1",
        projection_id="proj-1",
        dominant_state="fire",
        created_at_from=lo,
        created_at_to=lo,
        limit=25,
        offset=5,
    )
    assert q.dominant_state == "fire"
    assert q.limit == 25
    assert q.offset == 5


def test_state_run_query_is_frozen() -> None:
    q = StateRunQuery()
    with pytest.raises(Exception):
        q.limit = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ProjectionRunSummary
# ---------------------------------------------------------------------------


def test_projection_run_summary_is_frozen() -> None:
    s = ProjectionRunSummary(
        run_id="r1",
        created_at=datetime(2026, 1, 1),
        projection_id="p1",
        point_estimate=0.7,
        confidence=0.8,
    )
    with pytest.raises(Exception):
        s.run_id = "r2"  # type: ignore[misc]


def test_projection_run_summary_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        ProjectionRunSummary(
            run_id="r1",
            created_at=datetime(2026, 1, 1),
            projection_id="p1",
            point_estimate=0.7,
            confidence=0.8,
            extra="nope",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# StateRunSummary
# ---------------------------------------------------------------------------


def test_state_run_summary_nullable_projection_id() -> None:
    s = StateRunSummary(
        run_id="r1",
        created_at=datetime(2026, 1, 1),
        snapshot_id="snap-1",
        omega_id="omega-1",
        projection_id=None,
        dominant_state="dormant",
        transition_confidence=0.5,
    )
    assert s.projection_id is None


def test_state_run_summary_is_frozen() -> None:
    s = StateRunSummary(
        run_id="r1",
        created_at=datetime(2026, 1, 1),
        snapshot_id="snap-1",
        omega_id="omega-1",
        projection_id="p1",
        dominant_state="dormant",
        transition_confidence=0.5,
    )
    with pytest.raises(Exception):
        s.run_id = "r2"  # type: ignore[misc]
