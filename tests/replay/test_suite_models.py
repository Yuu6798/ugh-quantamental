"""Tests for regression suite model validation (Milestone 11)."""

from __future__ import annotations

import pytest

from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
from ugh_quantamental.replay.suite_models import (
    ProjectionSuiteCase,
    RegressionSuiteRequest,
    StateSuiteCase,
)


# ---------------------------------------------------------------------------
# ProjectionSuiteCase
# ---------------------------------------------------------------------------


def test_projection_suite_case_run_ids() -> None:
    c = ProjectionSuiteCase(name="smoke", run_ids=("run-a",))
    assert c.name == "smoke"
    assert c.run_ids == ("run-a",)
    assert c.query is None
    assert c.deduplicate_run_ids is True


def test_projection_suite_case_query() -> None:
    q = ProjectionRunQuery(projection_id="proj-1")
    c = ProjectionSuiteCase(name="q-driven", query=q)
    assert c.query == q
    assert c.run_ids is None


def test_projection_suite_case_rejects_both_missing() -> None:
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        ProjectionSuiteCase(name="bad")


def test_projection_suite_case_rejects_both_present() -> None:
    q = ProjectionRunQuery()
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        ProjectionSuiteCase(name="bad", run_ids=("run-a",), query=q)


def test_projection_suite_case_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        ProjectionSuiteCase(name="", run_ids=("run-a",))


def test_projection_suite_case_rejects_whitespace_name() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        ProjectionSuiteCase(name="   ", run_ids=("run-a",))


def test_projection_suite_case_is_frozen() -> None:
    c = ProjectionSuiteCase(name="smoke", run_ids=("run-a",))
    with pytest.raises(Exception):
        c.name = "other"  # type: ignore[misc]


def test_projection_suite_case_extra_forbidden() -> None:
    with pytest.raises(Exception):
        ProjectionSuiteCase(name="smoke", run_ids=("run-a",), unknown=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# StateSuiteCase
# ---------------------------------------------------------------------------


def test_state_suite_case_run_ids() -> None:
    c = StateSuiteCase(name="state-smoke", run_ids=("state-a",))
    assert c.name == "state-smoke"
    assert c.run_ids == ("state-a",)


def test_state_suite_case_query() -> None:
    q = StateRunQuery(snapshot_id="snap-1")
    c = StateSuiteCase(name="q-driven", query=q)
    assert c.query == q


def test_state_suite_case_rejects_both_missing() -> None:
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        StateSuiteCase(name="bad")


def test_state_suite_case_rejects_both_present() -> None:
    q = StateRunQuery()
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        StateSuiteCase(name="bad", run_ids=("state-a",), query=q)


def test_state_suite_case_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        StateSuiteCase(name="", run_ids=("state-a",))


# ---------------------------------------------------------------------------
# RegressionSuiteRequest
# ---------------------------------------------------------------------------


def test_suite_request_projection_only() -> None:
    req = RegressionSuiteRequest(
        projection_cases=(ProjectionSuiteCase(name="smoke", run_ids=("run-a",)),)
    )
    assert len(req.projection_cases) == 1
    assert len(req.state_cases) == 0


def test_suite_request_state_only() -> None:
    req = RegressionSuiteRequest(
        state_cases=(StateSuiteCase(name="smoke", run_ids=("state-a",)),)
    )
    assert len(req.state_cases) == 1


def test_suite_request_mixed() -> None:
    req = RegressionSuiteRequest(
        projection_cases=(ProjectionSuiteCase(name="p", run_ids=("run-a",)),),
        state_cases=(StateSuiteCase(name="s", run_ids=("state-a",)),),
    )
    assert len(req.projection_cases) == 1
    assert len(req.state_cases) == 1


def test_suite_request_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one"):
        RegressionSuiteRequest()


def test_suite_request_rejects_duplicate_projection_names() -> None:
    with pytest.raises(ValueError, match="unique"):
        RegressionSuiteRequest(
            projection_cases=(
                ProjectionSuiteCase(name="dup", run_ids=("run-a",)),
                ProjectionSuiteCase(name="dup", run_ids=("run-b",)),
            )
        )


def test_suite_request_rejects_duplicate_state_names() -> None:
    with pytest.raises(ValueError, match="unique"):
        RegressionSuiteRequest(
            state_cases=(
                StateSuiteCase(name="dup", run_ids=("state-a",)),
                StateSuiteCase(name="dup", run_ids=("state-b",)),
            )
        )


def test_suite_request_allows_same_name_across_groups() -> None:
    # Cross-group name collision is explicitly allowed
    req = RegressionSuiteRequest(
        projection_cases=(ProjectionSuiteCase(name="smoke", run_ids=("run-a",)),),
        state_cases=(StateSuiteCase(name="smoke", run_ids=("state-a",)),),
    )
    assert req.projection_cases[0].name == "smoke"
    assert req.state_cases[0].name == "smoke"


def test_suite_request_is_frozen() -> None:
    req = RegressionSuiteRequest(
        projection_cases=(ProjectionSuiteCase(name="smoke", run_ids=("run-a",)),)
    )
    with pytest.raises(Exception):
        req.projection_cases = ()  # type: ignore[misc]
