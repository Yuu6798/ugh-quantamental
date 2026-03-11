"""Tests for deterministic state engine models."""

import pytest
from pydantic import ValidationError

from ugh_quantamental.engine.state_models import StateConfig, StateEngineResult, StateEventFeatures
from ugh_quantamental.schemas.enums import LifecycleState, MacroCycleRegime, MarketRegime, QuestionDirection
from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
from ugh_quantamental.schemas.omega import BlockObservability, EvidenceLineageRecord, Omega
from ugh_quantamental.schemas.projection import ProjectionSnapshot
from ugh_quantamental.schemas.ssv import FBlock, PBlock, QBlock, QuestionLedger, QuestionRecord, RBlock, SSVSnapshot, TBlock, XBlock


def _state_probabilities() -> StateProbabilities:
    return StateProbabilities(
        dormant=0.30,
        setup=0.20,
        fire=0.20,
        expansion=0.15,
        exhaustion=0.10,
        failure=0.05,
    )


def _phi() -> Phi:
    return Phi(dominant_state=LifecycleState.dormant, probabilities=_state_probabilities())


def _market_svp() -> MarketSVP:
    return MarketSVP(
        as_of="2026-01-01T00:00:00Z",
        regime=MarketRegime.neutral,
        phi=_phi(),
        confidence=0.5,
    )


def _snapshot() -> SSVSnapshot:
    ledger = QuestionLedger(
        as_of="2026-01-01",
        coverage_ratio=1.0,
        questions=[
            QuestionRecord(
                question_id="q1",
                direction=QuestionDirection.positive,
                score=0.3,
                weight=1.0,
            )
        ],
    )
    return SSVSnapshot(
        snapshot_id="s1",
        q=QBlock(ledger=ledger),
        f=FBlock(factor_count=3, aggregate_signal=0.2),
        t=TBlock(timestamp="2026-01-01T00:00:00Z", lookback_days=30),
        p=PBlock(implied_move_30d=0.02, implied_volatility=0.25, skew_25d=0.01),
        phi=_phi(),
        r=RBlock(
            market_regime=MarketRegime.neutral,
            macro_cycle_regime=MacroCycleRegime.expansion,
            conviction=0.5,
        ),
        x=XBlock(),
    )


def _omega() -> Omega:
    observability = BlockObservability(q=0.8, f=0.8, t=0.8, p=0.8, r=0.8, x=0.8)
    return Omega(
        omega_id="o1",
        market_svp=_market_svp(),
        question_ledger=_snapshot().q.ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="src-1",
                observed_at="2026-01-01T00:00:00Z",
                source_type="internal",
            ),
        ),
        block_confidence=observability,
        block_observability=observability,
        confidence=0.8,
    )


def test_state_event_features_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        StateEventFeatures(
            catalyst_strength=1.1,
            follow_through=0.5,
            pricing_saturation=0.5,
            disconfirmation_strength=0.1,
            regime_shock=0.1,
            observation_freshness=0.9,
        )


def test_state_config_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        StateConfig(softmax_temperature=0.0)


def test_state_config_rejects_too_small_tie_break_epsilon() -> None:
    with pytest.raises(ValidationError):
        StateConfig(tie_break_epsilon=1e-10)


def test_state_engine_result_transition_confidence_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        StateEngineResult(
            evidence_scores=_state_probabilities(),
            updated_probabilities=_state_probabilities(),
            updated_phi=_phi(),
            updated_market_svp=_market_svp(),
            dominant_state=LifecycleState.dormant,
            transition_confidence=1.1,
        )


def test_state_engine_result_accepts_valid_payload() -> None:
    result = StateEngineResult(
        evidence_scores=_state_probabilities(),
        updated_probabilities=_state_probabilities(),
        updated_phi=_phi(),
        updated_market_svp=_market_svp(),
        dominant_state=LifecycleState.dormant,
        transition_confidence=0.4,
    )
    assert result.transition_confidence == pytest.approx(0.4)


def test_snapshot_and_omega_helpers_are_valid() -> None:
    snapshot = _snapshot()
    omega = _omega()
    projection = ProjectionSnapshot(
        projection_id="p1",
        horizon_days=30,
        point_estimate=0.1,
        lower_bound=-0.1,
        upper_bound=0.3,
        confidence=0.5,
    )
    assert snapshot.phi.dominant_state == LifecycleState.dormant
    assert omega.market_svp.regime == MarketRegime.neutral
    assert projection.confidence == pytest.approx(0.5)
