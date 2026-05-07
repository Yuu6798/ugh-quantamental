"""Tests for deterministic projection engine computations."""

import math

import pytest

from ugh_quantamental.engine.projection import (
    build_projection_snapshot,
    compute_alignment,
    compute_conviction,
    compute_e_raw,
    compute_e_star,
    compute_gravity_bias,
    compute_mismatch_px,
    compute_mismatch_sem,
    compute_u,
    compute_urgency,
    run_projection_engine,
)
from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    QuestionDirectionSign,
    QuestionFeatures,
    SignalFeatures,
)


@pytest.fixture
def baseline_question() -> QuestionFeatures:
    return QuestionFeatures(
        question_direction=QuestionDirectionSign.positive,
        q_strength=0.8,
        s_q=0.75,
        temporal_score=0.6,
    )


@pytest.fixture
def baseline_signal() -> SignalFeatures:
    return SignalFeatures(
        fundamental_score=0.4,
        technical_score=0.2,
        price_implied_score=0.1,
        context_score=1.2,
        grv_lock=0.9,
        regime_fit=0.8,
        narrative_dispersion=0.2,
        evidence_confidence=0.7,
        fire_probability=0.6,
    )


def test_compute_u_hand_checkable(
    baseline_question: QuestionFeatures,
    baseline_signal: SignalFeatures,
) -> None:
    config = ProjectionConfig()
    value = compute_u(baseline_question, baseline_signal, config)
    # v2 alpha defaults: u_weight=0.40, t_weight=0.30, f_weight=0.30 (unchanged).
    # compute_u uses f_weight + t_weight only (not u_weight). With t_weight bumped
    # 0.20→0.30 the signal_blend coefficient changes:
    #   directional = 1.0 * 0.8 * 0.75 = 0.6
    #   raw_u = 0.6 * (0.5 + 0.5*0.6) + (0.30*0.4 + 0.30*0.2) * (1.2/2.0)
    #         = 0.48 + 0.18 * 0.6 = 0.48 + 0.108 = 0.588
    assert value == pytest.approx(0.588)


def test_alignment_reduces_with_high_disagreement() -> None:
    config = ProjectionConfig()
    low_gap = AlignmentInputs(d_qf=0.1, d_qt=0.1, d_qp=0.1, d_ft=0.1, d_fp=0.1, d_tp=0.1)
    high_gap = AlignmentInputs(d_qf=0.9, d_qt=0.9, d_qp=0.9, d_ft=0.9, d_fp=0.9, d_tp=0.9)
    assert compute_alignment(low_gap, config) > compute_alignment(high_gap, config)
    assert compute_alignment(high_gap, config) == pytest.approx(0.1)


def test_gravity_bias_increases_with_lock_and_regime() -> None:
    config = ProjectionConfig()
    low = SignalFeatures(
        fundamental_score=0.0,
        technical_score=0.0,
        price_implied_score=0.0,
        context_score=1.0,
        grv_lock=0.1,
        regime_fit=0.1,
        narrative_dispersion=0.5,
        evidence_confidence=0.5,
        fire_probability=0.5,
    )
    high = low.model_copy(update={"grv_lock": 0.9, "regime_fit": 0.9})
    assert compute_gravity_bias(high, config) > compute_gravity_bias(low, config)


def test_mismatch_sign_behaviors(
    baseline_question: QuestionFeatures,
    baseline_signal: SignalFeatures,
) -> None:
    assert compute_mismatch_px(0.3, baseline_signal) > 0
    assert compute_mismatch_px(-0.2, baseline_signal) < 0

    sem_pos = compute_mismatch_sem(baseline_question, baseline_signal)
    neg_question = baseline_question.model_copy(
        update={"question_direction": QuestionDirectionSign.negative}
    )
    sem_neg = compute_mismatch_sem(neg_question, baseline_signal)
    assert sem_pos > 0
    assert sem_neg < 0


def test_zero_confidence_drives_zero_conviction(
    baseline_question: QuestionFeatures,
    baseline_signal: SignalFeatures,
) -> None:
    signal = baseline_signal.model_copy(update={"evidence_confidence": 0.0})
    conviction = compute_conviction(signal, alignment=1.0, mismatch_px=0.0, mismatch_sem=0.0)
    urgency = compute_urgency(baseline_question, signal, conviction)
    assert conviction == pytest.approx(0.0)
    assert 0.0 <= urgency <= 1.0


def test_urgency_increases_with_temporal_and_fire() -> None:
    low_q = QuestionFeatures(
        question_direction=QuestionDirectionSign.neutral,
        q_strength=0.5,
        s_q=0.5,
        temporal_score=0.1,
    )
    high_q = low_q.model_copy(update={"temporal_score": 0.9})
    low_s = SignalFeatures(
        fundamental_score=0.0,
        technical_score=0.0,
        price_implied_score=0.0,
        context_score=1.0,
        grv_lock=0.5,
        regime_fit=0.5,
        narrative_dispersion=0.5,
        evidence_confidence=0.5,
        fire_probability=0.1,
    )
    high_s = low_s.model_copy(update={"fire_probability": 0.9})
    assert compute_urgency(high_q, high_s, conviction=0.5) > compute_urgency(
        low_q, low_s, conviction=0.5
    )


def test_build_projection_snapshot_bounds_are_finite_and_ordered() -> None:
    snapshot = build_projection_snapshot(
        projection_id="p-1",
        horizon_days=30,
        e_star=0.2,
        conviction=0.4,
        urgency=0.9,
        mismatch_px=0.6,
        mismatch_sem=-0.4,
        config=ProjectionConfig(),
    )
    assert math.isfinite(snapshot.lower_bound)
    assert math.isfinite(snapshot.upper_bound)
    assert snapshot.lower_bound <= snapshot.upper_bound


def test_build_projection_snapshot_rejects_non_finite_e_star() -> None:
    with pytest.raises(ValueError, match="finite"):
        build_projection_snapshot(
            projection_id="p-inf",
            horizon_days=10,
            e_star=float("nan"),
            conviction=0.5,
            urgency=0.5,
            mismatch_px=0.0,
            mismatch_sem=0.0,
            config=ProjectionConfig(),
        )


def test_compute_e_raw_and_e_star_hand_checkable(
    baseline_signal: SignalFeatures,
) -> None:
    config = ProjectionConfig()
    e_raw = compute_e_raw(
        u_score=0.576, signal_features=baseline_signal, alignment=0.7, config=config
    )
    gravity = compute_gravity_bias(baseline_signal, config)
    e_star = compute_e_star(e_raw, gravity)
    # v2 e_raw: direction_signal × conviction_multiplier × alignment with
    # alpha defaults (u_w=0.40, t_w=0.30, p_w=0.20, conviction_floor=0.5).
    #   direction_signal = (0.40*0.576 + 0.30*0.2 + 0.20*0.1) / 0.90
    #                    = 0.3104 / 0.90 ≈ 0.34488889
    #   conviction_multiplier = 0.5 + 0.5 * 0.6 = 0.80
    #   e_raw = 0.34488889 * 0.80 * 0.70 ≈ 0.19313778
    # gravity_bias unchanged: 0.20*0.9 + 0.15*0.8 - 0.10*0.2 = 0.28
    # e_star = e_raw + gravity ≈ 0.47313778
    assert e_raw == pytest.approx(0.19313778, abs=1e-7)
    assert gravity == pytest.approx(0.28)
    assert e_star == pytest.approx(0.47313778, abs=1e-7)


def test_run_projection_engine_end_to_end_deterministic(
    baseline_question: QuestionFeatures,
    baseline_signal: SignalFeatures,
) -> None:
    alignment_inputs = AlignmentInputs(
        d_qf=0.2,
        d_qt=0.3,
        d_qp=0.4,
        d_ft=0.1,
        d_fp=0.2,
        d_tp=0.3,
    )
    result = run_projection_engine(
        projection_id="proj-001",
        horizon_days=20,
        question_features=baseline_question,
        signal_features=baseline_signal,
        alignment_inputs=alignment_inputs,
    )

    # v2 alpha-default golden values (u_w=0.40, t_w=0.30, p_w=0.20,
    # conviction_floor=0.5; f_weight unchanged at 0.30):
    assert result.u_score == pytest.approx(0.588)
    assert result.alignment == pytest.approx(0.75)
    assert result.e_raw == pytest.approx(0.21013333, abs=1e-7)
    assert result.gravity_bias == pytest.approx(0.28)
    assert result.e_star == pytest.approx(0.49013333, abs=1e-7)
    assert result.mismatch_px == pytest.approx(0.39013333, abs=1e-7)
    assert result.mismatch_sem == pytest.approx(0.5)
    assert result.conviction == pytest.approx(0.40817, abs=1e-5)
    assert result.urgency == pytest.approx(0.599183, abs=1e-6)

    snap = result.projection_snapshot
    assert snap.projection_id == "proj-001"
    assert snap.horizon_days == 20
    assert snap.point_estimate == pytest.approx(0.49013333, abs=1e-7)
    assert snap.lower_bound == pytest.approx(0.06328505, abs=1e-7)
    assert snap.upper_bound == pytest.approx(0.91698162, abs=1e-7)
    assert snap.confidence == pytest.approx(result.conviction)


# ---------------------------------------------------------------------------
# v2 compute_e_raw unit tests (spec §8.1)
# ---------------------------------------------------------------------------


def _v2_alpha_signal(
    *,
    technical: float = 0.0,
    price_implied: float = 0.0,
    fire: float = 0.5,
) -> SignalFeatures:
    """SignalFeatures fixture with the three v2 directional inputs explicit.

    Other fields are set to neutral / zero values so the only knobs that
    affect ``compute_e_raw`` are ``technical_score`` /
    ``price_implied_score`` / ``fire_probability``.
    """
    return SignalFeatures(
        fundamental_score=0.0,
        technical_score=technical,
        price_implied_score=price_implied,
        context_score=1.0,
        grv_lock=0.0,
        regime_fit=0.5,
        narrative_dispersion=0.0,
        evidence_confidence=1.0,
        fire_probability=fire,
    )


@pytest.mark.parametrize("fire", [0.0, 0.5, 1.0])
def test_e_raw_zero_when_all_directional_inputs_zero(fire: float) -> None:
    config = ProjectionConfig()
    signal = _v2_alpha_signal(technical=0.0, price_implied=0.0, fire=fire)
    e_raw = compute_e_raw(u_score=0.0, signal_features=signal, alignment=1.0, config=config)
    assert e_raw == 0.0


def test_fire_zero_shrinks_but_does_not_flip() -> None:
    """fire=0 → multiplier=floor (0.5 default), shrinks magnitude to 50% of fire=1."""
    config = ProjectionConfig()
    signal_zero = _v2_alpha_signal(technical=0.5, price_implied=0.5, fire=0.0)
    signal_one = _v2_alpha_signal(technical=0.5, price_implied=0.5, fire=1.0)

    e_zero = compute_e_raw(u_score=0.5, signal_features=signal_zero, alignment=1.0, config=config)
    e_one = compute_e_raw(u_score=0.5, signal_features=signal_one, alignment=1.0, config=config)

    assert e_zero > 0.0
    # conviction_multiplier(fire=0) / conviction_multiplier(fire=1) = floor / 1.0 = 0.5
    assert e_zero == pytest.approx(0.5 * e_one)


def test_fire_one_maximizes_signal() -> None:
    """fire=1 → multiplier=1.0 (no shrink); e_raw == direction_signal × alignment."""
    config = ProjectionConfig()
    signal = _v2_alpha_signal(technical=0.5, price_implied=0.5, fire=1.0)
    e_raw = compute_e_raw(u_score=0.5, signal_features=signal, alignment=0.8, config=config)

    direction_signal = (
        config.u_weight * 0.5 + config.t_weight * 0.5 + config.p_weight * 0.5
    ) / (config.u_weight + config.t_weight + config.p_weight)
    assert e_raw == pytest.approx(direction_signal * 0.8)


def test_price_implied_alone_drives_direction() -> None:
    """u=0, technical=0, price_implied=+1.0, fire=1.0 → e_raw = 0.20/0.90 × alignment."""
    config = ProjectionConfig()
    signal = _v2_alpha_signal(technical=0.0, price_implied=1.0, fire=1.0)
    alignment = 0.7
    e_raw = compute_e_raw(
        u_score=0.0, signal_features=signal, alignment=alignment, config=config
    )
    expected = (config.p_weight / (config.u_weight + config.t_weight + config.p_weight)) * alignment
    assert e_raw == pytest.approx(expected)


@pytest.mark.parametrize("fire", [0.0, 0.5, 1.0])
def test_no_anti_thrust_bias_in_choppy(fire: float) -> None:
    """All directional inputs zero → e_raw = 0 regardless of fire (spec §6.1).

    This is the structural fix for the v1 anti-thrust bias documented in
    spec §3 (compute_e_raw collapsed to ``-f_weight`` when fire=0,
    independent of any directional context).
    """
    config = ProjectionConfig()
    signal = _v2_alpha_signal(technical=0.0, price_implied=0.0, fire=fire)
    assert compute_e_raw(0.0, signal, alignment=1.0, config=config) == 0.0


def test_zero_weight_guard() -> None:
    """All three direction weights zero → e_raw=0 (preserves bounded/no-NaN)."""
    config = ProjectionConfig(u_weight=0.0, t_weight=0.0, p_weight=0.0)
    signal = _v2_alpha_signal(technical=0.5, price_implied=0.5, fire=1.0)
    assert compute_e_raw(0.5, signal, alignment=1.0, config=config) == 0.0
