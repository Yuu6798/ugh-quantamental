from ugh_quantamental.review_autofix.classifier import classify_review, extract_priority
from ugh_quantamental.review_autofix.models import Classification, ReviewContext, ReviewKind


def _context(body: str, path: str | None = "src/a.py") -> ReviewContext:
    return ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=1,
        review_id=1,
        review_comment_id=2,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="alice",
        body=body,
        path=path,
        diff_hunk="@@",
    )


def test_extract_priority_defaults_to_p2() -> None:
    assert extract_priority("please fix") == "P2"


def test_extract_priority_detects_explicit_marker() -> None:
    assert extract_priority("P1: lint issue") == "P1"


def test_classify_auto_fixable_for_lint_comment() -> None:
    assert classify_review(_context("P1 lint: sort imports")) == Classification.auto_fixable


def test_classify_skip_for_abstract_design_feedback() -> None:
    assert classify_review(_context("major design refactor is needed")) == Classification.skip


def test_classify_review_body_without_location_is_skip() -> None:
    context = _context("validator should be added", path=None)
    context = ReviewContext(**{**context.__dict__, "kind": ReviewKind.review_body})
    assert classify_review(context) == Classification.skip
