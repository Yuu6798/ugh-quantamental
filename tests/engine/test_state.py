"""Tests for deterministic lifecycle state engine behavior."""

import math

import pytest
from pydantic import ValidationError

from ugh_quantamental.engine.projection_models import ProjectionEngineResult
from ugh_quantamental.engine.state import (
    build_market_svp,
    build_phi,
    normalize_state_probabilities,
    resolve_dominant_state,
    run_state_engine,
)
from ugh_quantamental.engine.state_models import StateConfig, StateEventFeatures
from ugh_quantamental.schemas.enums import LifecycleState, MacroCycleRegime, MarketRegime, QuestionDirection
from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
from ugh_quantamental.schemas.omega import BlockObservability, EvidenceLineageRecord, Omega
from ugh_quantamental.schemas.projection import ProjectionSnapshot
from ugh_quantamental.schemas.ssv import FBlock, PBlock, QBlock, QuestionLedger, QuestionRecord, RBlock, SSVSnapshot, TBlock, XBlock


@pytest.fixture
def base_config() -> StateConfig:
    return StateConfig()


def _make_phi(dominant: LifecycleState) -> Phi:
    if dominant is LifecycleState.dormant:
        probs = StateProbabilities(
            dormant=0.60,
            setup=0.20,
            fire=0.05,
            expansion=0.05,
            exhaustion=0.05,
            failure=0.05,
        )
    elif dominant is LifecycleState.setup:
        probs = StateProbabilities(
            dormant=0.15,
            setup=0.45,
            fire=0.15,
            expansion=0.10,
            exhaustion=0.05,
            failure=0.10,
        )
    elif dominant is LifecycleState.fire:
        probs = StateProbabilities(
            dormant=0.10,
            setup=0.15,
            fire=0.45,
            expansion=0.15,
            exhaustion=0.10,
            failure=0.05,
        )
    else:
        probs = StateProbabilities(
            dormant=0.10,
            setup=0.10,
            fire=0.25,
            expansion=0.35,
            exhaustion=0.10,
            failure=0.10,
        )
    return Phi(dominant_state=dominant, probabilities=probs)


def _make_snapshot(prior_dominant: LifecycleState = LifecycleState.setup) -> SSVSnapshot:
    ledger = QuestionLedger(
        as_of="2026-01-01",
        coverage_ratio=0.9,
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
        f=FBlock(factor_count=5, aggregate_signal=0.3),
        t=TBlock(timestamp="2026-01-01T00:00:00Z", lookback_days=20),
        p=PBlock(implied_move_30d=0.03, implied_volatility=0.22, skew_25d=0.01),
        phi=_make_phi(prior_dominant),
        r=RBlock(
            market_regime=MarketRegime.risk_on,
            macro_cycle_regime=MacroCycleRegime.expansion,
            conviction=0.7,
        ),
        x=XBlock(),
    )


def _make_omega(snapshot: SSVSnapshot, regime: MarketRegime = MarketRegime.risk_on) -> Omega:
    block = BlockObservability(q=0.9, f=0.8, t=0.8, p=0.9, r=0.7, x=0.8)
    return Omega(
        omega_id="om-1",
        market_svp=MarketSVP(
            as_of=snapshot.t.timestamp,
            regime=regime,
            phi=snapshot.phi,
            confidence=0.6,
        ),
        question_ledger=snapshot.q.ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="src",
                observed_at=snapshot.t.timestamp,
                source_type="internal",
            ),
        ),
        block_confidence=block,
        block_observability=block,
        confidence=0.75,
    )


def _projection(
    *,
    e_star: float,
    conviction: float,
    urgency: float,
    mismatch_px: float,
    mismatch_sem: float,
) -> ProjectionEngineResult:
    snapshot = ProjectionSnapshot(
        projection_id="proj-1",
        horizon_days=30,
        point_estimate=e_star,
        lower_bound=e_star - 0.1,
        upper_bound=e_star + 0.1,
        confidence=conviction,
    )
    return ProjectionEngineResult(
        u_score=0.0,
        alignment=0.6,
        e_raw=e_star,
        gravity_bias=0.0,
        e_star=e_star,
        mismatch_px=mismatch_px,
        mismatch_sem=mismatch_sem,
        conviction=conviction,
        urgency=urgency,
        projection_snapshot=snapshot,
    )


def test_low_signal_case_leans_dormant(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.dormant)
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=-0.1,
            conviction=0.1,
            urgency=0.1,
            mismatch_px=0.2,
            mismatch_sem=0.1,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.05,
            follow_through=0.05,
            pricing_saturation=0.1,
            disconfirmation_strength=0.1,
            regime_shock=0.1,
            observation_freshness=0.8,
        ),
        config=base_config,
    )
    assert result.dominant_state is LifecycleState.dormant


def test_pre_catalyst_case_leans_setup(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.setup)
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=0.35,
            conviction=0.5,
            urgency=0.35,
            mismatch_px=0.3,
            mismatch_sem=0.2,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.2,
            follow_through=0.3,
            pricing_saturation=0.1,
            disconfirmation_strength=0.05,
            regime_shock=0.05,
            observation_freshness=0.9,
        ),
        config=base_config,
    )
    assert result.dominant_state is LifecycleState.setup


def test_strong_catalyst_case_leans_fire(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.fire)
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=0.6,
            conviction=0.8,
            urgency=0.85,
            mismatch_px=0.1,
            mismatch_sem=0.1,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.95,
            follow_through=0.9,
            pricing_saturation=0.2,
            disconfirmation_strength=0.05,
            regime_shock=0.05,
            observation_freshness=0.9,
        ),
        config=base_config,
    )
    assert result.dominant_state is LifecycleState.fire


def test_expansion_case_with_strong_follow_through(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.expansion)
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=0.8,
            conviction=0.9,
            urgency=0.7,
            mismatch_px=0.05,
            mismatch_sem=0.05,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.7,
            follow_through=0.95,
            pricing_saturation=0.35,
            disconfirmation_strength=0.05,
            regime_shock=0.05,
            observation_freshness=0.95,
        ),
        config=base_config,
    )
    assert result.dominant_state is LifecycleState.expansion


def test_exhaustion_case_with_high_pricing_saturation(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.expansion)
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=0.45,
            conviction=0.7,
            urgency=0.5,
            mismatch_px=0.05,
            mismatch_sem=0.05,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.3,
            follow_through=0.6,
            pricing_saturation=0.95,
            disconfirmation_strength=0.05,
            regime_shock=0.05,
            observation_freshness=0.8,
        ),
        config=base_config,
    )
    assert result.evidence_scores.exhaustion > result.evidence_scores.fire


def test_failure_case_negative_signal_or_disconfirmation(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.setup)
    failure_config = base_config.model_copy(
        update={"prior_weight": 0.2, "evidence_weight": 0.8, "failure_weight": 1.4}
    )
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=-0.85,
            conviction=0.3,
            urgency=0.4,
            mismatch_px=0.4,
            mismatch_sem=0.4,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.2,
            follow_through=0.2,
            pricing_saturation=0.2,
            disconfirmation_strength=0.9,
            regime_shock=0.8,
            observation_freshness=0.85,
        ),
        config=failure_config,
    )
    assert result.dominant_state is LifecycleState.failure


def test_dominant_state_resolution_is_deterministic() -> None:
    tied = StateProbabilities(
        dormant=0.3,
        setup=0.3,
        fire=0.2,
        expansion=0.1,
        exhaustion=0.05,
        failure=0.05,
    )
    winner = resolve_dominant_state(tied, LifecycleState.setup)
    phi = build_phi(tied, LifecycleState.setup, StateConfig())
    assert winner is LifecycleState.setup
    assert phi.dominant_state is LifecycleState.setup




def test_build_phi_tied_probabilities_valid_with_min_safe_epsilon() -> None:
    tied = StateProbabilities(
        dormant=0.25,
        setup=0.25,
        fire=0.20,
        expansion=0.15,
        exhaustion=0.10,
        failure=0.05,
    )
    config = StateConfig(tie_break_epsilon=1e-8)

    try:
        phi = build_phi(tied, LifecycleState.setup, config)
    except ValidationError as exc:  # pragma: no cover - regression safety
        pytest.fail(f"build_phi raised unexpectedly for min-safe epsilon: {exc}")

    values = phi.probabilities.model_dump()
    max_value = max(values.values())
    top_states = [name for name, value in values.items() if math.isclose(value, max_value, abs_tol=1e-12)]

    assert phi.dominant_state is LifecycleState.setup
    assert top_states == [LifecycleState.setup.value]

def test_market_svp_update_preserves_regime_and_replaces_phi() -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.setup)
    omega = _make_omega(snapshot, regime=MarketRegime.risk_off)
    probs = normalize_state_probabilities(
        {
            LifecycleState.dormant: 0.1,
            LifecycleState.setup: 0.2,
            LifecycleState.fire: 0.3,
            LifecycleState.expansion: 0.4,
            LifecycleState.exhaustion: 0.2,
            LifecycleState.failure: 0.1,
        },
        StateConfig(),
    )
    phi = build_phi(probs, LifecycleState.setup, StateConfig())
    updated = build_market_svp(
        snapshot=snapshot,
        omega=omega,
        updated_phi=phi,
        block_quality=0.7,
        transition_confidence=0.8,
        config=StateConfig(),
    )
    assert updated.regime is MarketRegime.risk_off
    assert updated.phi == phi




def test_run_state_engine_rejects_non_finite_projection_value(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.setup)
    with pytest.raises(ValueError, match="finite"):
        run_state_engine(
            snapshot=snapshot,
            omega=_make_omega(snapshot),
            projection_result=_projection(
                e_star=float("nan"),
                conviction=0.55,
                urgency=0.45,
                mismatch_px=0.2,
                mismatch_sem=0.25,
            ),
            event_features=StateEventFeatures(
                catalyst_strength=0.4,
                follow_through=0.5,
                pricing_saturation=0.3,
                disconfirmation_strength=0.15,
                regime_shock=0.1,
                observation_freshness=0.9,
            ),
            config=base_config,
        )


def test_normalize_state_probabilities_rejects_non_finite_scaled_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        normalize_state_probabilities(
            {
                LifecycleState.dormant: 0.1,
                LifecycleState.setup: 0.2,
                LifecycleState.fire: 0.3,
                LifecycleState.expansion: float("inf"),
                LifecycleState.exhaustion: 0.2,
                LifecycleState.failure: 0.1,
            },
            StateConfig(),
        )

def test_output_probabilities_sum_to_one_and_confidence_bounded(base_config: StateConfig) -> None:
    snapshot = _make_snapshot(prior_dominant=LifecycleState.setup)
    result = run_state_engine(
        snapshot=snapshot,
        omega=_make_omega(snapshot),
        projection_result=_projection(
            e_star=0.25,
            conviction=0.55,
            urgency=0.45,
            mismatch_px=0.2,
            mismatch_sem=0.25,
        ),
        event_features=StateEventFeatures(
            catalyst_strength=0.4,
            follow_through=0.5,
            pricing_saturation=0.3,
            disconfirmation_strength=0.15,
            regime_shock=0.1,
            observation_freshness=0.9,
        ),
        config=base_config,
    )
    total = sum(result.updated_probabilities.model_dump().values())
    assert math.isclose(total, 1.0, abs_tol=1e-8)
    assert 0.0 <= result.transition_confidence <= 1.0
