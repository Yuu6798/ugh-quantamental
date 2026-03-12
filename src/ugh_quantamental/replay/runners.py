"""Synchronous deterministic replay runners for persisted projection and state runs (v1).

These runners are read-only and diagnostic only.  They do not write run records,
flush, or commit the session.  The caller owns the session and transaction boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ugh_quantamental.engine.projection import run_projection_engine
from ugh_quantamental.engine.state import run_state_engine
from ugh_quantamental.query.readers import get_projection_run_bundle, get_state_run_bundle
from ugh_quantamental.replay.models import (
    ProjectionReplayComparison,
    ProjectionReplayRequest,
    ProjectionReplayResult,
    StateReplayComparison,
    StateReplayRequest,
    StateReplayResult,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _compare_projection(
    stored_result,
    recomputed_result,
) -> ProjectionReplayComparison:
    """Build a ProjectionReplayComparison from stored and recomputed engine results."""
    stored_json = stored_result.model_dump(mode="json")
    recomputed_json = recomputed_result.model_dump(mode="json")

    return ProjectionReplayComparison(
        exact_match=stored_json == recomputed_json,
        projection_snapshot_match=(
            stored_json["projection_snapshot"] == recomputed_json["projection_snapshot"]
        ),
        point_estimate_diff=abs(
            recomputed_result.projection_snapshot.point_estimate
            - stored_result.projection_snapshot.point_estimate
        ),
        confidence_diff=abs(
            recomputed_result.projection_snapshot.confidence
            - stored_result.projection_snapshot.confidence
        ),
        mismatch_px_diff=abs(recomputed_result.mismatch_px - stored_result.mismatch_px),
        mismatch_sem_diff=abs(recomputed_result.mismatch_sem - stored_result.mismatch_sem),
        conviction_diff=abs(recomputed_result.conviction - stored_result.conviction),
        urgency_diff=abs(recomputed_result.urgency - stored_result.urgency),
    )


def _compare_state(
    stored_result,
    recomputed_result,
) -> StateReplayComparison:
    """Build a StateReplayComparison from stored and recomputed engine results."""
    stored_json = stored_result.model_dump(mode="json")
    recomputed_json = recomputed_result.model_dump(mode="json")

    return StateReplayComparison(
        exact_match=stored_json == recomputed_json,
        dominant_state_match=recomputed_result.dominant_state == stored_result.dominant_state,
        transition_confidence_diff=abs(
            recomputed_result.transition_confidence - stored_result.transition_confidence
        ),
        market_svp_match=(
            stored_json["updated_market_svp"] == recomputed_json["updated_market_svp"]
        ),
        updated_probabilities_match=(
            stored_json["updated_probabilities"] == recomputed_json["updated_probabilities"]
        ),
    )


def replay_projection_run(
    session: Session,
    request: ProjectionReplayRequest,
) -> ProjectionReplayResult | None:
    """Replay a persisted projection run and compare stored vs recomputed result.

    Loads the bundle via the read-only query layer, reruns the deterministic engine
    with the recovered inputs, and returns a structured comparison.

    Returns ``None`` if the run_id is not found.
    Does not write, flush, or commit the session.
    """
    bundle = get_projection_run_bundle(session, request.run_id)
    if bundle is None:
        return None

    recomputed = run_projection_engine(
        projection_id=bundle.projection_id,
        horizon_days=bundle.result.projection_snapshot.horizon_days,
        question_features=bundle.question_features,
        signal_features=bundle.signal_features,
        alignment_inputs=bundle.alignment_inputs,
        config=bundle.config,
    )

    comparison = _compare_projection(bundle.result, recomputed)

    return ProjectionReplayResult(
        bundle=bundle,
        recomputed_result=recomputed,
        comparison=comparison,
    )


def replay_state_run(
    session: Session,
    request: StateReplayRequest,
) -> StateReplayResult | None:
    """Replay a persisted state run and compare stored vs recomputed result.

    Loads the bundle via the read-only query layer, reruns the deterministic engine
    with the recovered inputs, and returns a structured comparison.

    Returns ``None`` if the run_id is not found.
    Does not write, flush, or commit the session.
    """
    bundle = get_state_run_bundle(session, request.run_id)
    if bundle is None:
        return None

    recomputed = run_state_engine(
        snapshot=bundle.snapshot,
        omega=bundle.omega,
        projection_result=bundle.projection_result,
        event_features=bundle.event_features,
        config=bundle.config,
    )

    comparison = _compare_state(bundle.result, recomputed)

    return StateReplayResult(
        bundle=bundle,
        recomputed_result=recomputed,
        comparison=comparison,
    )
