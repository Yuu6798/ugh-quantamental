from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from ugh_quantamental.review_autofix.codex_executor import DirectApiCodexExecutor
from ugh_quantamental.review_autofix.executor_models import CodexExecutionStatus
from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind
from ugh_quantamental.review_autofix.task_builder import build_fix_task


def test_task_builder_includes_required_constraints() -> None:
    context = ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=10,
        review_id=2,
        review_comment_id=3,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="chatgpt-codex-connector[bot]",
        body="please fix",
        path="a.py",
        diff_hunk="@@",
        line=5,
        start_line=4,
        version_discriminator="v1",
    )

    task = build_fix_task(context, "k1")
    assert "same branch update only" in task.prompt
    assert "no new PR" in task.prompt
    assert "fix only the cited review finding" in task.prompt
    assert "run relevant tests" in task.prompt


def _make_urlopen_mock(changes: list) -> MagicMock:
    import json
    body = json.dumps({
        "choices": [{"message": {"content": json.dumps({"changes": changes})}}]
    }).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_executor_returns_failed_when_api_key_missing(monkeypatch) -> None:
    """DirectApiCodexExecutor returns failed when OPENAI_API_KEY is absent."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    context = ReviewContext(
        kind=ReviewKind.review_body,
        repository="acme/repo",
        pr_number=10,
        review_id=2,
        review_comment_id=None,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="chatgpt-codex-connector[bot]",
        body="file: a.py",
        path="a.py",
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v1",
    )
    task = build_fix_task(context, "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)
    result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.failed


def test_executor_applies_change_from_api(tmp_path: Path, monkeypatch) -> None:
    """DirectApiCodexExecutor writes files returned by the API and returns succeeded."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    context = ReviewContext(
        kind=ReviewKind.review_body,
        repository="acme/repo",
        pr_number=10,
        review_id=2,
        review_comment_id=None,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="chatgpt-codex-connector[bot]",
        body="file: a.py",
        path="a.py",
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v1",
    )
    task = build_fix_task(context, "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    mock_resp = _make_urlopen_mock([{"path": "a.py", "content": "fixed = True\n"}])
    with patch("ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen", return_value=mock_resp):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.succeeded
    assert (tmp_path / "a.py").read_text() == "fixed = True\n"
