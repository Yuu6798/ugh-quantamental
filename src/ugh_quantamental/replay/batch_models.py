"""Typed request, item, aggregate, and result models for batch replay (v1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator

from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
from ugh_quantamental.replay.models import ProjectionReplayResult, StateReplayResult


class BatchReplayStatus(str, Enum):
    """Per-run outcome status for a batch replay item."""

    ok = "ok"
    missing = "missing"
    error = "error"


class ProjectionBatchReplayRequest(BaseModel):
    """Request to replay multiple persisted projection runs in a single call.

    Exactly one of ``run_ids`` or ``query`` must be provided.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_ids: tuple[str, ...] | None = None
    query: ProjectionRunQuery | None = None
    deduplicate_run_ids: bool = True

    @model_validator(mode="after")
    def _exactly_one_source(self) -> ProjectionBatchReplayRequest:
        has_run_ids = self.run_ids is not None
        has_query = self.query is not None
        if has_run_ids == has_query:
            raise ValueError("exactly one of run_ids or query must be provided")
        return self


class StateBatchReplayRequest(BaseModel):
    """Request to replay multiple persisted state runs in a single call.

    Exactly one of ``run_ids`` or ``query`` must be provided.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_ids: tuple[str, ...] | None = None
    query: StateRunQuery | None = None
    deduplicate_run_ids: bool = True

    @model_validator(mode="after")
    def _exactly_one_source(self) -> StateBatchReplayRequest:
        has_run_ids = self.run_ids is not None
        has_query = self.query is not None
        if has_run_ids == has_query:
            raise ValueError("exactly one of run_ids or query must be provided")
        return self


@dataclass(frozen=True)
class ProjectionBatchReplayItem:
    """Per-run outcome for a single projection run in a batch replay."""

    run_id: str
    status: BatchReplayStatus
    result: ProjectionReplayResult | None
    error_message: str | None


@dataclass(frozen=True)
class StateBatchReplayItem:
    """Per-run outcome for a single state run in a batch replay."""

    run_id: str
    status: BatchReplayStatus
    result: StateReplayResult | None
    error_message: str | None


class ProjectionBatchReplayAggregate(BaseModel):
    """Aggregate mismatch summary over all items in a projection batch replay."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requested_count: int
    processed_count: int
    exact_match_count: int
    mismatch_count: int
    missing_count: int
    error_count: int
    max_point_estimate_diff: float
    max_confidence_diff: float


class StateBatchReplayAggregate(BaseModel):
    """Aggregate mismatch summary over all items in a state batch replay."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    requested_count: int
    processed_count: int
    exact_match_count: int
    mismatch_count: int
    missing_count: int
    error_count: int
    max_transition_confidence_diff: float


@dataclass(frozen=True)
class ProjectionBatchReplayResult:
    """Full outcome of a projection batch replay, including per-run items and aggregate."""

    items: tuple[ProjectionBatchReplayItem, ...]
    aggregate: ProjectionBatchReplayAggregate


@dataclass(frozen=True)
class StateBatchReplayResult:
    """Full outcome of a state batch replay, including per-run items and aggregate."""

    items: tuple[StateBatchReplayItem, ...]
    aggregate: StateBatchReplayAggregate
