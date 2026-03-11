from pydantic import ValidationError
import pytest

from ugh_quantamental.schemas.omega import Omega


def _valid_omega_payload() -> dict:
    return {
        "omega_id": "omega-001",
        "market_svp": {
            "as_of": "2026-01-15",
            "regime": "risk_on",
            "phi": {
                "dominant_state": "expansion",
                "probabilities": {
                    "dormant": 0.05,
                    "setup": 0.10,
                    "fire": 0.15,
                    "expansion": 0.40,
                    "exhaustion": 0.20,
                    "failure": 0.10,
                },
            },
            "confidence": 0.7,
        },
        "question_ledger": {
            "as_of": "2026-01-15",
            "questions": [
                {
                    "question_id": "q1",
                    "direction": "positive",
                    "score": 0.4,
                    "weight": 0.6,
                }
            ],
            "coverage_ratio": 0.8,
        },
        "evidence_lineage": [
            {
                "source_id": "feed-1",
                "observed_at": "2026-01-15T00:00:00Z",
                "source_type": "market_data",
            }
        ],
        "block_confidence": {"q": 0.8, "f": 0.7, "t": 0.9, "p": 0.8, "r": 0.75, "x": 0.6},
        "block_observability": {
            "q": 0.85,
            "f": 0.7,
            "t": 0.95,
            "p": 0.8,
            "r": 0.7,
            "x": 0.5,
        },
        "confidence": 0.72,
    }


def test_omega_valid_payload() -> None:
    model = Omega.model_validate(_valid_omega_payload())
    assert model.omega_id == "omega-001"


def test_omega_reject_missing_lineage() -> None:
    payload = _valid_omega_payload()
    payload["evidence_lineage"] = []

    with pytest.raises(ValidationError):
        Omega.model_validate(payload)


def test_omega_reject_block_confidence_over_one() -> None:
    payload = _valid_omega_payload()
    payload["block_confidence"]["q"] = 1.1

    with pytest.raises(ValidationError):
        Omega.model_validate(payload)
