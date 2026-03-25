"""Tests for review audit read-only query reader functions."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


# ---------------------------------------------------------------------------
# Helpers (imports deferred so module loads without SQLAlchemy)
# ---------------------------------------------------------------------------


def _make_db_session():
    """Return a fresh in-memory SQLite session with all tables created."""
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine()
    create_all_tables(engine)
    return create_session_factory(engine)()


def _make_review_audit_inputs(
    pr_number: int = 42,
    reviewer_login: str | None = "alice",
    with_action: bool = True,
):
    """Return (review_context, observation, result) for seeding a run."""
    from ugh_quantamental.engine.review_audit import run_review_audit_engine
    from ugh_quantamental.engine.review_audit_models import (
        FixActionFeatures,
        ReviewAuditConfig,
        ReviewIntentFeatures,
        ReviewObservation,
    )
    from ugh_quantamental.engine.review_audit_models import ReviewContext, ReviewKind

    ctx = ReviewContext(
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
    obs = ReviewObservation(
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
    intent = ReviewIntentFeatures(
        intent_clarity=0.8,
        locality_strength=0.9,
        mechanicalness=0.7,
        scope_boundness=0.8,
        semantic_change_risk=0.2,
        validation_intensity=0.3,
    )
    action = None
    if with_action:
        action = FixActionFeatures(
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
    config = ReviewAuditConfig()
    result = run_review_audit_engine(
        audit_id=f"audit-pr{pr_number}",
        intent=intent,
        action=action,
        config=config,
    )
    return ctx, obs, result


def _seed_review_audit_run(
    session,
    run_id: str,
    pr_number: int = 42,
    reviewer_login: str | None = "alice",
    with_action: bool = True,
    created_at: datetime | None = None,
):
    """Seed one ReviewAuditRunRecord via the repository."""
    from ugh_quantamental.persistence.repositories import ReviewAuditRunRepository

    ctx, obs, result = _make_review_audit_inputs(
        pr_number=pr_number,
        reviewer_login=reviewer_login,
        with_action=with_action,
    )
    ReviewAuditRunRepository.save_run(
        session,
        run_id=run_id,
        review_context=ctx,
        observation=obs,
        result=result,
        created_at=created_at,
    )
    session.flush()
    return run_id


# ---------------------------------------------------------------------------
# list_review_audit_run_summaries
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_returns_all_by_default() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    _seed_review_audit_run(session, "r1", pr_number=1)
    _seed_review_audit_run(session, "r2", pr_number=2)

    summaries = list_review_audit_run_summaries(session, ReviewAuditRunQuery())
    assert len(summaries) == 2
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_ordered_newest_first() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    _seed_review_audit_run(session, "r-old", created_at=base)
    _seed_review_audit_run(session, "r-new", created_at=base + timedelta(hours=1))

    summaries = list_review_audit_run_summaries(session, ReviewAuditRunQuery())
    assert summaries[0].run_id == "r-new"
    assert summaries[1].run_id == "r-old"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_filter_by_audit_id() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    _seed_review_audit_run(session, "r1", pr_number=1)
    _seed_review_audit_run(session, "r2", pr_number=2)

    summaries = list_review_audit_run_summaries(
        session, ReviewAuditRunQuery(audit_id="audit-pr1")
    )
    assert len(summaries) == 1
    assert summaries[0].run_id == "r1"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_filter_by_pr_number() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    _seed_review_audit_run(session, "r1", pr_number=10)
    _seed_review_audit_run(session, "r2", pr_number=20)
    _seed_review_audit_run(session, "r3", pr_number=10)

    summaries = list_review_audit_run_summaries(
        session, ReviewAuditRunQuery(pr_number=10)
    )
    assert len(summaries) == 2
    assert all(s.pr_number == 10 for s in summaries)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_filter_by_reviewer_login() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    _seed_review_audit_run(session, "r1", reviewer_login="alice")
    _seed_review_audit_run(session, "r2", reviewer_login="bob")
    _seed_review_audit_run(session, "r3", reviewer_login="alice")

    summaries = list_review_audit_run_summaries(
        session, ReviewAuditRunQuery(reviewer_login="alice")
    )
    assert len(summaries) == 2
    assert all(s.reviewer_login == "alice" for s in summaries)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_filter_by_verdict() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    # with_action=True yields non-"insufficient_data" verdicts
    _seed_review_audit_run(session, "r-with-action", with_action=True)
    # with_action=False always yields "insufficient_data"
    _seed_review_audit_run(session, "r-no-action", pr_number=99, with_action=False)

    summaries = list_review_audit_run_summaries(
        session, ReviewAuditRunQuery(verdict="insufficient_data")
    )
    assert all(s.verdict == "insufficient_data" for s in summaries)
    assert any(s.run_id == "r-no-action" for s in summaries)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_created_at_range() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    _seed_review_audit_run(session, "r-before", pr_number=1, created_at=datetime(2026, 1, 1))
    _seed_review_audit_run(session, "r-inside", pr_number=2, created_at=datetime(2026, 1, 10))
    _seed_review_audit_run(session, "r-after", pr_number=3, created_at=datetime(2026, 1, 20))

    summaries = list_review_audit_run_summaries(
        session,
        ReviewAuditRunQuery(
            created_at_from=datetime(2026, 1, 5),
            created_at_to=datetime(2026, 1, 15),
        ),
    )
    assert len(summaries) == 1
    assert summaries[0].run_id == "r-inside"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_limit() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    for i in range(5):
        _seed_review_audit_run(
            session, f"r{i}", pr_number=i + 1, created_at=base + timedelta(hours=i)
        )

    summaries = list_review_audit_run_summaries(session, ReviewAuditRunQuery(limit=3))
    assert len(summaries) == 3
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_offset() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    for i in range(4):
        _seed_review_audit_run(
            session, f"r{i}", pr_number=i + 1, created_at=base + timedelta(hours=i)
        )

    all_summaries = list_review_audit_run_summaries(session, ReviewAuditRunQuery())
    offset_summaries = list_review_audit_run_summaries(session, ReviewAuditRunQuery(offset=2))
    assert len(offset_summaries) == 2
    assert offset_summaries[0].run_id == all_summaries[2].run_id
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_review_audit_run_summaries_exposes_por_delta_e_mismatch_score() -> None:
    from ugh_quantamental.query.models import ReviewAuditRunQuery
    from ugh_quantamental.query.readers import list_review_audit_run_summaries

    session = _make_db_session()
    _seed_review_audit_run(session, "r-with-action", with_action=True)
    _seed_review_audit_run(session, "r-no-action", pr_number=99, with_action=False)

    summaries = list_review_audit_run_summaries(session, ReviewAuditRunQuery())
    by_id = {s.run_id: s for s in summaries}

    s_action = by_id["r-with-action"]
    assert isinstance(s_action.por, float)
    assert isinstance(s_action.delta_e, float)
    assert isinstance(s_action.mismatch_score, float)

    s_no_action = by_id["r-no-action"]
    assert isinstance(s_no_action.por, float)
    assert s_no_action.delta_e is None
    assert s_no_action.mismatch_score is None
    session.close()


# ---------------------------------------------------------------------------
# get_review_audit_run_bundle
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_review_audit_run_bundle_returns_fully_typed_bundle() -> None:
    from ugh_quantamental.engine.review_audit_models import ReviewAuditEngineResult
    from ugh_quantamental.query.models import ReviewAuditRunBundle
    from ugh_quantamental.query.readers import get_review_audit_run_bundle
    from ugh_quantamental.engine.review_audit_models import ReviewContext

    session = _make_db_session()
    _seed_review_audit_run(session, "r-bundle", pr_number=55, reviewer_login="carol")

    bundle = get_review_audit_run_bundle(session, "r-bundle")
    assert bundle is not None
    assert isinstance(bundle, ReviewAuditRunBundle)
    assert bundle.run_id == "r-bundle"
    assert bundle.pr_number == 55
    assert bundle.reviewer_login == "carol"
    assert bundle.audit_id == "audit-pr55"
    assert isinstance(bundle.review_context, ReviewContext)
    assert isinstance(bundle.result, ReviewAuditEngineResult)
    assert bundle.result.action_features is not None
    assert bundle.extractor_version == "v1"
    assert bundle.feature_spec_version == "v1"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_review_audit_run_bundle_missing_returns_none() -> None:
    from ugh_quantamental.query.readers import get_review_audit_run_bundle

    session = _make_db_session()
    bundle = get_review_audit_run_bundle(session, "does-not-exist")
    assert bundle is None
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_review_audit_run_bundle_without_action() -> None:
    from ugh_quantamental.query.readers import get_review_audit_run_bundle

    session = _make_db_session()
    _seed_review_audit_run(session, "r-no-action", pr_number=77, with_action=False)

    bundle = get_review_audit_run_bundle(session, "r-no-action")
    assert bundle is not None
    assert bundle.action_features is None
    assert bundle.result.action_features is None
    assert bundle.result.audit_snapshot.verdict == "insufficient_data"
    session.close()
