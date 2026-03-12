"""Tests for batch replay request model validation."""

from __future__ import annotations

import pytest

from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
from ugh_quantamental.replay.batch_models import (
    BatchReplayStatus,
    ProjectionBatchReplayRequest,
    StateBatchReplayRequest,
)


# ---------------------------------------------------------------------------
# BatchReplayStatus enum
# ---------------------------------------------------------------------------


def test_batch_replay_status_values() -> None:
    assert BatchReplayStatus.ok == "ok"
    assert BatchReplayStatus.missing == "missing"
    assert BatchReplayStatus.error == "error"


# ---------------------------------------------------------------------------
# ProjectionBatchReplayRequest — exactly one source required
# ---------------------------------------------------------------------------


def test_projection_batch_request_run_ids_accepted() -> None:
    req = ProjectionBatchReplayRequest(run_ids=("run-a", "run-b"))
    assert req.run_ids == ("run-a", "run-b")
    assert req.query is None
    assert req.deduplicate_run_ids is True


def test_projection_batch_request_query_accepted() -> None:
    q = ProjectionRunQuery(projection_id="proj-1")
    req = ProjectionBatchReplayRequest(query=q)
    assert req.query == q
    assert req.run_ids is None


def test_projection_batch_request_rejects_both_missing() -> None:
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        ProjectionBatchReplayRequest()


def test_projection_batch_request_rejects_both_present() -> None:
    q = ProjectionRunQuery(projection_id="proj-1")
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        ProjectionBatchReplayRequest(run_ids=("run-a",), query=q)


def test_projection_batch_request_deduplicate_flag_override() -> None:
    req = ProjectionBatchReplayRequest(run_ids=("run-a",), deduplicate_run_ids=False)
    assert req.deduplicate_run_ids is False


def test_projection_batch_request_extra_fields_forbidden() -> None:
    with pytest.raises(Exception):
        ProjectionBatchReplayRequest(run_ids=("run-a",), unknown_field=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# StateBatchReplayRequest — exactly one source required
# ---------------------------------------------------------------------------


def test_state_batch_request_run_ids_accepted() -> None:
    req = StateBatchReplayRequest(run_ids=("state-a",))
    assert req.run_ids == ("state-a",)
    assert req.query is None


def test_state_batch_request_query_accepted() -> None:
    q = StateRunQuery(snapshot_id="snap-1")
    req = StateBatchReplayRequest(query=q)
    assert req.query == q
    assert req.run_ids is None


def test_state_batch_request_rejects_both_missing() -> None:
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        StateBatchReplayRequest()


def test_state_batch_request_rejects_both_present() -> None:
    q = StateRunQuery(snapshot_id="snap-1")
    with pytest.raises(ValueError, match="exactly one of run_ids or query"):
        StateBatchReplayRequest(run_ids=("state-a",), query=q)


def test_state_batch_request_deduplicate_flag_override() -> None:
    req = StateBatchReplayRequest(run_ids=("state-a",), deduplicate_run_ids=False)
    assert req.deduplicate_run_ids is False


def test_state_batch_request_extra_fields_forbidden() -> None:
    with pytest.raises(Exception):
        StateBatchReplayRequest(run_ids=("state-a",), unknown_field=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_projection_batch_request_is_frozen() -> None:
    req = ProjectionBatchReplayRequest(run_ids=("run-a",))
    with pytest.raises(Exception):
        req.run_ids = ("run-b",)  # type: ignore[misc]


def test_state_batch_request_is_frozen() -> None:
    req = StateBatchReplayRequest(run_ids=("state-a",))
    with pytest.raises(Exception):
        req.run_ids = ("state-b",)  # type: ignore[misc]
