"""Tests for read-only query reader functions."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


# ---------------------------------------------------------------------------
# Shared helpers (imports deferred so module loads without SQLAlchemy)
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


def _make_projection_inputs():
    """Return minimal valid projection engine inputs."""
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )

    question = QuestionFeatures(
        question_direction=QuestionDirectionSign.positive,
        q_strength=0.7,
        s_q=0.6,
        temporal_score=0.5,
    )
    signal = SignalFeatures(
        fundamental_score=0.3,
        technical_score=0.2,
        price_implied_score=0.1,
        context_score=1.0,
        grv_lock=0.6,
        regime_fit=0.5,
        narrative_dispersion=0.2,
        evidence_confidence=0.7,
        fire_probability=0.4,
    )
    alignment = AlignmentInputs(
        d_qf=0.1, d_qt=0.2, d_qp=0.3,
        d_ft=0.1, d_fp=0.2, d_tp=0.2,
    )
    config = ProjectionConfig()
    return question, signal, alignment, config


def _make_projection_result(projection_id: str = "proj-q1", horizon_days: int = 30):
    from ugh_quantamental.engine.projection import run_projection_engine

    q, sig, align, cfg = _make_projection_inputs()
    return run_projection_engine(projection_id, horizon_days, q, sig, align, cfg), q, sig, align, cfg


def _make_snapshot_and_omega(snapshot_id: str = "snap-q1", omega_id: str = "omega-q1"):
    from ugh_quantamental.schemas.enums import (
        LifecycleState,
        MacroCycleRegime,
        MarketRegime,
        QuestionDirection,
    )
    from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
    from ugh_quantamental.schemas.omega import BlockObservability, EvidenceLineageRecord, Omega
    from ugh_quantamental.schemas.ssv import (
        FBlock,
        PBlock,
        QBlock,
        QuestionLedger,
        QuestionRecord,
        RBlock,
        SSVSnapshot,
        TBlock,
        XBlock,
    )

    probs = StateProbabilities(
        dormant=0.30, setup=0.20, fire=0.20,
        expansion=0.15, exhaustion=0.10, failure=0.05,
    )
    phi = Phi(dominant_state=LifecycleState.dormant, probabilities=probs)
    ledger = QuestionLedger(
        as_of="2026-01-01",
        coverage_ratio=1.0,
        questions=[
            QuestionRecord(
                question_id="q-qr-1",
                direction=QuestionDirection.positive,
                score=0.4,
                weight=1.0,
            )
        ],
    )
    snapshot = SSVSnapshot(
        snapshot_id=snapshot_id,
        q=QBlock(ledger=ledger),
        f=FBlock(factor_count=3, aggregate_signal=0.2),
        t=TBlock(timestamp="2026-01-01T00:00:00Z", lookback_days=30),
        p=PBlock(implied_move_30d=0.03, implied_volatility=0.22, skew_25d=0.01),
        phi=phi,
        r=RBlock(
            market_regime=MarketRegime.neutral,
            macro_cycle_regime=MacroCycleRegime.expansion,
            conviction=0.5,
        ),
        x=XBlock(tags=["query-test"]),
    )
    obs = BlockObservability(q=0.9, f=0.8, t=0.9, p=0.8, r=0.8, x=0.7)
    omega = Omega(
        omega_id=omega_id,
        market_svp=MarketSVP(
            as_of="2026-01-01T00:00:00Z",
            regime=MarketRegime.neutral,
            phi=phi,
            confidence=0.7,
        ),
        question_ledger=ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="src-qr-1",
                observed_at="2026-01-01T00:00:00Z",
                source_type="internal",
            ),
        ),
        block_confidence=obs,
        block_observability=obs,
        confidence=0.8,
    )
    return snapshot, omega


def _seed_projection_run(
    session,
    run_id: str,
    projection_id: str = "proj-q1",
    created_at: datetime | None = None,
) -> None:
    from ugh_quantamental.persistence.repositories import ProjectionRunRepository

    result, q, sig, align, cfg = _make_projection_result(projection_id)
    ProjectionRunRepository.save_run(
        session,
        run_id=run_id,
        projection_id=projection_id,
        question_features=q,
        signal_features=sig,
        alignment_inputs=align,
        config=cfg,
        result=result,
        created_at=created_at,
    )
    session.flush()


def _seed_state_run(
    session,
    run_id: str,
    snapshot_id: str = "snap-q1",
    omega_id: str = "omega-q1",
    projection_id: str = "proj-q1",
    created_at: datetime | None = None,
) -> None:
    from ugh_quantamental.engine.state import run_state_engine
    from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
    from ugh_quantamental.persistence.repositories import StateRunRepository

    proj_result, _, _, _, _ = _make_projection_result(projection_id)
    snapshot, omega = _make_snapshot_and_omega(snapshot_id, omega_id)
    events = StateEventFeatures(
        catalyst_strength=0.6,
        follow_through=0.5,
        pricing_saturation=0.3,
        disconfirmation_strength=0.2,
        regime_shock=0.1,
        observation_freshness=0.9,
    )
    config = StateConfig()
    state_result = run_state_engine(snapshot, omega, proj_result, events, config)

    StateRunRepository.save_run(
        session,
        run_id=run_id,
        snapshot_id=snapshot_id,
        omega_id=omega_id,
        projection_id=projection_id,
        dominant_state=state_result.dominant_state.value,
        transition_confidence=state_result.transition_confidence,
        snapshot=snapshot,
        omega=omega,
        projection_result=proj_result,
        event_features=events,
        config=config,
        result=state_result,
        created_at=created_at,
    )
    session.flush()


# ---------------------------------------------------------------------------
# Projection summary listing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_returns_all_by_default() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    session = _make_db_session()
    _seed_projection_run(session, "r1", "proj-a")
    _seed_projection_run(session, "r2", "proj-b")

    summaries = list_projection_run_summaries(session, ProjectionRunQuery())
    assert len(summaries) == 2
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_ordered_newest_first() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    _seed_projection_run(session, "r-old", created_at=base)
    _seed_projection_run(session, "r-new", created_at=base + timedelta(hours=1))

    summaries = list_projection_run_summaries(session, ProjectionRunQuery())
    assert summaries[0].run_id == "r-new"
    assert summaries[1].run_id == "r-old"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_filter_by_projection_id() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    session = _make_db_session()
    _seed_projection_run(session, "r1", "proj-alpha")
    _seed_projection_run(session, "r2", "proj-beta")
    _seed_projection_run(session, "r3", "proj-alpha")

    summaries = list_projection_run_summaries(
        session, ProjectionRunQuery(projection_id="proj-alpha")
    )
    assert len(summaries) == 2
    assert all(s.projection_id == "proj-alpha" for s in summaries)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_created_at_range() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    base = datetime(2026, 1, 10)
    session = _make_db_session()
    _seed_projection_run(session, "r-before", created_at=datetime(2026, 1, 1))
    _seed_projection_run(session, "r-inside", created_at=base)
    _seed_projection_run(session, "r-after", created_at=datetime(2026, 1, 20))

    summaries = list_projection_run_summaries(
        session,
        ProjectionRunQuery(
            created_at_from=datetime(2026, 1, 5),
            created_at_to=datetime(2026, 1, 15),
        ),
    )
    assert len(summaries) == 1
    assert summaries[0].run_id == "r-inside"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_limit() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    for i in range(5):
        _seed_projection_run(session, f"r{i}", created_at=base + timedelta(hours=i))

    summaries = list_projection_run_summaries(session, ProjectionRunQuery(limit=3))
    assert len(summaries) == 3
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_offset() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    for i in range(4):
        _seed_projection_run(session, f"r{i}", created_at=base + timedelta(hours=i))

    all_summaries = list_projection_run_summaries(session, ProjectionRunQuery())
    page2 = list_projection_run_summaries(session, ProjectionRunQuery(offset=2))
    assert len(page2) == 2
    assert page2[0].run_id == all_summaries[2].run_id
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_has_point_estimate_and_confidence() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    session = _make_db_session()
    _seed_projection_run(session, "r1")

    summaries = list_projection_run_summaries(session, ProjectionRunQuery())
    assert len(summaries) == 1
    s = summaries[0]
    assert isinstance(s.point_estimate, float)
    assert isinstance(s.confidence, float)
    assert 0.0 <= s.confidence <= 1.0
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_projection_run_summaries_empty_result() -> None:
    from ugh_quantamental.query.models import ProjectionRunQuery
    from ugh_quantamental.query.readers import list_projection_run_summaries

    session = _make_db_session()
    summaries = list_projection_run_summaries(
        session, ProjectionRunQuery(projection_id="nonexistent")
    )
    assert summaries == []
    session.close()


# ---------------------------------------------------------------------------
# State summary listing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_returns_all_by_default() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    session = _make_db_session()
    _seed_state_run(session, "s1", snapshot_id="snap-a", omega_id="omega-a")
    _seed_state_run(session, "s2", snapshot_id="snap-b", omega_id="omega-b")

    summaries = list_state_run_summaries(session, StateRunQuery())
    assert len(summaries) == 2
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_ordered_newest_first() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    _seed_state_run(session, "s-old", snapshot_id="snap-old", omega_id="omega-old", created_at=base)
    _seed_state_run(
        session, "s-new", snapshot_id="snap-new", omega_id="omega-new",
        created_at=base + timedelta(hours=1),
    )

    summaries = list_state_run_summaries(session, StateRunQuery())
    assert summaries[0].run_id == "s-new"
    assert summaries[1].run_id == "s-old"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_filter_by_snapshot_id() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    session = _make_db_session()
    _seed_state_run(session, "s1", snapshot_id="snap-x", omega_id="omega-1")
    _seed_state_run(session, "s2", snapshot_id="snap-y", omega_id="omega-2")
    _seed_state_run(session, "s3", snapshot_id="snap-x", omega_id="omega-3")

    summaries = list_state_run_summaries(session, StateRunQuery(snapshot_id="snap-x"))
    assert len(summaries) == 2
    assert all(s.snapshot_id == "snap-x" for s in summaries)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_filter_by_omega_id() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    session = _make_db_session()
    _seed_state_run(session, "s1", snapshot_id="snap-1", omega_id="omega-target")
    _seed_state_run(session, "s2", snapshot_id="snap-2", omega_id="omega-other")

    summaries = list_state_run_summaries(session, StateRunQuery(omega_id="omega-target"))
    assert len(summaries) == 1
    assert summaries[0].omega_id == "omega-target"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_filter_by_projection_id() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    session = _make_db_session()
    _seed_state_run(session, "s1", snapshot_id="snap-1", omega_id="omega-1", projection_id="proj-aa")
    _seed_state_run(session, "s2", snapshot_id="snap-2", omega_id="omega-2", projection_id="proj-bb")

    summaries = list_state_run_summaries(session, StateRunQuery(projection_id="proj-aa"))
    assert len(summaries) == 1
    assert summaries[0].projection_id == "proj-aa"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_filter_by_dominant_state() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    session = _make_db_session()
    # Seed two runs — dominant_state is determined by the engine, so we just
    # confirm filtering works by checking all results match the requested value.
    _seed_state_run(session, "s1", snapshot_id="snap-1", omega_id="omega-1")
    _seed_state_run(session, "s2", snapshot_id="snap-2", omega_id="omega-2")

    all_summaries = list_state_run_summaries(session, StateRunQuery())
    assert len(all_summaries) >= 1

    # Pick the dominant_state of the first result and filter by it.
    target_state = all_summaries[0].dominant_state
    filtered = list_state_run_summaries(session, StateRunQuery(dominant_state=target_state))
    assert all(s.dominant_state == target_state for s in filtered)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_created_at_range() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    base = datetime(2026, 1, 10)
    session = _make_db_session()
    _seed_state_run(session, "s-before", snapshot_id="snap-1", omega_id="omega-1",
                    created_at=datetime(2026, 1, 1))
    _seed_state_run(session, "s-inside", snapshot_id="snap-2", omega_id="omega-2",
                    created_at=base)
    _seed_state_run(session, "s-after", snapshot_id="snap-3", omega_id="omega-3",
                    created_at=datetime(2026, 1, 20))

    summaries = list_state_run_summaries(
        session,
        StateRunQuery(
            created_at_from=datetime(2026, 1, 5),
            created_at_to=datetime(2026, 1, 15),
        ),
    )
    assert len(summaries) == 1
    assert summaries[0].run_id == "s-inside"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_list_state_run_summaries_limit_and_offset() -> None:
    from ugh_quantamental.query.models import StateRunQuery
    from ugh_quantamental.query.readers import list_state_run_summaries

    base = datetime(2026, 1, 1)
    session = _make_db_session()
    for i in range(5):
        _seed_state_run(
            session, f"s{i}",
            snapshot_id=f"snap-{i}", omega_id=f"omega-{i}",
            created_at=base + timedelta(hours=i),
        )

    page1 = list_state_run_summaries(session, StateRunQuery(limit=2))
    page2 = list_state_run_summaries(session, StateRunQuery(limit=2, offset=2))
    assert len(page1) == 2
    assert len(page2) == 2
    assert {s.run_id for s in page1}.isdisjoint({s.run_id for s in page2})
    session.close()


# ---------------------------------------------------------------------------
# Bundle reconstruction — projection
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_projection_run_bundle_returns_none_for_missing() -> None:
    from ugh_quantamental.query.readers import get_projection_run_bundle

    session = _make_db_session()
    result = get_projection_run_bundle(session, "no-such-run")
    assert result is None
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_projection_run_bundle_returns_typed_models() -> None:
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        ProjectionEngineResult,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.query.models import ProjectionRunBundle
    from ugh_quantamental.query.readers import get_projection_run_bundle

    session = _make_db_session()
    _seed_projection_run(session, "bundle-proj-1", "proj-bundle")

    bundle = get_projection_run_bundle(session, "bundle-proj-1")
    assert bundle is not None
    assert isinstance(bundle, ProjectionRunBundle)
    assert bundle.run_id == "bundle-proj-1"
    assert bundle.projection_id == "proj-bundle"
    assert isinstance(bundle.question_features, QuestionFeatures)
    assert isinstance(bundle.signal_features, SignalFeatures)
    assert isinstance(bundle.alignment_inputs, AlignmentInputs)
    assert isinstance(bundle.config, ProjectionConfig)
    assert isinstance(bundle.result, ProjectionEngineResult)
    assert bundle.result.projection_snapshot.projection_id == "proj-bundle"
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_projection_run_bundle_roundtrip_fidelity() -> None:
    """Bundle result matches what run_projection_engine would produce."""
    from ugh_quantamental.engine.projection import run_projection_engine

    from ugh_quantamental.query.readers import get_projection_run_bundle

    session = _make_db_session()
    q, sig, align, cfg = _make_projection_inputs()
    expected = run_projection_engine("proj-rt", 30, q, sig, align, cfg)

    from ugh_quantamental.persistence.repositories import ProjectionRunRepository

    ProjectionRunRepository.save_run(
        session,
        run_id="bundle-rt",
        projection_id="proj-rt",
        question_features=q,
        signal_features=sig,
        alignment_inputs=align,
        config=cfg,
        result=expected,
    )
    session.flush()

    bundle = get_projection_run_bundle(session, "bundle-rt")
    assert bundle is not None
    assert bundle.result == expected
    assert bundle.question_features == q
    assert bundle.signal_features == sig
    assert bundle.alignment_inputs == align
    assert bundle.config == cfg
    session.close()


# ---------------------------------------------------------------------------
# Bundle reconstruction — state
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_state_run_bundle_returns_none_for_missing() -> None:
    from ugh_quantamental.query.readers import get_state_run_bundle

    session = _make_db_session()
    result = get_state_run_bundle(session, "no-such-run")
    assert result is None
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_state_run_bundle_returns_typed_models() -> None:
    from ugh_quantamental.engine.projection_models import ProjectionEngineResult
    from ugh_quantamental.engine.state_models import StateConfig, StateEngineResult, StateEventFeatures
    from ugh_quantamental.query.models import StateRunBundle
    from ugh_quantamental.query.readers import get_state_run_bundle
    from ugh_quantamental.schemas.omega import Omega
    from ugh_quantamental.schemas.ssv import SSVSnapshot

    session = _make_db_session()
    _seed_state_run(session, "bundle-state-1", snapshot_id="snap-b1", omega_id="omega-b1")

    bundle = get_state_run_bundle(session, "bundle-state-1")
    assert bundle is not None
    assert isinstance(bundle, StateRunBundle)
    assert bundle.run_id == "bundle-state-1"
    assert bundle.snapshot_id == "snap-b1"
    assert bundle.omega_id == "omega-b1"
    assert isinstance(bundle.snapshot, SSVSnapshot)
    assert isinstance(bundle.omega, Omega)
    assert isinstance(bundle.projection_result, ProjectionEngineResult)
    assert isinstance(bundle.event_features, StateEventFeatures)
    assert isinstance(bundle.config, StateConfig)
    assert isinstance(bundle.result, StateEngineResult)
    session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_state_run_bundle_roundtrip_fidelity() -> None:
    """Bundle result matches what run_state_engine would produce."""
    from ugh_quantamental.engine.state import run_state_engine
    from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
    from ugh_quantamental.persistence.repositories import StateRunRepository
    from ugh_quantamental.query.readers import get_state_run_bundle

    proj_result, _, _, _, _ = _make_projection_result("proj-state-rt")
    snapshot, omega = _make_snapshot_and_omega("snap-rt", "omega-rt")
    events = StateEventFeatures(
        catalyst_strength=0.6,
        follow_through=0.5,
        pricing_saturation=0.3,
        disconfirmation_strength=0.2,
        regime_shock=0.1,
        observation_freshness=0.9,
    )
    config = StateConfig()
    expected = run_state_engine(snapshot, omega, proj_result, events, config)

    session = _make_db_session()
    StateRunRepository.save_run(
        session,
        run_id="bundle-state-rt",
        snapshot_id=snapshot.snapshot_id,
        omega_id=omega.omega_id,
        projection_id="proj-state-rt",
        dominant_state=expected.dominant_state.value,
        transition_confidence=expected.transition_confidence,
        snapshot=snapshot,
        omega=omega,
        projection_result=proj_result,
        event_features=events,
        config=config,
        result=expected,
    )
    session.flush()

    bundle = get_state_run_bundle(session, "bundle-state-rt")
    assert bundle is not None
    assert bundle.result == expected
    assert bundle.snapshot == snapshot
    assert bundle.omega == omega
    assert bundle.event_features == events
    assert bundle.config == config
    session.close()


# ---------------------------------------------------------------------------
# Read-only behaviour
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_readers_do_not_add_records() -> None:
    """Running readers on a seeded session must not change the record count."""
    from sqlalchemy import func, select

    from ugh_quantamental.persistence.models import ProjectionRunRecord, StateRunRecord
    from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
    from ugh_quantamental.query.readers import (
        get_projection_run_bundle,
        get_state_run_bundle,
        list_projection_run_summaries,
        list_state_run_summaries,
    )

    session = _make_db_session()
    _seed_projection_run(session, "ro-proj")
    _seed_state_run(session, "ro-state", snapshot_id="snap-ro", omega_id="omega-ro")

    proj_count_before = session.scalar(select(func.count()).select_from(ProjectionRunRecord))
    state_count_before = session.scalar(select(func.count()).select_from(StateRunRecord))

    list_projection_run_summaries(session, ProjectionRunQuery())
    list_state_run_summaries(session, StateRunQuery())
    get_projection_run_bundle(session, "ro-proj")
    get_state_run_bundle(session, "ro-state")

    proj_count_after = session.scalar(select(func.count()).select_from(ProjectionRunRecord))
    state_count_after = session.scalar(select(func.count()).select_from(StateRunRecord))

    assert proj_count_after == proj_count_before
    assert state_count_after == state_count_before
    session.close()
