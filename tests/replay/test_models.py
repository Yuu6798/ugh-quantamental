"""Tests for replay layer model validation."""

from __future__ import annotations

import pytest

from ugh_quantamental.replay.models import (
    ProjectionReplayComparison,
    ProjectionReplayRequest,
    StateReplayComparison,
    StateReplayRequest,
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


def test_projection_replay_request_valid() -> None:
    req = ProjectionReplayRequest(run_id="proj-abc123")
    assert req.run_id == "proj-abc123"


def test_state_replay_request_valid() -> None:
    req = StateReplayRequest(run_id="state-xyz456")
    assert req.run_id == "state-xyz456"


def test_projection_replay_request_rejects_extra_fields() -> None:
    with pytest.raises(Exception):
        ProjectionReplayRequest(run_id="x", unexpected_field="y")  # type: ignore[call-arg]


def test_state_replay_request_rejects_extra_fields() -> None:
    with pytest.raises(Exception):
        StateReplayRequest(run_id="x", unexpected_field="y")  # type: ignore[call-arg]


def test_projection_replay_request_is_frozen() -> None:
    req = ProjectionReplayRequest(run_id="x")
    with pytest.raises(Exception):
        req.run_id = "y"  # type: ignore[misc]


def test_state_replay_request_is_frozen() -> None:
    req = StateReplayRequest(run_id="x")
    with pytest.raises(Exception):
        req.run_id = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Comparison models
# ---------------------------------------------------------------------------


def test_projection_replay_comparison_exact_match_shape() -> None:
    cmp = ProjectionReplayComparison(
        exact_match=True,
        projection_snapshot_match=True,
        point_estimate_diff=0.0,
        confidence_diff=0.0,
        mismatch_px_diff=0.0,
        mismatch_sem_diff=0.0,
        conviction_diff=0.0,
        urgency_diff=0.0,
    )
    assert cmp.exact_match is True
    assert cmp.projection_snapshot_match is True
    assert cmp.point_estimate_diff == 0.0


def test_projection_replay_comparison_mismatch_shape() -> None:
    cmp = ProjectionReplayComparison(
        exact_match=False,
        projection_snapshot_match=False,
        point_estimate_diff=0.05,
        confidence_diff=0.02,
        mismatch_px_diff=0.03,
        mismatch_sem_diff=0.01,
        conviction_diff=0.04,
        urgency_diff=0.02,
    )
    assert cmp.exact_match is False
    assert cmp.point_estimate_diff == pytest.approx(0.05)


def test_projection_replay_comparison_rejects_extra_fields() -> None:
    with pytest.raises(Exception):
        ProjectionReplayComparison(  # type: ignore[call-arg]
            exact_match=True,
            projection_snapshot_match=True,
            point_estimate_diff=0.0,
            confidence_diff=0.0,
            mismatch_px_diff=0.0,
            mismatch_sem_diff=0.0,
            conviction_diff=0.0,
            urgency_diff=0.0,
            unknown_field=99,
        )


def test_state_replay_comparison_exact_match_shape() -> None:
    cmp = StateReplayComparison(
        exact_match=True,
        dominant_state_match=True,
        transition_confidence_diff=0.0,
        market_svp_match=True,
        updated_probabilities_match=True,
    )
    assert cmp.exact_match is True
    assert cmp.dominant_state_match is True
    assert cmp.transition_confidence_diff == 0.0


def test_state_replay_comparison_mismatch_shape() -> None:
    cmp = StateReplayComparison(
        exact_match=False,
        dominant_state_match=False,
        transition_confidence_diff=0.12,
        market_svp_match=False,
        updated_probabilities_match=False,
    )
    assert cmp.exact_match is False
    assert cmp.transition_confidence_diff == pytest.approx(0.12)


def test_state_replay_comparison_rejects_extra_fields() -> None:
    with pytest.raises(Exception):
        StateReplayComparison(  # type: ignore[call-arg]
            exact_match=True,
            dominant_state_match=True,
            transition_confidence_diff=0.0,
            market_svp_match=True,
            updated_probabilities_match=True,
            extra="bad",
        )
