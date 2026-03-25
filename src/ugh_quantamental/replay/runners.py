"""Synchronous deterministic replay runners for persisted projection, state, and review audit runs.

These runners are read-only and diagnostic only.  They do not write run records,
flush, or commit the session.  The caller owns the session and transaction boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ugh_quantamental.engine.projection import run_projection_engine
from ugh_quantamental.engine.review_audit import run_review_audit_engine
from ugh_quantamental.engine.state import run_state_engine
from ugh_quantamental.query.readers import (
    get_projection_run_bundle,
    get_review_audit_run_bundle,
    get_state_run_bundle,
)
from ugh_quantamental.replay.models import (
    ProjectionReplayComparison,
    ProjectionReplayRequest,
    ProjectionReplayResult,
    ReviewAuditExtractorReplayComparison,
    ReviewAuditExtractorReplayRequest,
    ReviewAuditExtractorReplayResult,
    ReviewAuditReplayComparison,
    ReviewAuditReplayRequest,
    ReviewAuditReplayResult,
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


def _compare_review_audit(
    stored_result,
    recomputed_result,
) -> ReviewAuditReplayComparison:
    """Build a ReviewAuditReplayComparison from stored and recomputed engine results."""
    stored_json = stored_result.model_dump(mode="json")
    recomputed_json = recomputed_result.model_dump(mode="json")

    stored_snap = stored_result.audit_snapshot
    recomputed_snap = recomputed_result.audit_snapshot

    stored_de = stored_snap.delta_e
    recomputed_de = recomputed_snap.delta_e
    if stored_de is None and recomputed_de is None:
        delta_e_diff = None
    else:
        delta_e_diff = abs((recomputed_de or 0.0) - (stored_de or 0.0))

    stored_ms = stored_snap.mismatch_score
    recomputed_ms = recomputed_snap.mismatch_score
    if stored_ms is None and recomputed_ms is None:
        mismatch_score_diff = None
    else:
        mismatch_score_diff = abs((recomputed_ms or 0.0) - (stored_ms or 0.0))

    return ReviewAuditReplayComparison(
        exact_match=stored_json == recomputed_json,
        snapshot_match=stored_json["audit_snapshot"] == recomputed_json["audit_snapshot"],
        por_diff=abs(recomputed_snap.por - stored_snap.por),
        delta_e_diff=delta_e_diff,
        mismatch_score_diff=mismatch_score_diff,
        verdict_match=stored_snap.verdict == recomputed_snap.verdict,
    )


def replay_review_audit_run(
    session: Session,
    request: ReviewAuditReplayRequest,
) -> ReviewAuditReplayResult | None:
    """Replay a persisted review audit run (engine replay) and compare stored vs recomputed.

    Loads the bundle via the read-only query layer, reruns the deterministic engine
    with the recovered intent/action features and config, and returns a structured comparison.

    Returns ``None`` if the run_id is not found.
    Does not write, flush, or commit the session.
    """
    bundle = get_review_audit_run_bundle(session, request.run_id)
    if bundle is None:
        return None

    recomputed = run_review_audit_engine(
        audit_id=bundle.audit_id,
        intent=bundle.intent_features,
        action=bundle.action_features,
        config=bundle.result.config,
    )

    comparison = _compare_review_audit(bundle.result, recomputed)

    return ReviewAuditReplayResult(
        bundle=bundle,
        recomputed_result=recomputed,
        comparison=comparison,
    )


def _compare_review_audit_extractor(
    stored_observation,
    recomputed_observation,
    stored_features,
    recomputed_features,
) -> ReviewAuditExtractorReplayComparison:
    """Build a ReviewAuditExtractorReplayComparison from stored and re-extracted models."""
    stored_obs_json = stored_observation.model_dump(mode="json")
    recomputed_obs_json = recomputed_observation.model_dump(mode="json")
    stored_feat_json = stored_features.model_dump(mode="json")
    recomputed_feat_json = recomputed_features.model_dump(mode="json")

    observation_match = stored_obs_json == recomputed_obs_json
    intent_features_match = stored_feat_json == recomputed_feat_json

    return ReviewAuditExtractorReplayComparison(
        exact_match=observation_match and intent_features_match,
        observation_match=observation_match,
        intent_features_match=intent_features_match,
        # ReviewIntentFeatures numeric diffs
        intent_clarity_diff=abs(
            recomputed_features.intent_clarity - stored_features.intent_clarity
        ),
        locality_strength_diff=abs(
            recomputed_features.locality_strength - stored_features.locality_strength
        ),
        mechanicalness_diff=abs(
            recomputed_features.mechanicalness - stored_features.mechanicalness
        ),
        scope_boundness_diff=abs(
            recomputed_features.scope_boundness - stored_features.scope_boundness
        ),
        semantic_change_risk_diff=abs(
            recomputed_features.semantic_change_risk - stored_features.semantic_change_risk
        ),
        validation_intensity_diff=abs(
            recomputed_features.validation_intensity - stored_features.validation_intensity
        ),
        # ReviewObservation numeric count diffs
        mechanical_keyword_hits_diff=abs(
            recomputed_observation.mechanical_keyword_hits
            - stored_observation.mechanical_keyword_hits
        ),
        skip_keyword_hits_diff=abs(
            recomputed_observation.skip_keyword_hits - stored_observation.skip_keyword_hits
        ),
        ambiguity_signal_count_diff=abs(
            recomputed_observation.ambiguity_signal_count
            - stored_observation.ambiguity_signal_count
        ),
        # ReviewObservation non-numeric field matches
        has_path_hint_match=(
            recomputed_observation.has_path_hint == stored_observation.has_path_hint
        ),
        has_line_anchor_match=(
            recomputed_observation.has_line_anchor == stored_observation.has_line_anchor
        ),
        has_diff_hunk_match=(
            recomputed_observation.has_diff_hunk == stored_observation.has_diff_hunk
        ),
        priority_match=(recomputed_observation.priority == stored_observation.priority),
        behavior_preservation_signal_match=(
            recomputed_observation.behavior_preservation_signal
            == stored_observation.behavior_preservation_signal
        ),
        scope_limit_signal_match=(
            recomputed_observation.scope_limit_signal == stored_observation.scope_limit_signal
        ),
        target_file_present_match=(
            recomputed_observation.target_file_present == stored_observation.target_file_present
        ),
        review_kind_match=(
            recomputed_observation.review_kind == stored_observation.review_kind
        ),
    )


def replay_review_audit_extractor_run(
    session: Session,
    request: ReviewAuditExtractorReplayRequest,
) -> ReviewAuditExtractorReplayResult | None:
    """Replay feature extraction for a persisted review audit run and compare results.

    Loads the bundle via the read-only query layer, re-runs the three-layer extractor
    pipeline (``extract_review_observation`` → ``extract_review_intent_features``) on
    the stored ``ReviewContext``, and returns a structured comparison.

    Returns ``None`` if the run_id is not found.
    Does not write, flush, or commit the session.
    """
    from ugh_quantamental.engine.review_audit_extractor import (
        extract_review_intent_features,
        extract_review_observation,
    )

    bundle = get_review_audit_run_bundle(session, request.run_id)
    if bundle is None:
        return None

    recomputed_observation = extract_review_observation(bundle.review_context)
    recomputed_features = extract_review_intent_features(recomputed_observation)

    comparison = _compare_review_audit_extractor(
        bundle.observation,
        recomputed_observation,
        bundle.intent_features,
        recomputed_features,
    )

    return ReviewAuditExtractorReplayResult(
        bundle=bundle,
        recomputed_observation=recomputed_observation,
        recomputed_intent_features=recomputed_features,
        comparison=comparison,
    )
