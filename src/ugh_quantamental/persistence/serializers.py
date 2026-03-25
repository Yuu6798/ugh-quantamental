"""Pure serializer helpers bridging ORM JSON payloads and Pydantic contracts."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.review_audit_models import (
    FixActionFeatures,
    ReviewAuditEngineResult,
    ReviewIntentFeatures,
    ReviewObservation,
)
from ugh_quantamental.engine.state_models import (
    StateConfig,
    StateEngineResult,
    StateEventFeatures,
)
from ugh_quantamental.engine.review_audit_models import ReviewContext, ReviewKind
from ugh_quantamental.schemas.omega import Omega
from ugh_quantamental.schemas.ssv import SSVSnapshot

ModelT = TypeVar("ModelT", bound=BaseModel)


def dump_model_json(model: BaseModel) -> dict[str, Any]:
    """Dump a Pydantic model into JSON-safe Python primitives."""
    return model.model_dump(mode="json")


def load_model_json(model_type: type[ModelT], payload: dict[str, Any]) -> ModelT:
    """Validate JSON payload into a strongly-typed Pydantic model."""
    return model_type.model_validate(payload)


def projection_payload_to_models(payload: dict[str, Any]) -> tuple[
    QuestionFeatures,
    SignalFeatures,
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
]:
    """Rehydrate projection run JSON payload sections into typed models."""
    return (
        load_model_json(QuestionFeatures, payload["question_features_json"]),
        load_model_json(SignalFeatures, payload["signal_features_json"]),
        load_model_json(AlignmentInputs, payload["alignment_inputs_json"]),
        load_model_json(ProjectionConfig, payload["config_json"]),
        load_model_json(ProjectionEngineResult, payload["result_json"]),
    )


def state_payload_to_models(payload: dict[str, Any]) -> tuple[
    SSVSnapshot,
    Omega,
    ProjectionEngineResult,
    StateEventFeatures,
    StateConfig,
    StateEngineResult,
]:
    """Rehydrate state run JSON payload sections into typed models."""
    return (
        load_model_json(SSVSnapshot, payload["snapshot_json"]),
        load_model_json(Omega, payload["omega_json"]),
        load_model_json(ProjectionEngineResult, payload["projection_result_json"]),
        load_model_json(StateEventFeatures, payload["event_features_json"]),
        load_model_json(StateConfig, payload["config_json"]),
        load_model_json(StateEngineResult, payload["result_json"]),
    )


# ---------------------------------------------------------------------------
# ReviewContext serialization (frozen dataclass — cannot use dump_model_json)
# ---------------------------------------------------------------------------


def dump_review_context_json(context: ReviewContext) -> dict[str, Any]:
    """Serialize a ``ReviewContext`` frozen dataclass into a JSON-safe dict.

    ``ReviewKind`` enum values are serialized as their string ``.value`` so
    that the payload round-trips cleanly through the ORM JSON column.
    """
    return {
        "kind": context.kind.value,
        "repository": context.repository,
        "pr_number": context.pr_number,
        "review_id": context.review_id,
        "review_comment_id": context.review_comment_id,
        "head_sha": context.head_sha,
        "base_ref": context.base_ref,
        "head_ref": context.head_ref,
        "same_repo": context.same_repo,
        "reviewer_login": context.reviewer_login,
        "body": context.body,
        "path": context.path,
        "diff_hunk": context.diff_hunk,
        "line": context.line,
        "start_line": context.start_line,
        "version_discriminator": context.version_discriminator,
        "review_comment_node_id": context.review_comment_node_id,
        "review_body_path_hint_present": context.review_body_path_hint_present,
    }


def load_review_context_json(payload: dict[str, Any]) -> ReviewContext:
    """Deserialize a JSON dict into a frozen ``ReviewContext`` dataclass.

    ``kind`` is re-constructed from its string value via ``ReviewKind``.
    """
    return ReviewContext(
        kind=ReviewKind(payload["kind"]),
        repository=payload["repository"],
        pr_number=payload["pr_number"],
        review_id=payload["review_id"],
        review_comment_id=payload["review_comment_id"],
        head_sha=payload["head_sha"],
        base_ref=payload["base_ref"],
        head_ref=payload["head_ref"],
        same_repo=payload["same_repo"],
        reviewer_login=payload["reviewer_login"],
        body=payload["body"],
        path=payload["path"],
        diff_hunk=payload["diff_hunk"],
        line=payload["line"],
        start_line=payload["start_line"],
        version_discriminator=payload["version_discriminator"],
        review_comment_node_id=payload.get("review_comment_node_id"),
        review_body_path_hint_present=payload.get("review_body_path_hint_present", False),
    )


def review_audit_payload_to_models(payload: dict[str, Any]) -> tuple[
    ReviewContext,
    ReviewObservation,
    ReviewIntentFeatures,
    FixActionFeatures | None,
    ReviewAuditEngineResult,
]:
    """Rehydrate review audit run JSON payload sections into typed models.

    ``action_features_json`` may be ``None`` (detect_only / propose_only modes).
    """
    action_features: FixActionFeatures | None = None
    if payload.get("action_features_json") is not None:
        action_features = load_model_json(FixActionFeatures, payload["action_features_json"])
    return (
        load_review_context_json(payload["review_context_json"]),
        load_model_json(ReviewObservation, payload["observation_json"]),
        load_model_json(ReviewIntentFeatures, payload["intent_features_json"]),
        action_features,
        load_model_json(ReviewAuditEngineResult, payload["engine_result_json"]),
    )
