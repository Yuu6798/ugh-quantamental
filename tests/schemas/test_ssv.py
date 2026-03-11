from pydantic import ValidationError
import pytest

from ugh_quantamental.schemas.ssv import SSVSnapshot


def _valid_ssv_payload() -> dict:
    return {
        "snapshot_id": "ssv-1",
        "q": {
            "ledger": {
                "as_of": "2026-01-15",
                "questions": [
                    {
                        "question_id": "q-1",
                        "direction": "negative",
                        "score": -0.3,
                        "weight": 0.5,
                    }
                ],
                "coverage_ratio": 0.9,
            }
        },
        "f": {"factor_count": 12, "aggregate_signal": 0.25},
        "t": {"timestamp": "2026-01-15T00:00:00Z", "lookback_days": 30},
        "p": {"implied_move_30d": 0.06, "implied_volatility": 0.22, "skew_25d": -0.15},
        "phi": {
            "dominant_state": "expansion",
            "probabilities": {
                "dormant": 0.05,
                "setup": 0.10,
                "fire": 0.20,
                "expansion": 0.35,
                "exhaustion": 0.20,
                "failure": 0.10,
            },
        },
        "r": {
            "market_regime": "risk_off",
            "macro_cycle_regime": "slowdown",
            "conviction": 0.65,
        },
        "x": {"tags": ["baseline"], "notes": "frozen v1"},
    }


def test_ssv_snapshot_valid_payload() -> None:
    model = SSVSnapshot.model_validate(_valid_ssv_payload())
    assert model.r.macro_cycle_regime.value == "slowdown"


def test_ssv_snapshot_reject_invalid_lookback_days() -> None:
    payload = _valid_ssv_payload()
    payload["t"]["lookback_days"] = 0

    with pytest.raises(ValidationError):
        SSVSnapshot.model_validate(payload)


def test_ssv_snapshot_reject_invalid_implied_volatility() -> None:
    payload = _valid_ssv_payload()
    payload["p"]["implied_volatility"] = -0.01

    with pytest.raises(ValidationError):
        SSVSnapshot.model_validate(payload)
