"""Deterministic lifecycle-state update engine (Milestone 5)."""

from __future__ import annotations

import math

from ugh_quantamental.engine.projection_models import ProjectionEngineResult
from ugh_quantamental.engine.state_models import StateConfig, StateEngineResult, StateEventFeatures
from ugh_quantamental.schemas.enums import LifecycleState
from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
from ugh_quantamental.schemas.omega import Omega
from ugh_quantamental.schemas.ssv import SSVSnapshot

_STATES: tuple[LifecycleState, ...] = (
    LifecycleState.dormant,
    LifecycleState.setup,
    LifecycleState.fire,
    LifecycleState.expansion,
    LifecycleState.exhaustion,
    LifecycleState.failure,
)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _to_map(probabilities: StateProbabilities) -> dict[LifecycleState, float]:
    raw = probabilities.model_dump()
    return {state: raw[state.value] for state in _STATES}


def _to_probabilities(values: dict[LifecycleState, float]) -> StateProbabilities:
    return StateProbabilities(**{state.value: values[state] for state in _STATES})


def _normalize_simple(values: dict[LifecycleState, float]) -> StateProbabilities:
    clipped = {state: _clamp(values[state]) for state in _STATES}
    total = sum(clipped.values())
    if total <= 0.0:
        uniform = 1.0 / len(_STATES)
        return _to_probabilities({state: uniform for state in _STATES})
    return _to_probabilities({state: clipped[state] / total for state in _STATES})


def compute_block_quality(omega: Omega, event_features: StateEventFeatures) -> float:
    """Compute quality of usable observations from Omega and freshness."""
    conf = omega.block_confidence
    obs = omega.block_observability
    block_score = (
        (conf.q * obs.q)
        + (conf.f * obs.f)
        + (conf.t * obs.t)
        + (conf.p * obs.p)
        + (conf.r * obs.r)
        + (conf.x * obs.x)
    ) / 6.0
    return _clamp(0.7 * block_score + 0.3 * event_features.observation_freshness)


def compute_state_evidence(
    snapshot: SSVSnapshot,
    projection_result: ProjectionEngineResult,
    event_features: StateEventFeatures,
    config: StateConfig,
) -> dict[LifecycleState, float]:
    """Compute deterministic raw lifecycle evidence scores from normalized features."""
    prior = snapshot.phi.probabilities
    p_fire = prior.fire
    p_exp = prior.expansion

    conviction = projection_result.conviction
    urgency = projection_result.urgency
    e_star = projection_result.e_star
    positive_e = _clamp((e_star + 1.0) / 2.0)
    negative_e = _clamp((-e_star + 1.0) / 2.0)

    catalyst = event_features.catalyst_strength
    follow_through = event_features.follow_through
    pricing_sat = event_features.pricing_saturation
    disconfirmation = event_features.disconfirmation_strength
    regime_shock = event_features.regime_shock
    mismatch_shrink = _clamp(1.0 - abs(projection_result.mismatch_px))

    dormant = config.dormant_weight * _clamp(
        (1.0 - conviction)
        * (1.0 - urgency)
        * (1.0 - catalyst)
        * (1.0 - follow_through)
    )
    setup = config.setup_weight * _clamp(
        positive_e * (1.0 - pricing_sat) * (1.0 - p_fire) * (1.0 - catalyst + 0.4 * catalyst)
    )
    fire = config.fire_weight * _clamp(catalyst * prior.fire * urgency * follow_through)
    expansion = config.expansion_weight * _clamp(
        positive_e * conviction * follow_through * (0.6 + 0.4 * (p_fire + p_exp))
    )
    exhaustion = config.exhaustion_weight * _clamp(
        positive_e * pricing_sat * mismatch_shrink * (0.5 + 0.5 * follow_through)
    )
    failure = config.failure_weight * _clamp(
        max(negative_e, disconfirmation, regime_shock)
    )

    return {
        LifecycleState.dormant: dormant,
        LifecycleState.setup: setup,
        LifecycleState.fire: fire,
        LifecycleState.expansion: expansion,
        LifecycleState.exhaustion: exhaustion,
        LifecycleState.failure: failure,
    }


def blend_with_prior(
    prior_probabilities: StateProbabilities,
    evidence_scores: dict[LifecycleState, float],
    config: StateConfig,
) -> dict[LifecycleState, float]:
    """Blend normalized evidence with prior lifecycle probabilities."""
    prior = _to_map(prior_probabilities)
    evidence_probs = normalize_state_probabilities(evidence_scores, config)
    evidence = _to_map(evidence_probs)
    weight_sum = config.prior_weight + config.evidence_weight
    prior_w = 0.0 if weight_sum == 0 else config.prior_weight / weight_sum
    evidence_w = 0.0 if weight_sum == 0 else config.evidence_weight / weight_sum

    return {
        state: _clamp(prior_w * prior[state] + evidence_w * evidence[state])
        for state in _STATES
    }


def normalize_state_probabilities(
    scores: dict[LifecycleState, float],
    config: StateConfig,
) -> StateProbabilities:
    """Apply softmax normalization to scores to produce valid lifecycle probabilities."""
    scaled = {state: scores[state] / config.softmax_temperature for state in _STATES}
    max_value = max(scaled.values())
    exps = {state: math.exp(scaled[state] - max_value) for state in _STATES}
    total = sum(exps.values())
    if total <= 0.0:
        uniform = 1.0 / len(_STATES)
        return _to_probabilities({state: uniform for state in _STATES})
    normalized = {state: exps[state] / total for state in _STATES}
    return _to_probabilities(normalized)


def resolve_dominant_state(
    probabilities: StateProbabilities,
    prior_dominant_state: LifecycleState,
) -> LifecycleState:
    """Resolve dominant state deterministically using prior-first tie policy."""
    values = _to_map(probabilities)
    max_value = max(values.values())
    tied_states = [
        state for state in _STATES if math.isclose(values[state], max_value, abs_tol=1e-12)
    ]
    if len(tied_states) == 1:
        return tied_states[0]
    if prior_dominant_state in tied_states:
        return prior_dominant_state
    for state in _STATES:
        if state in tied_states:
            return state
    return _STATES[0]


def build_phi(
    probabilities: StateProbabilities,
    prior_dominant_state: LifecycleState,
    config: StateConfig,
) -> Phi:
    """Build Phi and ensure unique dominant state via tiny deterministic tie break."""
    winner = resolve_dominant_state(probabilities, prior_dominant_state)
    values = _to_map(probabilities)
    max_value = max(values.values())
    tied_states = [
        state for state in _STATES if math.isclose(values[state], max_value, abs_tol=1e-12)
    ]

    if len(tied_states) > 1:
        values[winner] += config.tie_break_epsilon
        total = sum(values.values())
        values = {state: values[state] / total for state in _STATES}

    adjusted = _to_probabilities(values)
    return Phi(dominant_state=winner, probabilities=adjusted)


def build_market_svp(
    snapshot: SSVSnapshot,
    omega: Omega,
    updated_phi: Phi,
    block_quality: float,
    transition_confidence: float,
    config: StateConfig,
) -> MarketSVP:
    """Build updated MarketSVP preserving regime and replacing lifecycle envelope."""
    confidence = _clamp(
        config.quality_confidence_weight * block_quality
        + config.transition_confidence_weight * transition_confidence
    )
    return MarketSVP(
        as_of=snapshot.t.timestamp,
        regime=omega.market_svp.regime,
        phi=updated_phi,
        confidence=confidence,
    )


def run_state_engine(
    snapshot: SSVSnapshot,
    omega: Omega,
    projection_result: ProjectionEngineResult,
    event_features: StateEventFeatures,
    config: StateConfig | None = None,
) -> StateEngineResult:
    """Run deterministic lifecycle-state update using prior + evidence blending."""
    cfg = config or StateConfig()
    block_quality = compute_block_quality(omega, event_features)
    evidence_raw = compute_state_evidence(snapshot, projection_result, event_features, cfg)
    evidence_probs = normalize_state_probabilities(evidence_raw, cfg)

    blended = blend_with_prior(snapshot.phi.probabilities, evidence_raw, cfg)
    updated_probs = _normalize_simple(blended)
    updated_phi = build_phi(updated_probs, snapshot.phi.dominant_state, cfg)

    prior_probs = _to_map(snapshot.phi.probabilities)
    updated_map = _to_map(updated_phi.probabilities)
    movement = 0.5 * sum(abs(updated_map[state] - prior_probs[state]) for state in _STATES)
    transition_confidence = _clamp((1.0 - movement) * block_quality)

    updated_market_svp = build_market_svp(
        snapshot=snapshot,
        omega=omega,
        updated_phi=updated_phi,
        block_quality=block_quality,
        transition_confidence=transition_confidence,
        config=cfg,
    )

    return StateEngineResult(
        evidence_scores=evidence_probs,
        updated_probabilities=updated_phi.probabilities,
        updated_phi=updated_phi,
        updated_market_svp=updated_market_svp,
        dominant_state=updated_phi.dominant_state,
        transition_confidence=transition_confidence,
    )
