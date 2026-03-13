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
        explicit_rule_id = re.search(r"\brule\s*:\s*none-normalization\b", text) is not None
        has_target_field = "range_hit" in text
        has_none_request = re.search(r"\b(none|null)\b", text) is not None
        has_normalize_phrase = re.search(r"\bnone[-\s]?normalization\b", text) is not None
        has_set_to_none_phrase = re.search(r"\bset\b.*\b(none|null)\b", text) is not None
        has_explicit_intent = explicit_rule_id or has_target_field or has_normalize_phrase or has_set_to_none_phrase

        if context.path is None:
            return None

        if not (has_none_request and has_explicit_intent):
            return None

        return RuleMatch(
            rule_id=self.rule_id,
            priority=extract_priority(context.body),
            target_file=context.path,
            summary="normalize invalid nullable value to None",
            validation_scope="project",
        )

    def _replace_range_hit_assignment(self, line: str) -> tuple[str, bool]:
        match = re.match(r"^(\s*range_hit\s*=\s*)([^;#\r\n]*?)(\s*)([;#].*)?(\r\n|\n|\r)?$", line)
        if match is None:
            return line, False
        prefix, _value, spacing, suffix, line_ending = match.groups()
        updated = f"{prefix}None{spacing}{suffix or ''}{line_ending or ''}"
        return updated, updated != line

    def _fallback_review_body_line(self, lines: list[str]) -> int | None:
        candidates = [idx for idx, line in enumerate(lines, start=1) if re.match(r"^\s*range_hit\s*=", line)]
        if len(candidates) == 1:
            return candidates[0]
        return None

    def apply(self, context: ReviewContext) -> RuleApplication:
        if context.path is None:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", None, "", ""), False, "no file")
        file_path = Path(context.path)
        try:
            with file_path.open(encoding="utf-8", newline="") as fh:
                before = fh.read()
        except FileNotFoundError:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "missing file")
        lines = before.splitlines(keepends=True)
        target_line = context.line or context.start_line
        if (
            context.kind.value == "diff_comment"
            and context.start_line is not None
            and context.line is not None
            and context.start_line < context.line
        ):
            for candidate in range(context.start_line, context.line + 1):
                if candidate <= 0 or candidate > len(lines):
                    continue
                if re.match(r"^\s*range_hit\s*=", lines[candidate - 1]):
                    target_line = candidate
                    break

        if target_line is None or target_line <= 0:
            if context.kind.value != "review_body":
                return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no reviewed line")
            fallback = self._fallback_review_body_line(lines)
            if fallback is None:
                return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no unique fallback")
            target_line = fallback
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
        has_import_phrase = re.search(r"\b(sort\s+imports?|import\s+order|unused\s+imports?)\b", text) is not None
        if context.path and (explicit_rule_id or has_import_keyword or has_import_phrase):
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
        with file_path.open(encoding="utf-8", newline="") as fh:
            before = fh.read()
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

        lines = before.splitlines(keepends=True)
        changed = False
        for line_no in sorted(import_lines):
            idx = line_no - 1
            if idx >= len(lines):
                continue
            line = lines[idx]
            line_body = line.rstrip("\r\n")
            if "  " not in line_body:
                continue
            leading = line_body[: len(line_body) - len(line_body.lstrip())]
            stripped = line_body.lstrip()
            if ";" in stripped:
                continue
            suffix = line[len(line_body) :]
            updated = leading + " ".join(stripped.split()) + suffix
            if updated != line:
                lines[idx] = updated
                changed = True

        if not changed:
            return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), False, "no-op")

        after = "".join(lines)
        file_path.write_text(after, encoding="utf-8", newline="")
        return RuleApplication(self.match(context) or RuleMatch(self.rule_id, "P2", context.path, "", ""), True, "applied")


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: tuple[BaseRule, ...] = (NoneNormalizationRule(), ImportCleanupRule())

    def match(self, context: ReviewContext) -> BaseRule | None:
        for rule in self._rules:
            if rule.match(context):
                return rule
        return None
