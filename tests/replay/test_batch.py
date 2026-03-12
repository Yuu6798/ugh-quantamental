"""Tests for batch replay runners: explicit run_ids, query-driven, error isolation, aggregates."""

from __future__ import annotations

import importlib.util

import pytest

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
from ugh_quantamental.replay.batch_models import (
    BatchReplayStatus,
    ProjectionBatchReplayRequest,
    StateBatchReplayRequest,
)

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

pytestmark = pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")


# ---------------------------------------------------------------------------
# Seeding helpers (reuse pattern from test_runners.py)
# ---------------------------------------------------------------------------


def _seed_projection_run(
    session,
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
    alignment_inputs: AlignmentInputs,
    projection_config: ProjectionConfig,
    run_id: str,
    projection_id: str = "proj-batch-1",
) -> str:
    from ugh_quantamental.workflows.models import ProjectionWorkflowRequest
    from ugh_quantamental.workflows.runners import run_projection_workflow

    req = ProjectionWorkflowRequest(
        projection_id=projection_id,
        horizon_days=30,
        question_features=question_features,
        signal_features=signal_features,
        alignment_inputs=alignment_inputs,
        config=projection_config,
        run_id=run_id,
    )
    run_projection_workflow(session, req)
    session.flush()
    return run_id


def _seed_state_run(
    session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features: StateEventFeatures,
    state_config: StateConfig,
    run_id: str,
) -> str:
    from ugh_quantamental.workflows.models import StateWorkflowRequest
    from ugh_quantamental.workflows.runners import run_state_workflow

    req = StateWorkflowRequest(
        snapshot=ssv_snapshot,
        omega=omega,
        projection_result=projection_engine_result,
        event_features=event_features,
        config=state_config,
        run_id=run_id,
    )
    run_state_workflow(session, req)
    session.flush()
    return run_id


# ---------------------------------------------------------------------------
# Projection batch — explicit run_ids
# ---------------------------------------------------------------------------


def test_projection_batch_explicit_run_ids(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_id_a = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-proj-a",
    )
    run_id_b = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-proj-b",
    )

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(run_ids=(run_id_a, run_id_b)),
    )

    assert result.aggregate.requested_count == 2
    assert result.aggregate.processed_count == 2
    assert result.aggregate.exact_match_count == 2
    assert result.aggregate.mismatch_count == 0
    assert result.aggregate.missing_count == 0
    assert result.aggregate.error_count == 0
    assert len(result.items) == 2
    assert all(item.status == BatchReplayStatus.ok for item in result.items)


# ---------------------------------------------------------------------------
# State batch — explicit run_ids
# ---------------------------------------------------------------------------


def test_state_batch_explicit_run_ids(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_state_batch

    run_id_a = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "pb-state-a",
    )
    run_id_b = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "pb-state-b",
    )

    result = replay_state_batch(
        db_session,
        StateBatchReplayRequest(run_ids=(run_id_a, run_id_b)),
    )

    assert result.aggregate.requested_count == 2
    assert result.aggregate.processed_count == 2
    assert result.aggregate.exact_match_count == 2
    assert result.aggregate.mismatch_count == 0
    assert result.aggregate.missing_count == 0
    assert result.aggregate.error_count == 0
    assert all(item.status == BatchReplayStatus.ok for item in result.items)


# ---------------------------------------------------------------------------
# Projection batch — query-driven selection
# ---------------------------------------------------------------------------


def test_projection_batch_query_driven(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    pid = "proj-query-driven-batch"
    _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-qd-1", projection_id=pid,
    )
    _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-qd-2", projection_id=pid,
    )

    q = ProjectionRunQuery(projection_id=pid, limit=10)
    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(query=q),
    )

    assert result.aggregate.requested_count == 2
    assert result.aggregate.exact_match_count == 2
    assert result.aggregate.missing_count == 0


# ---------------------------------------------------------------------------
# State batch — query-driven selection
# ---------------------------------------------------------------------------


def test_state_batch_query_driven(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_state_batch

    _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "pb-sqd-1",
    )
    _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "pb-sqd-2",
    )

    # Filter by the snapshot_id used in the fixture
    q = StateRunQuery(snapshot_id=ssv_snapshot.snapshot_id, limit=10)
    result = replay_state_batch(
        db_session,
        StateBatchReplayRequest(query=q),
    )

    # At least 2 seeded runs match; more may exist from other tests using same snapshot_id
    assert result.aggregate.requested_count >= 2
    assert result.aggregate.exact_match_count >= 2


# ---------------------------------------------------------------------------
# Duplicate run-id deduplication (first-seen order preserved)
# ---------------------------------------------------------------------------


def test_projection_batch_deduplicates_run_ids(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-dedup-1",
    )

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(
            run_ids=(run_id, run_id, run_id),
            deduplicate_run_ids=True,
        ),
    )

    # Only one unique run_id after deduplication
    assert result.aggregate.requested_count == 1
    assert len(result.items) == 1
    assert result.items[0].run_id == run_id


def test_projection_batch_no_dedup_when_disabled(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-nodedup-1",
    )

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(
            run_ids=(run_id, run_id),
            deduplicate_run_ids=False,
        ),
    )

    assert result.aggregate.requested_count == 2
    assert len(result.items) == 2


def test_projection_batch_dedup_preserves_order(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_a = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-order-a",
    )
    run_b = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-order-b",
    )

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(
            run_ids=(run_a, run_b, run_a),  # run_a duplicated at end
            deduplicate_run_ids=True,
        ),
    )

    assert result.aggregate.requested_count == 2
    assert result.items[0].run_id == run_a
    assert result.items[1].run_id == run_b


# ---------------------------------------------------------------------------
# Missing run handling
# ---------------------------------------------------------------------------


def test_projection_batch_missing_run(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-mixed-ok",
    )

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(run_ids=(run_id, "definitely-does-not-exist")),
    )

    statuses = {item.run_id: item.status for item in result.items}
    assert statuses[run_id] == BatchReplayStatus.ok
    assert statuses["definitely-does-not-exist"] == BatchReplayStatus.missing
    assert result.aggregate.missing_count == 1
    assert result.aggregate.processed_count == 1  # ok only (error=0)


def test_state_batch_missing_run(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from ugh_quantamental.replay.batch import replay_state_batch

    run_id = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "sb-mixed-ok",
    )

    result = replay_state_batch(
        db_session,
        StateBatchReplayRequest(run_ids=(run_id, "no-such-state-run")),
    )

    statuses = {item.run_id: item.status for item in result.items}
    assert statuses[run_id] == BatchReplayStatus.ok
    assert statuses["no-such-state-run"] == BatchReplayStatus.missing
    assert result.aggregate.missing_count == 1


# ---------------------------------------------------------------------------
# Per-run exception isolation (monkeypatch single-run replay to raise)
# ---------------------------------------------------------------------------


def test_projection_batch_error_isolation(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
    monkeypatch,
) -> None:
    from ugh_quantamental.replay import batch as batch_module

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-error-isolation",
    )

    original_fn = batch_module.replay_projection_run

    call_count = {"n": 0}

    def raise_on_second(session, request):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated engine failure")
        return original_fn(session, request)

    monkeypatch.setattr(batch_module, "replay_projection_run", raise_on_second)

    # Two run IDs: first succeeds, second raises
    result = batch_module.replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(run_ids=(run_id, "error-trigger-id")),
    )

    statuses = {item.run_id: item.status for item in result.items}
    assert statuses[run_id] == BatchReplayStatus.ok
    assert statuses["error-trigger-id"] == BatchReplayStatus.error
    assert result.aggregate.error_count == 1
    assert "simulated engine failure" in result.items[1].error_message


def test_state_batch_error_isolation(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
    monkeypatch,
) -> None:
    from ugh_quantamental.replay import batch as batch_module

    run_id = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "sb-error-isolation",
    )

    original_fn = batch_module.replay_state_run

    call_count = {"n": 0}

    def raise_on_second(session, request):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated state failure")
        return original_fn(session, request)

    monkeypatch.setattr(batch_module, "replay_state_run", raise_on_second)

    result = batch_module.replay_state_batch(
        db_session,
        StateBatchReplayRequest(run_ids=(run_id, "error-state-id")),
    )

    statuses = {item.run_id: item.status for item in result.items}
    assert statuses[run_id] == BatchReplayStatus.ok
    assert statuses["error-state-id"] == BatchReplayStatus.error
    assert result.aggregate.error_count == 1
    assert "simulated state failure" in result.items[1].error_message


# ---------------------------------------------------------------------------
# Aggregate counts in mixed batches
# ---------------------------------------------------------------------------


def test_projection_batch_aggregate_counts_mixed(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
    monkeypatch,
) -> None:
    from ugh_quantamental.replay import batch as batch_module

    run_ok = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-agg-ok",
    )

    original_fn = batch_module.replay_projection_run

    def _error_for_error_id(session, request):
        if request.run_id == "pb-agg-error":
            raise RuntimeError("forced error")
        return original_fn(session, request)

    monkeypatch.setattr(batch_module, "replay_projection_run", _error_for_error_id)

    result = batch_module.replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(
            run_ids=(run_ok, "pb-agg-missing", "pb-agg-error"),
            deduplicate_run_ids=False,
        ),
    )

    agg = result.aggregate
    assert agg.requested_count == 3
    assert agg.exact_match_count == 1
    assert agg.missing_count == 1
    assert agg.error_count == 1
    assert agg.processed_count == 2  # ok + error


# ---------------------------------------------------------------------------
# Aggregate max diff reporting
# ---------------------------------------------------------------------------


def test_projection_batch_max_diff_from_mismatch(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from ugh_quantamental.persistence.models import ProjectionRunRecord
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-maxdiff",
    )

    # Tamper with stored result to introduce a known diff
    record = db_session.get(ProjectionRunRecord, run_id)
    tampered = dict(record.result_json)
    snap = dict(tampered["projection_snapshot"])
    snap["point_estimate"] = snap["point_estimate"] + 0.25
    tampered["projection_snapshot"] = snap
    record.result_json = tampered
    db_session.flush()
    db_session.expire(record)

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(run_ids=(run_id,)),
    )

    assert result.aggregate.mismatch_count == 1
    assert result.aggregate.max_point_estimate_diff == pytest.approx(0.25, abs=1e-9)


def test_state_batch_max_diff_from_mismatch(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from ugh_quantamental.persistence.models import StateRunRecord
    from ugh_quantamental.replay.batch import replay_state_batch

    run_id = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "sb-maxdiff",
    )

    record = db_session.get(StateRunRecord, run_id)
    tampered = dict(record.result_json)
    tampered["transition_confidence"] = max(
        0.0, min(1.0, tampered["transition_confidence"] + 0.07)
    )
    record.result_json = tampered
    db_session.flush()
    db_session.expire(record)

    result = replay_state_batch(
        db_session,
        StateBatchReplayRequest(run_ids=(run_id,)),
    )

    assert result.aggregate.mismatch_count == 1
    assert result.aggregate.max_transition_confidence_diff == pytest.approx(0.07, abs=1e-9)


# ---------------------------------------------------------------------------
# Read-only guarantee: no new records written during batch replay
# ---------------------------------------------------------------------------


def test_projection_batch_performs_no_writes(
    db_session,
    question_features,
    signal_features,
    alignment_inputs,
    projection_config,
) -> None:
    from sqlalchemy import func, select

    from ugh_quantamental.persistence.models import ProjectionRunRecord
    from ugh_quantamental.replay.batch import replay_projection_batch

    run_id = _seed_projection_run(
        db_session, question_features, signal_features, alignment_inputs,
        projection_config, "pb-readonly",
    )
    db_session.flush()

    count_before = db_session.scalar(
        select(func.count()).select_from(ProjectionRunRecord)
    )

    replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(run_ids=(run_id,)),
    )

    count_after = db_session.scalar(
        select(func.count()).select_from(ProjectionRunRecord)
    )

    assert count_after == count_before


def test_state_batch_performs_no_writes(
    db_session,
    ssv_snapshot,
    omega,
    projection_engine_result,
    event_features,
    state_config,
) -> None:
    from sqlalchemy import func, select

    from ugh_quantamental.persistence.models import StateRunRecord
    from ugh_quantamental.replay.batch import replay_state_batch

    run_id = _seed_state_run(
        db_session, ssv_snapshot, omega, projection_engine_result,
        event_features, state_config, "sb-readonly",
    )
    db_session.flush()

    count_before = db_session.scalar(select(func.count()).select_from(StateRunRecord))

    replay_state_batch(
        db_session,
        StateBatchReplayRequest(run_ids=(run_id,)),
    )

    count_after = db_session.scalar(select(func.count()).select_from(StateRunRecord))

    assert count_after == count_before


# ---------------------------------------------------------------------------
# Empty batch
# ---------------------------------------------------------------------------


def test_projection_batch_empty_run_ids(db_session) -> None:
    from ugh_quantamental.replay.batch import replay_projection_batch

    result = replay_projection_batch(
        db_session,
        ProjectionBatchReplayRequest(run_ids=()),
    )

    assert result.aggregate.requested_count == 0
    assert result.aggregate.processed_count == 0
    assert result.aggregate.exact_match_count == 0
    assert result.aggregate.max_point_estimate_diff == 0.0
    assert result.aggregate.max_confidence_diff == 0.0
    assert len(result.items) == 0


def test_state_batch_empty_run_ids(db_session) -> None:
    from ugh_quantamental.replay.batch import replay_state_batch

    result = replay_state_batch(
        db_session,
        StateBatchReplayRequest(run_ids=()),
    )

    assert result.aggregate.requested_count == 0
    assert result.aggregate.max_transition_confidence_diff == 0.0
    assert len(result.items) == 0
