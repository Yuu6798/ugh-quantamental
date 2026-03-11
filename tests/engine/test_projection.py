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
    assert value == pytest.approx(0.576)


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
    e_raw = compute_e_raw(u_score=0.576, signal_features=baseline_signal, alignment=0.7, config=config)
    gravity = compute_gravity_bias(baseline_signal, config)
    e_star = compute_e_star(e_raw, gravity)
    assert e_raw == pytest.approx(0.2716)
    assert gravity == pytest.approx(0.28)
    assert e_star == pytest.approx(0.5516)


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

    assert result.u_score == pytest.approx(0.576)
    assert result.alignment == pytest.approx(0.75)
    assert result.e_raw == pytest.approx(0.291)
    assert result.gravity_bias == pytest.approx(0.28)
    assert result.e_star == pytest.approx(0.571)
    assert result.mismatch_px == pytest.approx(0.471)
    assert result.mismatch_sem == pytest.approx(0.5)
    assert result.conviction == pytest.approx(0.39755625)
    assert result.urgency == pytest.approx(0.600244375)

    snap = result.projection_snapshot
    assert snap.projection_id == "proj-001"
    assert snap.horizon_days == 20
    assert snap.point_estimate == pytest.approx(0.571)
    assert snap.lower_bound == pytest.approx(0.13325240625)
    assert snap.upper_bound == pytest.approx(1.00874759375)
    assert snap.confidence == pytest.approx(result.conviction)
