from ugh_quantamental.review_autofix.classifier import classify_codex_review, classify_review, extract_priority
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
        line=1,
        start_line=1,
        version_discriminator="2024-01-01T00:00:00Z:deadbeef",
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


# --- classify_codex_review tests ---


def _codex_context(body: str, path: str | None = "src/a.py", kind: ReviewKind = ReviewKind.diff_comment) -> ReviewContext:
    return ReviewContext(
        kind=kind,
        repository="acme/repo",
        pr_number=1,
        review_id=1,
        review_comment_id=2 if kind == ReviewKind.diff_comment else None,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="chatgpt-codex-connector[bot]",
        body=body,
        path=path,
        diff_hunk="@@" if kind == ReviewKind.diff_comment else None,
        line=1 if kind == ReviewKind.diff_comment else None,
        start_line=1 if kind == ReviewKind.diff_comment else None,
        version_discriminator="2024-01-01T00:00:00Z:deadbeef",
    )


def test_codex_classify_arbitrary_comment_is_auto_fixable() -> None:
    """Any diff comment from Codex defaults to auto_fixable without needing keywords."""
    assert classify_codex_review(_codex_context("Please add a type annotation here.")) == Classification.auto_fixable


def test_codex_classify_skip_keywords_remain_skip() -> None:
    assert classify_codex_review(_codex_context("major design refactor needed")) == Classification.skip


def test_codex_classify_review_body_with_file_hint_is_auto_fixable() -> None:
    ctx = _codex_context("file: src/a.py\nPlease rename this variable.", path="src/a.py", kind=ReviewKind.review_body)
    assert classify_codex_review(ctx) == Classification.auto_fixable


def test_codex_classify_review_body_without_hint_is_skip() -> None:
    ctx = _codex_context("General architecture concern.", path=None, kind=ReviewKind.review_body)
    assert classify_codex_review(ctx) == Classification.skip


def test_codex_classify_no_keyword_comment_is_auto_fixable() -> None:
    """Codex comment not matching any legacy keyword must still be auto_fixable."""
    assert classify_codex_review(_codex_context("Rename this to snake_case.")) == Classification.auto_fixable


def test_codex_classify_review_body_false_positive_substring_is_skip() -> None:
    """'profile:' contains 'file:' as a substring; must not be treated as a valid path hint.

    Since context.path is None (build_review_context found no line-start file hint),
    classify_codex_review must return skip rather than auto_fixable.
    """
    ctx = _codex_context("update profile: …", path=None, kind=ReviewKind.review_body)
    assert classify_codex_review(ctx) == Classification.skip
