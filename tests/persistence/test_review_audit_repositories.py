"""Round-trip tests for ReviewAuditRunRepository and review audit serializers."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


# ---------------------------------------------------------------------------
# Shared fixtures (pure Python — no SQLAlchemy)
# ---------------------------------------------------------------------------


def _make_review_context():
    from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind

    return ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="Yuu6798/ugh-quantamental",
        pr_number=42,
        review_id=None,
        review_comment_id=101,
        head_sha="abc123def456",
        base_ref="main",
        head_ref="feature/foo",
        same_repo=True,
        reviewer_login="alice",
        body="Use snake_case here.",
        path="src/foo.py",
        diff_hunk="@@ -1,3 +1,3 @@\n-foo = 1\n+bar = 1",
        line=5,
        start_line=None,
        version_discriminator="v1",
        review_comment_node_id="PRR_abc",
        review_body_path_hint_present=False,
    )


def _make_observation():
    from ugh_quantamental.engine.review_audit_models import ReviewObservation

    return ReviewObservation(
        has_path_hint=True,
        has_line_anchor=True,
        has_diff_hunk=True,
        priority="P1",
        mechanical_keyword_hits=2,
        skip_keyword_hits=0,
        behavior_preservation_signal=False,
        scope_limit_signal=True,
        ambiguity_signal_count=0,
        target_file_present=True,
        review_kind="diff_comment",
    )


def _make_intent_features():
    from ugh_quantamental.engine.review_audit_models import ReviewIntentFeatures

    return ReviewIntentFeatures(
        intent_clarity=0.8,
        locality_strength=0.9,
        mechanicalness=0.7,
        scope_boundness=0.85,
        semantic_change_risk=0.1,
        validation_intensity=0.3,
    )


def _make_action_features():
    from ugh_quantamental.engine.review_audit_models import FixActionFeatures

    return FixActionFeatures(
        changed=True,
        validation_ok=True,
        lines_changed=3,
        files_changed=1,
        target_file_match=1.0,
        line_anchor_touched=1.0,
        diff_hunk_overlap=0.9,
        scope_ratio=0.2,
        validation_scope_executed=0.5,
        behavior_preservation_proxy=0.95,
        execution_status="succeeded",
    )


def _make_engine_result(with_action: bool = True):
    from ugh_quantamental.engine.review_audit_models import (
        ReviewAuditConfig,
        ReviewAuditEngineResult,
        ReviewAuditSnapshot,
    )

    action = _make_action_features() if with_action else None
    snapshot = ReviewAuditSnapshot(
        audit_id="audit-test-001",
        por=0.83,
        delta_e=0.12 if with_action else None,
        mismatch_score=0.05 if with_action else None,
        verdict="aligned" if with_action else "insufficient_data",
    )
    return ReviewAuditEngineResult(
        audit_snapshot=snapshot,
        intent_features=_make_intent_features(),
        action_features=action,
        config=ReviewAuditConfig(),
    )


def _session():
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine()
    create_all_tables(engine)
    return create_session_factory(engine)()


# ---------------------------------------------------------------------------
# Repository round-trip tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_save_load_round_trip_with_action_features() -> None:
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository

    context = _make_review_context()
    observation = _make_observation()
    intent = _make_intent_features()
    action = _make_action_features()
    result = _make_engine_result(with_action=True)

    with _session() as session:
        ReviewAuditRunRepository.save_run(
            session,
            run_id="audit-run-001",
            audit_id="audit-test-001",
            pr_number=42,
            reviewer_login="alice",
            review_context=context,
            observation=observation,
            intent_features=intent,
            action_features=action,
            result=result,
        )
        session.commit()

        loaded = ReviewAuditRunRepository.load_run(session, "audit-run-001")

    assert loaded is not None
    assert loaded.run_id == "audit-run-001"
    assert loaded.audit_id == "audit-test-001"
    assert loaded.pr_number == 42
    assert loaded.reviewer_login == "alice"
    assert loaded.verdict == "aligned"
    assert loaded.extractor_version == "v1"
    assert loaded.feature_spec_version == "v1"
    # ReviewContext round-trip
    assert loaded.review_context == context
    assert loaded.review_context.kind.value == "diff_comment"
    # Pydantic model round-trips
    assert loaded.observation == observation
    assert loaded.intent_features == intent
    assert loaded.action_features == action
    assert loaded.result == result
    # naive UTC timestamp
    assert loaded.created_at.tzinfo is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_save_load_round_trip_without_action_features() -> None:
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository

    context = _make_review_context()
    observation = _make_observation()
    intent = _make_intent_features()
    result = _make_engine_result(with_action=False)

    with _session() as session:
        ReviewAuditRunRepository.save_run(
            session,
            run_id="audit-run-002",
            audit_id="audit-test-001",
            pr_number=42,
            reviewer_login=None,
            review_context=context,
            observation=observation,
            intent_features=intent,
            action_features=None,
            result=result,
        )
        session.commit()

        loaded = ReviewAuditRunRepository.load_run(session, "audit-run-002")

    assert loaded is not None
    assert loaded.action_features is None
    assert loaded.reviewer_login is None
    assert loaded.verdict == "insufficient_data"
    assert loaded.review_context == context


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_load_missing_run_returns_none() -> None:
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository

    with _session() as session:
        loaded = ReviewAuditRunRepository.load_run(session, "does-not-exist")

    assert loaded is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_timezone_aware_created_at_normalized_to_naive_utc() -> None:
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository

    aware_dt = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    context = _make_review_context()
    result = _make_engine_result(with_action=True)

    with _session() as session:
        ReviewAuditRunRepository.save_run(
            session,
            run_id="audit-run-003",
            audit_id="audit-test-tz",
            pr_number=7,
            reviewer_login=None,
            review_context=context,
            observation=_make_observation(),
            intent_features=_make_intent_features(),
            action_features=_make_action_features(),
            result=result,
            created_at=aware_dt,
        )
        session.commit()

        loaded = ReviewAuditRunRepository.load_run(session, "audit-run-003")

    assert loaded is not None
    assert loaded.created_at.tzinfo is None
    assert loaded.created_at == datetime(2026, 3, 15, 12, 0, 0)


# ---------------------------------------------------------------------------
# Serializer unit tests (no SQLAlchemy required)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_dump_load_review_context_roundtrip() -> None:
    from ugh_quantamental.persistence.serializers import (
        dump_review_context_json,
        load_review_context_json,
    )
    from ugh_quantamental.review_autofix.models import ReviewKind

    context = _make_review_context()
    payload = dump_review_context_json(context)

    assert isinstance(payload, dict)
    assert payload["kind"] == "diff_comment"
    assert payload["pr_number"] == 42

    reloaded = load_review_context_json(payload)
    assert reloaded == context
    assert reloaded.kind is ReviewKind.diff_comment


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_dump_load_review_context_review_body_kind() -> None:
    """review_body kind also round-trips correctly."""
    from ugh_quantamental.persistence.serializers import (
        dump_review_context_json,
        load_review_context_json,
    )
    from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind

    context = ReviewContext(
        kind=ReviewKind.review_body,
        repository="Yuu6798/ugh-quantamental",
        pr_number=99,
        review_id=55,
        review_comment_id=None,
        head_sha="deadbeef1234",
        base_ref="main",
        head_ref="fix/bar",
        same_repo=False,
        reviewer_login=None,
        body="LGTM overall.",
        path=None,
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v1",
    )
    payload = dump_review_context_json(context)
    reloaded = load_review_context_json(payload)
    assert reloaded == context
    assert reloaded.kind is ReviewKind.review_body


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_review_audit_payload_to_models_with_action() -> None:
    from ugh_quantamental.persistence.serializers import (
        dump_model_json,
        dump_review_context_json,
        review_audit_payload_to_models,
    )

    context = _make_review_context()
    observation = _make_observation()
    intent = _make_intent_features()
    action = _make_action_features()
    result = _make_engine_result(with_action=True)

    payload = {
        "review_context_json": dump_review_context_json(context),
        "observation_json": dump_model_json(observation),
        "intent_features_json": dump_model_json(intent),
        "action_features_json": dump_model_json(action),
        "engine_result_json": dump_model_json(result),
    }

    ctx, obs, intf, actf, res = review_audit_payload_to_models(payload)

    assert ctx == context
    assert obs == observation
    assert intf == intent
    assert actf == action
    assert res == result


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_review_audit_payload_to_models_null_action() -> None:
    from ugh_quantamental.persistence.serializers import (
        dump_model_json,
        dump_review_context_json,
        review_audit_payload_to_models,
    )

    context = _make_review_context()
    result = _make_engine_result(with_action=False)

    payload = {
        "review_context_json": dump_review_context_json(context),
        "observation_json": dump_model_json(_make_observation()),
        "intent_features_json": dump_model_json(_make_intent_features()),
        "action_features_json": None,
        "engine_result_json": dump_model_json(result),
    }

    ctx, obs, intf, actf, res = review_audit_payload_to_models(payload)

    assert actf is None
    assert ctx == context
    assert res == result
