from __future__ import annotations

import re

from .models import Classification, ReviewContext

_PRIORITY_RE = re.compile(r"\bP([0-3])\b", re.IGNORECASE)
_AUTO_KEYWORDS = (
    "lint",
    "ruff",
    "import",
    "unused",
    "none",
    "null",
    "utc",
    "validator",
    "normalizer",
    "型",
    "整理",
    "未使用",
)
_SKIP_KEYWORDS = ("design", "refactor", "大規模", "アーキ", "仕様変更")


def extract_priority(text: str) -> str:
    match = _PRIORITY_RE.search(text)
    if not match:
        return "P2"
    return f"P{match.group(1)}"


def classify_review(context: ReviewContext) -> Classification:
    body = context.body.lower()
    if any(word in body for word in _SKIP_KEYWORDS):
        return Classification.skip
    if context.path is None and context.kind.value == "review_body":
        if "file:" not in body and "path:" not in body:
            return Classification.skip
    if any(word in body for word in _AUTO_KEYWORDS):
        return Classification.auto_fixable
    if any(token in body for token in ("should", "提案", "consider")):
        return Classification.propose_only
    return Classification.skip


def classify_codex_review(context: ReviewContext) -> Classification:
    """Classify a review that has already been verified to come from a trusted Codex actor.

    Unlike ``classify_review``, this function does NOT require the review body to match
    auto-fix keyword patterns.  The Codex bot only comments on things it can fix, so the
    default disposition is ``auto_fixable``.  We only skip for:

    * Explicit skip keywords (large-scale design / refactor directives).
    * ``review_body`` events without any file-location hint (ambiguous target — fail-closed).
    """
    body = context.body.lower()
    if any(word in body for word in _SKIP_KEYWORDS):
        return Classification.skip
    if context.kind.value == "review_body" and context.path is None:
        # Use the already-parsed and sanitized path from ReviewContext rather than
        # raw substring matching on the body.  Substring checks ("file:" in body)
        # produce false positives — e.g. "update profile: …" contains "file:" as a
        # substring but has no concrete file target.  build_review_context() already
        # performs a line-start check ("file:" / "path:" at the start of a line) and
        # path sanitization; context.path is None means no valid target was found.
        return Classification.skip
    return Classification.auto_fixable
