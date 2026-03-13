from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .classifier import extract_priority
from .models import ReviewContext, RuleMatch


@dataclass(frozen=True)
class RuleApplication:
    match: RuleMatch
    changed: bool
    details: str


class BaseRule:
    rule_id: str

    def match(self, context: ReviewContext) -> RuleMatch | None:
        raise NotImplementedError

    def apply(self, context: ReviewContext) -> RuleApplication:
        raise NotImplementedError


class NoneNormalizationRule(BaseRule):
    rule_id = "none-normalization"

    def match(self, context: ReviewContext) -> RuleMatch | None:
        text = context.body.lower()
        if ("none" in text or "null" in text) and context.path:
            return RuleMatch(
                rule_id=self.rule_id,
                priority=extract_priority(context.body),
                target_file=context.path,
                summary="normalize invalid nullable value to None",
                validation_scope="project",
            )
        return None

    def apply(self, context: ReviewContext) -> RuleApplication:
        if context.path is None:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", None, "", ""), False, "no file")
        file_path = Path(context.path)
        before = file_path.read_text(encoding="utf-8")
        after = re.sub(r"(range_hit\s*=\s*)([^\n#]+)", r"\1None", before)
        changed = before != after
        if changed:
            file_path.write_text(after, encoding="utf-8")
        return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), changed, "applied" if changed else "no-op")


class ImportCleanupRule(BaseRule):
    rule_id = "import-cleanup"

    def match(self, context: ReviewContext) -> RuleMatch | None:
        text = context.body.lower()
        if context.path and ("import" in text or "ruff" in text or "unused" in text or "整理" in text):
            return RuleMatch(
                rule_id=self.rule_id,
                priority=extract_priority(context.body),
                target_file=context.path,
                summary="apply minimal import cleanup",
                validation_scope=context.path,
            )
        return None

    def apply(self, context: ReviewContext) -> RuleApplication:
        if context.path is None:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", None, "", ""), False, "no file")
        file_path = Path(context.path)
        before = file_path.read_text(encoding="utf-8")
        lines = [line for line in before.splitlines()]
        cleaned: list[str] = []
        for line in lines:
            if line.strip().startswith("import ") and "  " in line:
                cleaned.append(" ".join(line.split()))
            else:
                cleaned.append(line)
        after = "\n".join(cleaned) + ("\n" if before.endswith("\n") else "")
        changed = before != after
        if changed:
            file_path.write_text(after, encoding="utf-8")
        return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), changed, "applied" if changed else "no-op")


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: tuple[BaseRule, ...] = (NoneNormalizationRule(), ImportCleanupRule())

    def match(self, context: ReviewContext) -> BaseRule | None:
        for rule in self._rules:
            if rule.match(context):
                return rule
        return None
