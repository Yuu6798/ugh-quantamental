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
