"""Round-trip tests for minimal projection/state repositories."""

import importlib.util
from datetime import datetime, timedelta, timezone

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

if HAS_SQLALCHEMY:
    from sqlalchemy.orm import Session


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_run_round_trip() -> None:
    from sqlalchemy.orm import Session

    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )
    from ugh_quantamental.persistence.repositories import ProjectionRunRepository

    def _session() -> Session:
        engine = create_db_engine()
        create_all_tables(engine)
        return create_session_factory(engine)()

    with _session() as session:
        question = QuestionFeatures(
            question_direction=QuestionDirectionSign.positive,
            q_strength=0.8,
            s_q=0.7,
            temporal_score=0.6,
        )
        signal = SignalFeatures(
            fundamental_score=0.4,
            technical_score=0.2,
            price_implied_score=0.1,
            context_score=1.0,
            grv_lock=0.7,
            regime_fit=0.6,
            narrative_dispersion=0.2,
            evidence_confidence=0.8,
            fire_probability=0.6,
        )
        alignment = AlignmentInputs(
            d_qf=0.2,
            d_qt=0.3,
            d_qp=0.4,
            d_ft=0.2,
            d_fp=0.2,
            d_tp=0.3,
        )
        config = ProjectionConfig()
        result = run_projection_engine("proj-1", 30, question, signal, alignment, config)

        ProjectionRunRepository.save_run(
            session,
            run_id="proj-run-1",
            projection_id="proj-1",
            question_features=question,
            signal_features=signal,
            alignment_inputs=alignment,
            config=config,
            result=result,
        )
        session.commit()

        loaded = ProjectionRunRepository.load_run(session, "proj-run-1")
        assert loaded is not None
        assert loaded.projection_id == "proj-1"
        assert loaded.result.projection_snapshot.projection_id == "proj-1"
        assert loaded.question_features == question
        assert loaded.created_at.tzinfo is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_run_round_trip() -> None:
    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.engine.state import run_state_engine
    from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )
    from ugh_quantamental.persistence.repositories import StateRunRepository
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

    def _session() -> Session:
        engine = create_db_engine()
        create_all_tables(engine)
        return create_session_factory(engine)()

    def _snapshot() -> SSVSnapshot:
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
                    question_id="q-1",
                    direction=QuestionDirection.positive,
                    score=0.4,
                    weight=1.0,
                )
            ],
        )
        return SSVSnapshot(
            snapshot_id="snap-1",
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
            x=XBlock(tags=["test"]),
        )

    def _omega(snapshot: SSVSnapshot) -> Omega:
        obs = BlockObservability(q=0.9, f=0.8, t=0.9, p=0.8, r=0.8, x=0.7)
        return Omega(
            omega_id="omega-1",
            market_svp=MarketSVP(
                as_of="2026-01-01T00:00:00Z",
                regime=MarketRegime.neutral,
                phi=snapshot.phi,
                confidence=0.7,
            ),
            question_ledger=snapshot.q.ledger,
            evidence_lineage=(
                EvidenceLineageRecord(
                    source_id="src-1",
                    observed_at="2026-01-01T00:00:00Z",
                    source_type="internal",
                ),
            ),
            block_confidence=obs,
            block_observability=obs,
            confidence=0.8,
        )

    with _session() as session:
        question = QuestionFeatures(
            question_direction=QuestionDirectionSign.positive,
            q_strength=0.7,
            s_q=0.7,
            temporal_score=0.5,
        )
        signal = SignalFeatures(
            fundamental_score=0.3,
            technical_score=0.2,
            price_implied_score=0.0,
            context_score=1.1,
            grv_lock=0.8,
            regime_fit=0.7,
            narrative_dispersion=0.2,
            evidence_confidence=0.75,
            fire_probability=0.5,
        )
        alignment = AlignmentInputs(d_qf=0.2, d_qt=0.2, d_qp=0.2, d_ft=0.2, d_fp=0.2, d_tp=0.2)
        projection = run_projection_engine("proj-2", 20, question, signal, alignment, ProjectionConfig())

        snapshot = _snapshot()
        omega = _omega(snapshot)
        events = StateEventFeatures(
            catalyst_strength=0.6,
            follow_through=0.5,
            pricing_saturation=0.3,
            disconfirmation_strength=0.2,
            regime_shock=0.1,
            observation_freshness=0.9,
        )
        config = StateConfig()
        state_result = run_state_engine(snapshot, omega, projection, events, config)

        StateRunRepository.save_run(
            session,
            run_id="state-run-1",
            snapshot_id=snapshot.snapshot_id,
            omega_id=omega.omega_id,
            projection_id=projection.projection_snapshot.projection_id,
            dominant_state=state_result.dominant_state.value,
            transition_confidence=state_result.transition_confidence,
            snapshot=snapshot,
            omega=omega,
            projection_result=projection,
            event_features=events,
            config=config,
            result=state_result,
        )
        session.commit()

        loaded = StateRunRepository.load_run(session, "state-run-1")
        assert loaded is not None
        assert loaded.snapshot_id == snapshot.snapshot_id
        assert loaded.omega_id == omega.omega_id
        assert loaded.projection_id == "proj-2"
        assert loaded.dominant_state == state_result.dominant_state.value
        assert loaded.result.dominant_state == state_result.dominant_state
        assert loaded.created_at.tzinfo is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_run_created_at_normalizes_aware_timezone_to_naive_utc() -> None:
    from sqlalchemy.orm import Session

    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine, create_session_factory
    from ugh_quantamental.persistence.repositories import ProjectionRunRepository

    def _session() -> Session:
        engine = create_db_engine()
        create_all_tables(engine)
        return create_session_factory(engine)()

    question = QuestionFeatures(
        question_direction=QuestionDirectionSign.positive,
        q_strength=0.8,
        s_q=0.7,
        temporal_score=0.6,
    )
    signal = SignalFeatures(
        fundamental_score=0.4,
        technical_score=0.2,
        price_implied_score=0.1,
        context_score=1.0,
        grv_lock=0.7,
        regime_fit=0.6,
        narrative_dispersion=0.2,
        evidence_confidence=0.8,
        fire_probability=0.6,
    )
    alignment = AlignmentInputs(d_qf=0.2, d_qt=0.3, d_qp=0.4, d_ft=0.2, d_fp=0.2, d_tp=0.3)
    config = ProjectionConfig()
    result = run_projection_engine("proj-3", 30, question, signal, alignment, config)

    ist = timezone(timedelta(hours=5, minutes=30))
    created_at = datetime(2026, 3, 11, 12, 0, 0, tzinfo=ist)

    with _session() as session:
        ProjectionRunRepository.save_run(
            session,
            run_id="proj-run-tz",
            projection_id="proj-3",
            question_features=question,
            signal_features=signal,
            alignment_inputs=alignment,
            config=config,
            result=result,
            created_at=created_at,
        )
        session.commit()

        loaded = ProjectionRunRepository.load_run(session, "proj-run-tz")

    assert loaded is not None
    assert loaded.created_at == datetime(2026, 3, 11, 6, 30, 0)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_state_run_created_at_normalizes_aware_timezone_to_naive_utc() -> None:
    from sqlalchemy.orm import Session

    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.engine.state import run_state_engine
    from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine, create_session_factory
    from ugh_quantamental.persistence.repositories import StateRunRepository
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

    def _session() -> Session:
        engine = create_db_engine()
        create_all_tables(engine)
        return create_session_factory(engine)()

    probabilities = StateProbabilities(dormant=0.30, setup=0.20, fire=0.20, expansion=0.15, exhaustion=0.10, failure=0.05)
    phi = Phi(dominant_state=LifecycleState.dormant, probabilities=probabilities)
    snapshot = SSVSnapshot(
        snapshot_id="snap-2",
        q=QBlock(ledger=QuestionLedger(as_of="2026-01-01", coverage_ratio=1.0, questions=[QuestionRecord(question_id="q-1", direction=QuestionDirection.positive, score=0.4, weight=1.0)])),
        f=FBlock(factor_count=3, aggregate_signal=0.2),
        t=TBlock(timestamp="2026-01-01T00:00:00Z", lookback_days=30),
        p=PBlock(implied_move_30d=0.03, implied_volatility=0.22, skew_25d=0.01),
        phi=phi,
        r=RBlock(market_regime=MarketRegime.neutral, macro_cycle_regime=MacroCycleRegime.expansion, conviction=0.5),
        x=XBlock(tags=["test"]),
    )
    obs = BlockObservability(q=0.9, f=0.8, t=0.9, p=0.8, r=0.8, x=0.7)
    omega = Omega(
        omega_id="omega-2",
        market_svp=MarketSVP(as_of="2026-01-01T00:00:00Z", regime=MarketRegime.neutral, phi=phi, confidence=0.7),
        question_ledger=snapshot.q.ledger,
        evidence_lineage=(EvidenceLineageRecord(source_id="src-1", observed_at="2026-01-01T00:00:00Z", source_type="internal"),),
        block_confidence=obs,
        block_observability=obs,
        confidence=0.8,
    )

    question = QuestionFeatures(question_direction=QuestionDirectionSign.positive, q_strength=0.7, s_q=0.7, temporal_score=0.5)
    signal = SignalFeatures(fundamental_score=0.3, technical_score=0.2, price_implied_score=0.0, context_score=1.1, grv_lock=0.8, regime_fit=0.7, narrative_dispersion=0.2, evidence_confidence=0.75, fire_probability=0.5)
    alignment = AlignmentInputs(d_qf=0.2, d_qt=0.2, d_qp=0.2, d_ft=0.2, d_fp=0.2, d_tp=0.2)
    projection = run_projection_engine("proj-4", 20, question, signal, alignment, ProjectionConfig())
    events = StateEventFeatures(catalyst_strength=0.6, follow_through=0.5, pricing_saturation=0.3, disconfirmation_strength=0.2, regime_shock=0.1, observation_freshness=0.9)
    config = StateConfig()
    state_result = run_state_engine(snapshot, omega, projection, events, config)

    ist = timezone(timedelta(hours=5, minutes=30))
    created_at = datetime(2026, 3, 11, 12, 0, 0, tzinfo=ist)

    with _session() as session:
        StateRunRepository.save_run(
            session,
            run_id="state-run-tz",
            snapshot_id=snapshot.snapshot_id,
            omega_id=omega.omega_id,
            projection_id=projection.projection_snapshot.projection_id,
            dominant_state=state_result.dominant_state.value,
            transition_confidence=state_result.transition_confidence,
            snapshot=snapshot,
            omega=omega,
            projection_result=projection,
            event_features=events,
            config=config,
            result=state_result,
            created_at=created_at,
        )
        session.commit()

        loaded = StateRunRepository.load_run(session, "state-run-tz")

    assert loaded is not None
    assert loaded.created_at == datetime(2026, 3, 11, 6, 30, 0)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_projection_run_created_at_preserves_naive_datetime_as_utc_policy() -> None:
    from sqlalchemy.orm import Session

    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        ProjectionConfig,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine, create_session_factory
    from ugh_quantamental.persistence.repositories import ProjectionRunRepository

    def _session() -> Session:
        engine = create_db_engine()
        create_all_tables(engine)
        return create_session_factory(engine)()

    question = QuestionFeatures(question_direction=QuestionDirectionSign.positive, q_strength=0.8, s_q=0.7, temporal_score=0.6)
    signal = SignalFeatures(fundamental_score=0.4, technical_score=0.2, price_implied_score=0.1, context_score=1.0, grv_lock=0.7, regime_fit=0.6, narrative_dispersion=0.2, evidence_confidence=0.8, fire_probability=0.6)
    alignment = AlignmentInputs(d_qf=0.2, d_qt=0.3, d_qp=0.4, d_ft=0.2, d_fp=0.2, d_tp=0.3)
    config = ProjectionConfig()
    result = run_projection_engine("proj-5", 30, question, signal, alignment, config)

    naive_created_at = datetime(2026, 3, 11, 12, 0, 0)

    with _session() as session:
        ProjectionRunRepository.save_run(
            session,
            run_id="proj-run-naive",
            projection_id="proj-5",
            question_features=question,
            signal_features=signal,
            alignment_inputs=alignment,
            config=config,
            result=result,
            created_at=naive_created_at,
        )
        session.commit()

        loaded = ProjectionRunRepository.load_run(session, "proj-run-naive")

    assert loaded is not None
    assert loaded.created_at == naive_created_at
