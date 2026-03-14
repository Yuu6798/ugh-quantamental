from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class CodexFixTask:
    task_id: str
    prompt: str
    repository: str
    pr_number: int
    head_ref: str
    base_ref: str
    head_sha: str


class CodexExecutionStatus(str, Enum):
    succeeded = "succeeded"
    no_op = "no_op"
    failed = "failed"
    timeout = "timeout"
    malformed = "malformed"


@dataclass(frozen=True)
class CodexTaskHandle:
    task_id: str


@dataclass(frozen=True)
class CodexExecutionResult:
    status: CodexExecutionStatus
    changed: bool
    summary: str


@dataclass(frozen=True)
class CodexApplyResult:
    changed: bool
    branch_updated: bool
    summary: str
