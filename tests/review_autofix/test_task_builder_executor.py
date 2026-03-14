from __future__ import annotations

from pathlib import Path

from ugh_quantamental.review_autofix.codex_executor import LocalSubprocessCodexExecutor
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


def test_executor_returns_failed_when_command_not_configured() -> None:
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
    executor = LocalSubprocessCodexExecutor(command="", timeout_seconds=30)
    handle = executor.submit_fix_task(task)
    result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.failed


def test_executor_runs_command_and_writes_prompt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
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
    executor = LocalSubprocessCodexExecutor(command="test -f \"$CODEX_TASK_FILE\"", timeout_seconds=30)
    handle = executor.submit_fix_task(task)
    result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.succeeded
