"""Tests for review audit replay runners: engine replay and extractor replay."""

from __future__ import annotations

import importlib.util

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

pytestmark = pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db_session():
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine()
    create_all_tables(engine)
    return create_session_factory(engine)()


def _make_review_context(pr_number: int = 42, reviewer_login: str | None = "alice"):
    from ugh_quantamental.engine.review_audit_models import ReviewContext, ReviewKind

    return ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="Yuu6798/ugh-quantamental",
        pr_number=pr_number,
        review_id=1001,
        review_comment_id=2001,
        head_sha="abc123def456",
        base_ref="main",
        head_ref="feature/foo",
        same_repo=True,
        reviewer_login=reviewer_login,
        body="Please fix this import. minimal change only.",
        path="src/foo.py",
        diff_hunk="@@ -1,3 +1,4 @@",
        line=10,
        start_line=None,
        version_discriminator="v1",
    )


def _make_fix_action():
    from ugh_quantamental.engine.review_audit_models import FixActionFeatures

    return FixActionFeatures(
        changed=True,
        validation_ok=True,
        lines_changed=5,
        files_changed=1,
        target_file_match=0.9,
        line_anchor_touched=0.8,
        diff_hunk_overlap=0.7,
        scope_ratio=0.3,
        validation_scope_executed=0.5,
        behavior_preservation_proxy=0.8,
        execution_status="succeeded",
    )


def _seed_review_audit_run(
    session,
    run_id: str,
    with_action: bool = True,
    pr_number: int = 42,
) -> str:
    """Seed a review audit run using extractor-produced features + engine."""
    from ugh_quantamental.engine.review_audit import run_review_audit_engine
    from ugh_quantamental.engine.review_audit_models import ReviewAuditConfig
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository
    from ugh_quantamental.engine.review_audit_extractor import (
        extract_review_intent_features,
        extract_review_observation,
    )

    ctx = _make_review_context(pr_number=pr_number)
    obs = extract_review_observation(ctx)
    intent = extract_review_intent_features(obs)
    action = _make_fix_action() if with_action else None
    config = ReviewAuditConfig()
    result = run_review_audit_engine(
        audit_id=f"audit-{run_id}",
        intent=intent,
        action=action,
        config=config,
    )
    ReviewAuditRunRepository.save_run(
        session,
        run_id=run_id,
        review_context=ctx,
        observation=obs,
        result=result,
    )
    session.flush()
    return run_id


# ---------------------------------------------------------------------------
# Engine replay — missing run
# ---------------------------------------------------------------------------


def test_replay_review_audit_run_missing_returns_none() -> None:
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    result = replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="no-such-run"))
    assert result is None
    session.close()


# ---------------------------------------------------------------------------
# Engine replay — exact-match cases
# ---------------------------------------------------------------------------


def test_replay_review_audit_run_exact_match_with_action() -> None:
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-with-action", with_action=True)

    result = replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="r-with-action"))
    assert result is not None
    cmp = result.comparison
    assert cmp.exact_match is True
    assert cmp.snapshot_match is True
    assert cmp.por_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.verdict_match is True
    session.close()


def test_replay_review_audit_run_exact_match_without_action() -> None:
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-no-action", with_action=False)

    result = replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="r-no-action"))
    assert result is not None
    cmp = result.comparison
    assert cmp.exact_match is True
    assert cmp.snapshot_match is True
    assert cmp.verdict_match is True
    session.close()


def test_replay_review_audit_run_delta_e_diff_none_when_both_none() -> None:
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-no-action-2", with_action=False)

    result = replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="r-no-action-2"))
    assert result is not None
    assert result.comparison.delta_e_diff is None
    session.close()


def test_replay_review_audit_run_mismatch_score_diff_none_when_both_none() -> None:
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-no-action-3", with_action=False)

    result = replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="r-no-action-3"))
    assert result is not None
    assert result.comparison.mismatch_score_diff is None
    session.close()


def test_replay_review_audit_run_verdict_matches_on_exact_replay() -> None:
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-verdict", with_action=True)

    result = replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="r-verdict"))
    assert result is not None
    assert result.comparison.verdict_match is True
    stored_verdict = result.bundle.result.audit_snapshot.verdict
    recomputed_verdict = result.recomputed_result.audit_snapshot.verdict
    assert stored_verdict == recomputed_verdict
    session.close()


def test_replay_review_audit_run_is_read_only() -> None:
    """Replaying does not persist additional records."""
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries
    from ugh_quantamental.replay.models import ReviewAuditReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-ro")

    before = list_review_audit_run_summaries(session, ReviewAuditRunQuery())
    replay_review_audit_run(session, ReviewAuditReplayRequest(run_id="r-ro"))
    after = list_review_audit_run_summaries(session, ReviewAuditRunQuery())

    assert len(before) == len(after)
    session.close()


# ---------------------------------------------------------------------------
# Extractor replay — missing run
# ---------------------------------------------------------------------------


def test_replay_review_audit_extractor_run_missing_returns_none() -> None:
    from ugh_quantamental.replay.models import ReviewAuditExtractorReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_extractor_run

    session = _make_db_session()
    result = replay_review_audit_extractor_run(
        session, ReviewAuditExtractorReplayRequest(run_id="no-such-run")
    )
    assert result is None
    session.close()


# ---------------------------------------------------------------------------
# Extractor replay — exact-match cases
# ---------------------------------------------------------------------------


def test_replay_review_audit_extractor_run_exact_match() -> None:
    from ugh_quantamental.replay.models import ReviewAuditExtractorReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_extractor_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-extractor")

    result = replay_review_audit_extractor_run(
        session, ReviewAuditExtractorReplayRequest(run_id="r-extractor")
    )
    assert result is not None
    cmp = result.comparison
    assert cmp.exact_match is True
    assert cmp.observation_match is True
    assert cmp.intent_features_match is True
    session.close()


def test_replay_review_audit_extractor_run_numeric_diffs_zero_on_exact_match() -> None:
    from ugh_quantamental.replay.models import ReviewAuditExtractorReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_extractor_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-ext-nums")

    result = replay_review_audit_extractor_run(
        session, ReviewAuditExtractorReplayRequest(run_id="r-ext-nums")
    )
    assert result is not None
    cmp = result.comparison
    assert cmp.intent_clarity_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.locality_strength_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.mechanicalness_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.scope_boundness_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.semantic_change_risk_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.validation_intensity_diff == pytest.approx(0.0, abs=1e-9)
    assert cmp.mechanical_keyword_hits_diff == 0
    assert cmp.skip_keyword_hits_diff == 0
    assert cmp.ambiguity_signal_count_diff == 0
    session.close()


def test_replay_review_audit_extractor_run_symbolic_fields_match() -> None:
    from ugh_quantamental.replay.models import ReviewAuditExtractorReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_extractor_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-ext-sym")

    result = replay_review_audit_extractor_run(
        session, ReviewAuditExtractorReplayRequest(run_id="r-ext-sym")
    )
    assert result is not None
    cmp = result.comparison
    assert cmp.has_path_hint_match is True
    assert cmp.has_line_anchor_match is True
    assert cmp.has_diff_hunk_match is True
    assert cmp.priority_match is True
    assert cmp.behavior_preservation_signal_match is True
    assert cmp.scope_limit_signal_match is True
    assert cmp.target_file_present_match is True
    assert cmp.review_kind_match is True
    session.close()


def test_replay_review_audit_extractor_run_recomputed_fields_accessible() -> None:
    from ugh_quantamental.engine.review_audit_models import ReviewIntentFeatures, ReviewObservation
    from ugh_quantamental.replay.models import ReviewAuditExtractorReplayRequest
    from ugh_quantamental.replay.runners import replay_review_audit_extractor_run

    session = _make_db_session()
    _seed_review_audit_run(session, "r-ext-fields")

    result = replay_review_audit_extractor_run(
        session, ReviewAuditExtractorReplayRequest(run_id="r-ext-fields")
    )
    assert result is not None
    assert isinstance(result.recomputed_observation, ReviewObservation)
    assert isinstance(result.recomputed_intent_features, ReviewIntentFeatures)
    session.close()
