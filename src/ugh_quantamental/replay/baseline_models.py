"""Typed request, result, and comparison models for regression suite baselines (v1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ugh_quantamental.replay.suite_models import RegressionSuiteRequest


class CreateRegressionBaselineRequest(BaseModel):
    """Request to create and persist a named regression suite baseline.

    ``baseline_name`` must be non-empty and unique across persisted baselines.
    Exactly the suite defined by ``suite_request`` will be run and stored.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_name: str
    suite_request: RegressionSuiteRequest
    description: str | None = None
    baseline_id: str | None = None
    created_at: datetime | None = None

    @field_validator("baseline_name")
    @classmethod
    def _name_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("baseline_name must be non-empty")
        return v


class CompareRegressionBaselineRequest(BaseModel):
    """Request to compare a stored baseline against a fresh suite rerun.

    Exactly one of ``baseline_id`` or ``baseline_name`` must be provided.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_id: str | None = None
    baseline_name: str | None = None

    @model_validator(mode="after")
    def _exactly_one_identifier(self) -> CompareRegressionBaselineRequest:
        if (self.baseline_id is None) == (self.baseline_name is None):
            raise ValueError("exactly one of baseline_id or baseline_name must be provided")
        return self


@dataclass(frozen=True)
class RegressionSuiteBaseline:
    """Rehydrated baseline record with typed suite request and serialized result."""

    baseline_id: str
    baseline_name: str
    created_at: datetime
    description: str | None
    suite_request: RegressionSuiteRequest
    suite_result_json: dict


@dataclass(frozen=True)
class RegressionSuiteBaselineBundle:
    """Outcome of creating or loading a baseline; pairs the typed baseline with its raw record."""

    baseline: RegressionSuiteBaseline
    persisted_run_id: str


@dataclass(frozen=True)
class RegressionSuiteCaseDelta:
    """Per-case comparison between baseline and current suite result."""

    name: str
    exists_in_baseline: bool
    exists_in_current: bool
    passed_match: bool | None


@dataclass(frozen=True)
class RegressionBaselineComparison:
    """Field-by-field comparison of stored vs current regression suite aggregate."""

    exact_match: bool
    case_count_match: bool
    passed_case_count_diff: int
    failed_case_count_diff: int
    total_missing_count_diff: int
    total_error_count_diff: int
    total_mismatch_count_diff: int
    case_deltas: tuple[RegressionSuiteCaseDelta, ...]


@dataclass(frozen=True)
class RegressionBaselineCompareResult:
    """Full outcome of comparing a stored baseline against a fresh suite rerun."""

    baseline: RegressionSuiteBaseline
    current_result_json: dict
    comparison: RegressionBaselineComparison
