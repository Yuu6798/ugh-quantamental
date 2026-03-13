from pathlib import Path

from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind
from ugh_quantamental.review_autofix.rules import RuleRegistry


def _context(body: str, path: str) -> ReviewContext:
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


def test_import_rule_is_selectable() -> None:
    context = _context("lint: sort imports", "src/file.py")
    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None
    assert rule.rule_id == "import-cleanup"
