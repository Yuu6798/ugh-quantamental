"""Shared pytest fixtures for workflow tests."""

from __future__ import annotations

import importlib.util

import pytest

from ugh_quantamental.engine.projection import run_projection_engine
from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionDirectionSign,
    QuestionFeatures,
    SignalFeatures,
)
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

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


@pytest.fixture()
def make_ssv_snapshot() -> SSVSnapshot:
    probabilities = StateProbabilities(
        dormant=0.30,
        setup=0.20,
        fire=0.20,
        expansion=0.15,
        exhaustion=0.10,
        failure=0.05,
    )
    phi = Phi(dominant_state=LifecycleState.dormant, probabilities=probabilities)
    ledger = QuestionLedger(
        as_of="2026-01-01",
        coverage_ratio=1.0,
        questions=[
            QuestionRecord(
                question_id="q-wf-1",
                direction=QuestionDirection.positive,
                score=0.4,
                weight=1.0,
            )
        ],
    )
    return SSVSnapshot(
        snapshot_id="snap-wf-1",
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
        x=XBlock(tags=["wf-test"]),
    )


@pytest.fixture()
def make_omega(make_ssv_snapshot: SSVSnapshot) -> Omega:
    obs = BlockObservability(q=0.9, f=0.8, t=0.9, p=0.8, r=0.8, x=0.7)
    return Omega(
        omega_id="omega-wf-1",
        market_svp=MarketSVP(
            as_of="2026-01-01T00:00:00Z",
            regime=MarketRegime.neutral,
            phi=make_ssv_snapshot.phi,
            confidence=0.7,
        ),
        question_ledger=make_ssv_snapshot.q.ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="src-wf-1",
                observed_at="2026-01-01T00:00:00Z",
                source_type="internal",
            ),
        ),
        block_confidence=obs,
        block_observability=obs,
        confidence=0.8,
    )


@pytest.fixture()
def make_projection_engine_result() -> ProjectionEngineResult:
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
    alignment = AlignmentInputs(d_qf=0.1, d_qt=0.2, d_qp=0.3, d_ft=0.1, d_fp=0.2, d_tp=0.2)
    return run_projection_engine("proj-fixture", 30, question, signal, alignment, ProjectionConfig())


@pytest.fixture()
def db_session():
    """In-memory SQLite session for workflow persistence tests."""
    if not HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")
    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine, create_session_factory

    engine = create_db_engine()
    create_all_tables(engine)
    session = create_session_factory(engine)()
    yield session
    session.close()
