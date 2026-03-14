from pathlib import Path

from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind
from ugh_quantamental.review_autofix.rules import NoneNormalizationRule, RuleRegistry


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


def test_none_rule_missing_target_file_is_safe_noop(tmp_path: Path) -> None:
    missing = tmp_path / "missing.py"
    context = _context("Please set range_hit to None", str(missing))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert result.details == "missing file"


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


def test_none_rule_preserves_semicolon_suffix_content(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5; audit()\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "range_hit = None; audit()\n"


def test_none_rule_preserves_inline_comment_suffix(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5  # keep note\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "range_hit = None  # keep note\n"


def test_none_rule_preserves_unrelated_trailing_text(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5; other = range_hit + 1\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "range_hit = None; other = range_hit + 1\n"


def test_import_rule_is_selectable() -> None:
    context = _context("lint: sort imports", "src/file.py")
    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None
    assert rule.rule_id == "import-cleanup"


def test_import_rule_does_not_modify_multiline_string(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sample.py"
    target.write_text(
        "doc = \"\"\"\nimport  fake\n\"\"\"\nimport  os\n",
        encoding="utf-8",
    )
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "doc = \"\"\"\nimport  fake\n\"\"\"\nimport os\n"


def test_import_rule_missing_target_file_is_safe_noop(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    missing = tmp_path / "missing.py"
    context = _context("lint: sort imports", str(missing))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert result.details == "missing file"


def test_import_rule_existing_file_behavior_unchanged(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sample.py"
    target.write_text("import  os\nx = 1\n", encoding="utf-8")
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert result.details == "applied"
    assert target.read_text(encoding="utf-8") == "import os\nx = 1\n"



def test_import_rule_preserves_lf_newlines(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sample.py"
    target.write_text("import  os\nx = 1\n", encoding="utf-8")
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "import os\nx = 1\n"


def test_import_rule_preserves_crlf_newlines(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sample.py"
    target.write_bytes(b"import  os\r\nx = 1\r\n")
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_bytes() == b"import os\r\nx = 1\r\n"


def test_import_rule_skips_symlink_target_resolving_outside_repo(tmp_path: Path, monkeypatch) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("import  os\n", encoding="utf-8")

    repo = tmp_path / "repo"
    repo.mkdir()
    link = repo / "linked.py"
    link.symlink_to(outside)

    monkeypatch.chdir(repo)
    context = _context("lint: sort imports", str(link))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert result.details == "unsafe target"
    assert outside.read_text(encoding="utf-8") == "import  os\n"


def test_import_rule_skips_absolute_target_outside_repo_root(tmp_path: Path, monkeypatch) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("import  os\n", encoding="utf-8")

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    context = _context("lint: sort imports", str(outside))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert result.details == "unsafe target"
    assert outside.read_text(encoding="utf-8") == "import  os\n"

def test_import_rule_preserves_indentation_inside_function(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sample.py"
    target.write_text(
        "def f():\n    import  os\n    return os.name\n",
        encoding="utf-8",
    )
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "def f():\n    import os\n    return os.name\n"


def test_import_rule_preserves_indentation_inside_try_block(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "sample.py"
    target.write_text(
        "try:\n    import  os\nexcept Exception:\n    pass\n",
        encoding="utf-8",
    )
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "try:\n    import os\nexcept Exception:\n    pass\n"


def test_import_rule_not_selected_by_important_word() -> None:
    context = _context("This is important for docs", "src/file.py")
    registry = RuleRegistry()
    assert registry.match(context) is None


def test_import_rule_not_selected_by_generic_import_cleanup_mention() -> None:
    context = _context("We discussed import-cleanup in roadmap", "src/file.py")
    registry = RuleRegistry()
    assert registry.match(context) is None



def test_import_rule_not_selected_by_generic_unused_feedback() -> None:
    context = _context("There is an unused variable in this function", "src/file.py")
    registry = RuleRegistry()
    assert registry.match(context) is None


def test_import_rule_selected_by_unused_imports_feedback() -> None:
    context = _context("Please remove unused imports", "src/file.py")
    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None
    assert rule.rule_id == "import-cleanup"


def test_import_rule_selected_by_explicit_rule_id() -> None:
    context = _context("rule: import-cleanup", "src/file.py")
    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None
    assert rule.rule_id == "import-cleanup"


def test_none_rule_review_body_fallback_applies_without_line(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("x = 1\nrange_hit = 0.5\n", encoding="utf-8")
    context = ReviewContext(
        kind=ReviewKind.review_body,
        repository="acme/repo",
        pr_number=7,
        review_id=99,
        review_comment_id=None,
        head_sha="sha",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="reviewer",
        body="file: sample.py\nset range_hit to None",
        path=str(target),
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v",
    )

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "x = 1\nrange_hit = None\n"


def test_none_rule_review_body_generic_none_text_does_not_match(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("x = 1\nrange_hit = 0.5\n", encoding="utf-8")
    context = ReviewContext(
        kind=ReviewKind.review_body,
        repository="acme/repo",
        pr_number=7,
        review_id=99,
        review_comment_id=None,
        head_sha="sha",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="reviewer",
        body="file: sample.py\nnone of this should be auto fixed",
        path=str(target),
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v",
    )

    registry = RuleRegistry()
    assert registry.match(context) is None


def test_none_rule_review_body_generic_set_none_without_range_hit_does_not_match(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("x = 1\nrange_hit = 0.5\n", encoding="utf-8")
    context = ReviewContext(
        kind=ReviewKind.review_body,
        repository="acme/repo",
        pr_number=7,
        review_id=99,
        review_comment_id=None,
        head_sha="sha",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="reviewer",
        body="file: sample.py\nPlease set foo to None",
        path=str(target),
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v",
    )

    registry = RuleRegistry()
    assert registry.match(context) is None


def test_none_rule_diff_comment_without_line_still_noop(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target), line=1)
    context = ReviewContext(**{**context.__dict__, "line": None, "start_line": None})

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert result.details == "no reviewed line"
    assert target.read_text(encoding="utf-8") == "range_hit = 0.5\n"


def test_import_rule_skips_semicolon_mixed_content_line(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text('import  os; msg = "a  b"\n', encoding="utf-8")
    context = _context("lint: sort imports", str(target))

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert target.read_text(encoding="utf-8") == 'import  os; msg = "a  b"\n'


def test_none_rule_diff_comment_generic_none_text_does_not_match() -> None:
    context = _context("none of these import changes look right", "src/file.py")
    rule = NoneNormalizationRule()
    assert rule.match(context) is None


def test_none_rule_diff_comment_explicit_intent_still_matches() -> None:
    context = _context("Please set range_hit to None", "src/file.py")
    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None
    assert rule.rule_id == "none-normalization"

def test_none_rule_multiline_diff_uses_start_line_when_targeted(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5\nother = 1\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target), line=2)
    context = ReviewContext(**{**context.__dict__, "start_line": 1})

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is True
    assert target.read_text(encoding="utf-8") == "range_hit = None\nother = 1\n"


def test_none_rule_single_line_still_respects_reviewed_line(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("range_hit = 0.5\nother = 1\n", encoding="utf-8")
    context = _context("Please set range_hit to None", str(target), line=2)

    registry = RuleRegistry()
    rule = registry.match(context)
    assert rule is not None

    result = rule.apply(context)
    assert result.changed is False
    assert result.details == "no-op"
    assert target.read_text(encoding="utf-8") == "range_hit = 0.5\nother = 1\n"
