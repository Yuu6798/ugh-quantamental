from __future__ import annotations

import json
from pathlib import Path

from ugh_quantamental.review_autofix import bot
from ugh_quantamental.review_autofix.executor_models import (
    CodexApplyResult,
    CodexExecutionResult,
    CodexExecutionStatus,
    CodexTaskHandle,
)


class _ExecutorStub:
    def __init__(self, result: CodexExecutionResult, apply_result: CodexApplyResult) -> None:
        self._result = result
        self._apply_result = apply_result
        self.submitted_prompts: list[str] = []

    def submit_fix_task(self, task):
        self.submitted_prompts.append(task.prompt)
        return CodexTaskHandle(task_id=task.task_id)

    def wait_for_result(self, handle: CodexTaskHandle) -> CodexExecutionResult:
        del handle
        return self._result

    def apply_or_confirm_branch_update(self, handle: CodexTaskHandle, result: CodexExecutionResult) -> CodexApplyResult:
        del handle
        del result
        return self._apply_result


class _FakeGithubClient:
    markers: set[str] = set()

    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        del token, api_url

    def has_processed_marker(self, context, marker: str) -> bool:
        del context
        return marker in self.markers

    def persist_marker(self, context, marker: str) -> None:
        del context
        self.markers.add(marker)

    def reply_to_review_comment(self, repo: str, comment_id: int, body: str) -> None:
        del repo, comment_id
        self.markers.add(body.splitlines()[-1])

    def reply_to_pr(self, repo: str, pr_number: int, body: str) -> None:
        del repo, pr_number
        self.markers.add(body.splitlines()[-1])


def _write_comment_event(path: Path, reviewer: str = "chatgpt-codex-connector[bot]", head_repo: str = "acme/repo") -> None:
    payload = {
        "repository": {"full_name": "acme/repo"},
        "pull_request": {
            "number": 12,
            "base": {"ref": "main"},
            "head": {"ref": "feature", "sha": "abc", "repo": {"full_name": head_repo}},
        },
        "comment": {
            "id": 44,
            "pull_request_review_id": 10,
            "user": {"login": reviewer},
            "body": "P1 please set range_hit to None",
            "path": "dummy.py",
            "diff_hunk": "@@",
            "line": 1,
            "start_line": 1,
            "updated_at": "2024-01-01T00:00:00Z",
            "node_id": "PRRC_node_44",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_review_event(path: Path, reviewer: str = "chatgpt-codex-connector[bot]") -> None:
    payload = {
        "repository": {"full_name": "acme/repo"},
        "pull_request": {
            "number": 12,
            "base": {"ref": "main"},
            "head": {"ref": "feature", "sha": "abc", "repo": {"full_name": "acme/repo"}},
        },
        "review": {
            "id": 10,
            "user": {"login": reviewer},
            "body": "file: dummy.py\nP1 please set range_hit to None",
            "submitted_at": "2024-01-01T00:00:00Z",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _set_common_env(monkeypatch, tmp_path: Path, event_path: Path, event_name: str) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("BOT_MODE", "apply_and_push")
    monkeypatch.setenv("TARGET_REVIEWERS", "chatgpt-codex-connector[bot]")
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "chatgpt-codex-connector[bot]")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("VALIDATION_LINT_COMMANDS", "true")
    monkeypatch.setenv("VALIDATION_TEST_COMMANDS", "true")


def test_codex_reviewer_comment_builds_task(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    result = bot.run()

    assert result.reason == "pushed"
    assert stub.submitted_prompts


def test_non_codex_reviewer_ignored_actor(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event, reviewer="alice")
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")
    assert bot.run().reason == "ignored-actor"


def test_self_bot_ignored_actor(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event, reviewer="github-actions[bot]")
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "chatgpt-codex-connector[bot],github-actions[bot]")
    assert bot.run().reason == "ignored-actor"


def test_duplicate_review_skips(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    first = bot.run()
    second = bot.run()

    assert first.reason == "pushed"
    assert second.reason == "duplicate"


def test_noop_from_executor_does_not_push(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.no_op, False, "noop"),
        CodexApplyResult(changed=False, branch_updated=False, summary="noop"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: (_ for _ in ()).throw(AssertionError("should not push")))

    result = bot.run()
    assert result.reason == "codex-no-op"
    assert result.pushed is False


def test_validation_failure_does_not_push(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")
    monkeypatch.setenv("VALIDATION_LINT_COMMANDS", "false")

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: (_ for _ in ()).throw(AssertionError("should not commit")))
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: (_ for _ in ()).throw(AssertionError("should not push")))

    result = bot.run()
    assert result.reason == "validation-failed"


def test_success_pushes_same_branch(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    pushed: list[str] = []
    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: pushed.append(branch))

    result = bot.run()
    assert result.reason == "pushed"
    assert pushed == ["feature"]


def test_review_body_event_is_supported(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_review_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review")

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    result = bot.run()
    assert result.reason == "pushed"


def test_fork_safety_keeps_propose_only(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event, head_repo="fork/repo")
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    called = {"executor": False}

    def _builder(command, timeout_seconds):
        del command, timeout_seconds
        called["executor"] = True
        raise AssertionError("executor should not run for fork propose-only")

    monkeypatch.setattr(bot, "build_executor", _builder)

    result = bot.run()
    assert result.reason == "proposed-only"
    assert called["executor"] is False


def test_durable_duplicate_detection_with_github_marker(tmp_path: Path, monkeypatch) -> None:
    _FakeGithubClient.markers = set()
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClient)

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    first = bot.run()
    assert first.reason == "pushed"

    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-2.json"))
    second = bot.run()
    assert second.reason == "duplicate"
