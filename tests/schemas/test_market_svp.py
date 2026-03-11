from pydantic import ValidationError
import pytest

from ugh_quantamental.schemas.market_svp import MarketSVP, StateProbabilities


def _valid_phi_probabilities() -> dict:
    return {
        "dormant": 0.10,
        "setup": 0.15,
        "fire": 0.25,
        "expansion": 0.20,
        "exhaustion": 0.20,
        "failure": 0.10,
    }


def test_state_probabilities_valid_payload() -> None:
    model = StateProbabilities.model_validate(_valid_phi_probabilities())
    assert model.fire == 0.25


def test_state_probabilities_accepts_rounded_total_within_tolerance() -> None:
    model = StateProbabilities.model_validate(
        {
            "dormant": 0.166667,
            "setup": 0.166667,
            "fire": 0.166667,
            "expansion": 0.166667,
            "exhaustion": 0.166667,
            "failure": 0.166667,
        }
    )
    assert model.failure == 0.166667


def test_market_svp_valid_payload() -> None:
    payload = {
        "as_of": "2026-01-15",
        "regime": "neutral",
        "phi": {
            "dominant_state": "fire",
            "probabilities": _valid_phi_probabilities(),
        },
        "confidence": 0.75,
    }

    model = MarketSVP.model_validate(payload)
    assert model.phi.dominant_state.value == "fire"


def test_state_probabilities_reject_sum_materially_outside_tolerance() -> None:
    payload = _valid_phi_probabilities()
    payload["failure"] = 0.101

    with pytest.raises(ValidationError):
        StateProbabilities.model_validate(payload)


def test_market_svp_reject_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        MarketSVP.model_validate(
            {
                "as_of": "2026-01-15",
                "regime": "neutral",
                "phi": {
                    "dominant_state": "fire",
                    "probabilities": _valid_phi_probabilities(),
                },
                "confidence": 1.1,
            }
        )


def test_market_svp_reject_dominant_state_mismatch() -> None:
    payload = {
        "as_of": "2026-01-15",
        "regime": "neutral",
        "phi": {
            "dominant_state": "setup",
            "probabilities": _valid_phi_probabilities(),
        },
        "confidence": 0.75,
    }

    with pytest.raises(ValidationError):
        MarketSVP.model_validate(payload)


def test_market_svp_reject_tied_highest_probability() -> None:
    payload = {
        "as_of": "2026-01-15",
        "regime": "neutral",
        "phi": {
            "dominant_state": "fire",
            "probabilities": {
                "dormant": 0.10,
                "setup": 0.15,
                "fire": 0.25,
                "expansion": 0.25,
                "exhaustion": 0.15,
                "failure": 0.10,
            },
        },
        "confidence": 0.75,
    }

    with pytest.raises(ValidationError):
        MarketSVP.model_validate(payload)
