from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Classification(str, Enum):
    auto_fixable = "auto_fixable"
    propose_only = "propose_only"
    skip = "skip"


class ReviewKind(str, Enum):
    diff_comment = "diff_comment"
    review_body = "review_body"


@dataclass(frozen=True)
class ReviewContext:
    kind: ReviewKind
    repository: str
    pr_number: int
    review_id: int | None
    review_comment_id: int | None
    head_sha: str
    base_ref: str
    head_ref: str
    same_repo: bool
    reviewer_login: str | None
    body: str
    path: str | None
    diff_hunk: str | None
    version_discriminator: str


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    priority: str
    target_file: str | None
    summary: str
    validation_scope: str


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    command_results: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ProcessResult:
    processed_key: str
    classification: Classification
    matched_rule: str | None
    changed: bool
    validation_ok: bool
    pushed: bool
    reply_sent: bool
    reason: str
