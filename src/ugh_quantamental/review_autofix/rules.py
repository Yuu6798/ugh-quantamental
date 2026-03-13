from __future__ import annotations

import ast
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

    def _replace_range_hit_assignment(self, line: str) -> tuple[str, bool]:
        updated = re.sub(r"^(\s*range_hit\s*=\s*)([^#\n]+)", r"\1None", line)
        return updated, updated != line

    def apply(self, context: ReviewContext) -> RuleApplication:
        if context.path is None:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", None, "", ""), False, "no file")
        target_line = context.line or context.start_line
        if target_line is None or target_line <= 0:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no reviewed line")

        file_path = Path(context.path)
        before = file_path.read_text(encoding="utf-8")
        lines = before.splitlines(keepends=True)
        if target_line > len(lines):
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "reviewed line out of range")

        updated_line, changed = self._replace_range_hit_assignment(lines[target_line - 1])
        if not changed:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no-op")

        lines[target_line - 1] = updated_line
        file_path.write_text("".join(lines), encoding="utf-8")
        return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), True, "applied")


class ImportCleanupRule(BaseRule):
    rule_id = "import-cleanup"

    def match(self, context: ReviewContext) -> RuleMatch | None:
        text = context.body.lower()
        explicit_rule_id = re.search(r"\brule\s*:\s*import-cleanup\b", text) is not None
        keyword_text = text.replace("import-cleanup", " ")
        has_import_keyword = re.search(r"\bimports?\b", keyword_text) is not None
        has_lint_keyword = any(token in text for token in ("ruff", "unused", "整理"))
        if context.path and (explicit_rule_id or has_import_keyword or has_lint_keyword):
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
        try:
            tree = ast.parse(before)
        except SyntaxError:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "syntax-error")

        import_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and getattr(node, "lineno", None) is not None:
                if getattr(node, "end_lineno", node.lineno) == node.lineno:
                    import_lines.add(node.lineno)

        if not import_lines:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no-op")

        lines = before.splitlines()
        changed = False
        for line_no in sorted(import_lines):
            idx = line_no - 1
            if idx >= len(lines):
                continue
            line = lines[idx]
            if "  " not in line:
                continue
            leading = line[: len(line) - len(line.lstrip())]
            stripped = line.lstrip()
            updated = leading + " ".join(stripped.split())
            if updated != line:
                lines[idx] = updated
                changed = True

        if not changed:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no-op")

        after = "\n".join(lines) + ("\n" if before.endswith("\n") else "")
        file_path.write_text(after, encoding="utf-8")
        return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), True, "applied")


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: tuple[BaseRule, ...] = (NoneNormalizationRule(), ImportCleanupRule())

    def match(self, context: ReviewContext) -> BaseRule | None:
        for rule in self._rules:
            if rule.match(context):
                return rule
        return None
