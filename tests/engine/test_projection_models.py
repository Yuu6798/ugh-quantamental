"""Tests for deterministic projection input/result models."""

import math

import pytest
from pydantic import ValidationError

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    QuestionDirectionSign,
    QuestionFeatures,
    SignalFeatures,
)


def test_question_features_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        QuestionFeatures(
            question_direction=QuestionDirectionSign.positive,
            q_strength=1.1,
            s_q=0.5,
            temporal_score=0.3,
        )


def test_signal_features_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        SignalFeatures(
            fundamental_score=0.0,
            technical_score=0.0,
            price_implied_score=0.0,
            context_score=2.1,
            grv_lock=0.5,
            regime_fit=0.5,
            narrative_dispersion=0.1,
            evidence_confidence=0.8,
            fire_probability=0.2,
        )


def test_alignment_inputs_default_weights() -> None:
    inputs = AlignmentInputs(
        d_qf=0.1,
        d_qt=0.2,
        d_qp=0.3,
        d_ft=0.4,
        d_fp=0.5,
        d_tp=0.6,
    )
    assert inputs.w_qf == pytest.approx(1.0)
    assert inputs.w_tp == pytest.approx(1.0)


def test_projection_config_rejects_nan_gravity_coefficient() -> None:
    with pytest.raises(ValidationError):
        ProjectionConfig(gravity_lock_coef=math.nan)


def test_projection_config_rejects_inf_non_gravity_coefficient() -> None:
    with pytest.raises(ValidationError):
        ProjectionConfig(bounds_base_width=math.inf)


def test_projection_config_rejects_negative_inf_coefficient() -> None:
    with pytest.raises(ValidationError):
        ProjectionConfig(gravity_dispersion_coef=-math.inf)


def test_alignment_inputs_rejects_inf_weight() -> None:
    with pytest.raises(ValidationError):
        AlignmentInputs(
            d_qf=0.1,
            d_qt=0.2,
            d_qp=0.3,
            d_ft=0.4,
            d_fp=0.5,
            d_tp=0.6,
            w_qf=math.inf,
        )


def test_projection_config_accepts_finite_values() -> None:
    config = ProjectionConfig(
        u_weight=0.7,
        gravity_lock_coef=0.15,
        bounds_max_width=0.9,
    )
    assert config.u_weight == pytest.approx(0.7)


def test_alignment_inputs_accepts_finite_values() -> None:
    inputs = AlignmentInputs(
        d_qf=0.1,
        d_qt=0.2,
        d_qp=0.3,
        d_ft=0.4,
        d_fp=0.5,
        d_tp=0.6,
        w_qf=0.8,
    )
    assert inputs.w_qf == pytest.approx(0.8)
