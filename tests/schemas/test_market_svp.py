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


def test_state_probabilities_reject_sum_not_one() -> None:
    payload = _valid_phi_probabilities()
    payload["failure"] = 0.11

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
