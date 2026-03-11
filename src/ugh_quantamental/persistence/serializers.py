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
from ugh_quantamental.engine.state_models import (
    StateConfig,
    StateEngineResult,
    StateEventFeatures,
)
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
