"""End-to-end tests for the review audit workflow runner."""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

import pytest

from ugh_quantamental.engine.review_audit_models import (
    FixActionFeatures,
    ReviewIntentFeatures,
    ReviewObservation,
)
from ugh_quantamental.engine.review_audit_models import ReviewContext, ReviewKind
from ugh_quantamental.workflows.models import ReviewAuditWorkflowRequest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


# ---------------------------------------------------------------------------
# Shared input builders
# ---------------------------------------------------------------------------


def _review_context() -> ReviewContext:
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
    )


def _observation() -> ReviewObservation:
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


def _intent_features() -> ReviewIntentFeatures:
    return ReviewIntentFeatures(
        intent_clarity=0.8,
        locality_strength=0.9,
        mechanicalness=0.7,
        scope_boundness=0.85,
        semantic_change_risk=0.1,
        validation_intensity=0.3,
    )


def _action_features() -> FixActionFeatures:
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


# ---------------------------------------------------------------------------
# Workflow roundtrip — with action_features
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_review_audit_workflow_with_action_features(db_session) -> None:
    """Workflow roundtrip with action_features: persisted_run matches engine result."""
    from ugh_quantamental.workflows.runners import run_review_audit_workflow

    req = ReviewAuditWorkflowRequest(
        audit_id="audit-wf-001",
        pr_number=42,
        review_context=_review_context(),
        observation=_observation(),
        intent_features=_intent_features(),
        action_features=_action_features(),
        run_id="raudit-explicit-001",
    )
    result = run_review_audit_workflow(db_session, req)
    db_session.commit()

    # run_id propagated
    assert result.run_id == "raudit-explicit-001"
    assert result.persisted_run.run_id == "raudit-explicit-001"

    # engine result preserved
    assert result.engine_result.audit_snapshot.audit_id == "audit-wf-001"
    assert result.engine_result.audit_snapshot.delta_e is not None
    assert result.engine_result.audit_snapshot.mismatch_score is not None

    # persisted_run matches engine result
    assert result.persisted_run.audit_id == "audit-wf-001"
    assert result.persisted_run.pr_number == 42
    assert result.persisted_run.reviewer_login == "alice"
    assert result.persisted_run.verdict == result.engine_result.audit_snapshot.verdict
    assert result.persisted_run.result == result.engine_result
    assert result.persisted_run.action_features == result.engine_result.action_features
    assert result.persisted_run.intent_features == result.engine_result.intent_features


# ---------------------------------------------------------------------------
# Workflow roundtrip — without action_features
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_review_audit_workflow_without_action_features(db_session) -> None:
    """Workflow roundtrip without action_features: delta_e and mismatch_score are None."""
    from ugh_quantamental.workflows.runners import run_review_audit_workflow

    req = ReviewAuditWorkflowRequest(
        audit_id="audit-wf-002",
        pr_number=42,
        review_context=_review_context(),
        observation=_observation(),
        intent_features=_intent_features(),
        action_features=None,
    )
    result = run_review_audit_workflow(db_session, req)
    db_session.commit()

    # auto-generated run_id uses raudit- prefix
    assert result.run_id.startswith("raudit-")

    # delta_e and mismatch_score absent when no action
    assert result.engine_result.audit_snapshot.delta_e is None
    assert result.engine_result.audit_snapshot.mismatch_score is None
    assert result.engine_result.audit_snapshot.verdict == "insufficient_data"

    # persisted run matches
    assert result.persisted_run.action_features is None
    assert result.persisted_run.verdict == "insufficient_data"
    assert result.persisted_run.result == result.engine_result


# ---------------------------------------------------------------------------
# Workflow does not commit — caller owns transaction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_review_audit_workflow_does_not_commit(db_session) -> None:
    """Saving and reloading work inside the same session without explicit commit."""
    from ugh_quantamental.workflows.runners import run_review_audit_workflow
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository

    req = ReviewAuditWorkflowRequest(
        audit_id="audit-wf-003",
        pr_number=7,
        review_context=_review_context(),
        observation=_observation(),
        intent_features=_intent_features(),
        run_id="raudit-no-commit",
    )
    result = run_review_audit_workflow(db_session, req)
    # deliberately no commit — reload should still work within the same session
    reloaded = ReviewAuditRunRepository.load_run(db_session, "raudit-no-commit")

    assert reloaded is not None
    assert reloaded.run_id == result.run_id
    assert reloaded.audit_id == "audit-wf-003"


# ---------------------------------------------------------------------------
# Reload failure path
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_review_audit_workflow_reload_failure_raises(db_session) -> None:
    """RuntimeError is raised when load_run returns None after save."""
    from ugh_quantamental.workflows.runners import run_review_audit_workflow

    req = ReviewAuditWorkflowRequest(
        audit_id="audit-wf-004",
        pr_number=1,
        review_context=_review_context(),
        observation=_observation(),
        intent_features=_intent_features(),
    )

    target = "ugh_quantamental.workflows.runners.ReviewAuditRunRepository.load_run"
    with patch(target, return_value=None):
        with pytest.raises(RuntimeError, match="Failed to reload review audit run"):
            run_review_audit_workflow(db_session, req)
