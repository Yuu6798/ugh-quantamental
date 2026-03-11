from pydantic import ValidationError
import pytest

from ugh_quantamental.schemas.projection import ProjectionSnapshot


def test_projection_snapshot_valid_payload() -> None:
    payload = {
        "projection_id": "proj-1",
        "horizon_days": 10,
        "point_estimate": 0.12,
        "lower_bound": 0.05,
        "upper_bound": 0.2,
        "confidence": 0.8,
    }

    model = ProjectionSnapshot.model_validate(payload)
    assert model.horizon_days == 10


def test_projection_snapshot_reject_invalid_horizon() -> None:
    with pytest.raises(ValidationError):
        ProjectionSnapshot.model_validate(
            {
                "projection_id": "proj-1",
                "horizon_days": 0,
                "point_estimate": 0.12,
                "lower_bound": 0.05,
                "upper_bound": 0.2,
                "confidence": 0.8,
            }
        )


def test_projection_snapshot_reject_invalid_bounds() -> None:
    with pytest.raises(ValidationError):
        ProjectionSnapshot.model_validate(
            {
                "projection_id": "proj-1",
                "horizon_days": 5,
                "point_estimate": 0.12,
                "lower_bound": 0.25,
                "upper_bound": 0.2,
                "confidence": 0.8,
            }
        )
