from pathlib import Path

from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind
from ugh_quantamental.review_autofix.rules import RuleRegistry


def _context(body: str, path: str, line: int = 1) -> ReviewContext:
    return ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=7,
        review_id=1,
        review_comment_id=2,
        head_sha="sha",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="reviewer",
        body=body,
        path=path,
        diff_hunk="@@",
        line=line,
        start_line=line,
        version_discriminator="2024-01-01T00:00:00Z:deadbeef",
    )


def test_none_rule_rewrites_range_hit_assignment(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "range_hit = None\n"


def test_none_rule_only_rewrites_reviewed_line(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5\nother = 1\nrange_hit = 0.7\ntext = 'range_hit = 0.9'\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target), line=3)

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "range_hit = 0.5\nother = 1\nrange_hit = None\ntext = 'range_hit = 0.9'\n"


def test_import_rule_is_selectable() -> None:
    context = _context("lint: sort imports", "src/file.py")
    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None
    assert rule.rule_id == "import-cleanup"
