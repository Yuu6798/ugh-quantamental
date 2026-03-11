"""Tests for deterministic projection input/result models."""

import pytest
from pydantic import ValidationError

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
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
