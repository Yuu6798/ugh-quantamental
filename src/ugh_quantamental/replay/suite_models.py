"""Typed request, case-result, aggregate, and result models for the regression suite (v1)."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ugh_quantamental.query.models import ProjectionRunQuery, StateRunQuery
from ugh_quantamental.replay.batch_models import (
    ProjectionBatchReplayResult,
    StateBatchReplayResult,
)


class ProjectionSuiteCase(BaseModel):
    """A named projection batch replay case within a regression suite.

    Exactly one of ``run_ids`` or ``query`` must be provided.
    ``name`` must be non-empty.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    run_ids: tuple[str, ...] | None = None
    query: ProjectionRunQuery | None = None
    deduplicate_run_ids: bool = True

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("case name must be non-empty")
        return v

    @model_validator(mode="after")
    def _exactly_one_source(self) -> ProjectionSuiteCase:
        if (self.run_ids is None) == (self.query is None):
            raise ValueError("exactly one of run_ids or query must be provided")
        return self


class StateSuiteCase(BaseModel):
    """A named state batch replay case within a regression suite.

    Exactly one of ``run_ids`` or ``query`` must be provided.
    ``name`` must be non-empty.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    run_ids: tuple[str, ...] | None = None
    query: StateRunQuery | None = None
    deduplicate_run_ids: bool = True

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("case name must be non-empty")
        return v

    @model_validator(mode="after")
    def _exactly_one_source(self) -> StateSuiteCase:
        if (self.run_ids is None) == (self.query is None):
            raise ValueError("exactly one of run_ids or query must be provided")
        return self


class RegressionSuiteRequest(BaseModel):
    """Request to run a named regression suite over persisted projection and state runs.

    At least one case (projection or state) must be provided.
    Within each group, case names must be unique.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection_cases: tuple[ProjectionSuiteCase, ...] = ()
    state_cases: tuple[StateSuiteCase, ...] = ()

    @model_validator(mode="after")
    def _at_least_one_case(self) -> RegressionSuiteRequest:
        if not self.projection_cases and not self.state_cases:
            raise ValueError("at least one projection or state case must be provided")
        return self

    @model_validator(mode="after")
    def _unique_projection_names(self) -> RegressionSuiteRequest:
        names = [c.name for c in self.projection_cases]
        if len(names) != len(set(names)):
            raise ValueError("projection case names must be unique within the suite")
        return self

    @model_validator(mode="after")
    def _unique_state_names(self) -> RegressionSuiteRequest:
        names = [c.name for c in self.state_cases]
        if len(names) != len(set(names)):
            raise ValueError("state case names must be unique within the suite")
        return self


@dataclass(frozen=True)
class ProjectionSuiteCaseResult:
    """Outcome of running a single projection suite case."""

    name: str
    batch_result: ProjectionBatchReplayResult
    passed: bool


@dataclass(frozen=True)
class StateSuiteCaseResult:
    """Outcome of running a single state suite case."""

    name: str
    batch_result: StateBatchReplayResult
    passed: bool


class RegressionSuiteAggregate(BaseModel):
    """Suite-level aggregate summed across all projection and state cases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projection_case_count: int
    state_case_count: int
    total_case_count: int
    passed_case_count: int
    failed_case_count: int
    total_projection_requested: int
    total_state_requested: int
    total_missing_count: int
    total_error_count: int
    total_mismatch_count: int


@dataclass(frozen=True)
class RegressionSuiteResult:
    """Full outcome of a regression suite run."""

    projection_cases: tuple[ProjectionSuiteCaseResult, ...]
    state_cases: tuple[StateSuiteCaseResult, ...]
    aggregate: RegressionSuiteAggregate
