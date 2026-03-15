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


def test_noop_artifact_only_does_not_push(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    class _ArtifactOnlyExecutor:
        def submit_fix_task(self, task):
            from ugh_quantamental.review_autofix.executor_models import CodexTaskHandle

            return CodexTaskHandle(task_id=task.task_id)

        def wait_for_result(self, handle):
            del handle
            artifact = Path(".autofix-bot") / "codex-task-artifact.txt"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("prompt", encoding="utf-8")
            return CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok")

        def apply_or_confirm_branch_update(self, handle, result):
            del handle, result
            return CodexApplyResult(changed=True, branch_updated=False, summary="ok")

    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: _ArtifactOnlyExecutor())
    monkeypatch.setattr(bot, "commit_changes", lambda msg: (_ for _ in ()).throw(AssertionError("should not commit")))
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: (_ for _ in ()).throw(AssertionError("should not push")))

    result = bot.run()
    assert result.reason == "no-change-after-codex"
    assert result.pushed is False


def test_codex_review_without_legacy_keywords_reaches_executor(tmp_path: Path, monkeypatch) -> None:
    """A Codex review body that matches none of the legacy auto-keywords must still
    reach the executor and succeed (classify_codex_review defaults to auto_fixable)."""
    event = tmp_path / "event.json"
    payload = {
        "repository": {"full_name": "acme/repo"},
        "pull_request": {
            "number": 12,
            "base": {"ref": "main"},
            "head": {"ref": "feature", "sha": "abc", "repo": {"full_name": "acme/repo"}},
        },
        "comment": {
            "id": 99,
            "pull_request_review_id": 10,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": "Please rename this variable to snake_case.",  # no legacy keywords
            "path": "src/foo.py",
            "diff_hunk": "@@",
            "line": 3,
            "start_line": 3,
            "updated_at": "2024-06-01T00:00:00Z",
            "node_id": "PRRC_node_99",
        },
    }
    event.write_text(json.dumps(payload), encoding="utf-8")
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")

    submitted: list[str] = []

    class _Stub:
        def submit_fix_task(self, task):
            submitted.append(task.prompt)
            return CodexTaskHandle(task_id=task.task_id)

        def wait_for_result(self, handle):
            return CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok")

        def apply_or_confirm_branch_update(self, handle, result):
            return CodexApplyResult(changed=True, branch_updated=False, summary="ok")

    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: _Stub())
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    result = bot.run()
    assert result.reason == "pushed"
    assert submitted, "executor must have been called"


def _write_review_event_no_path(path: Path, reviewer: str = "chatgpt-codex-connector[bot]") -> None:
    """pull_request_review event with no file:/path: hint in the review body."""
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
            "body": "P1 please set range_hit to None",  # no file: hint
            "submitted_at": "2024-01-01T00:00:00Z",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


_FAKE_INLINE_COMMENT: dict = {
    "id": 44,
    "pull_request_review_id": 10,
    "user": {"login": "chatgpt-codex-connector[bot]"},
    "body": "P1 please set range_hit to None",
    "path": "dummy.py",
    "diff_hunk": "@@",
    "line": 310,
    "start_line": 310,
    "updated_at": "2024-01-01T00:00:00Z",
    "node_id": "PRRC_node_44",
}


class _FakeGithubClientWithInlineComments:
    """Fake GithubClient that returns configurable inline comments for the fallback path."""

    markers: set[str] = set()
    inline_comments: tuple[dict, ...] = ()

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

    def list_review_comments_for_review(self, repo: str, pr_number: int, review_id: int) -> tuple[dict, ...]:
        del repo, pr_number, review_id
        return self.inline_comments


def test_review_body_no_path_with_inline_comment_expands_and_processes(
    tmp_path: Path, monkeypatch
) -> None:
    """review_body + no file hint + related inline comment → skip does NOT occur; inline comment
    is classified and processed instead."""
    _FakeGithubClientWithInlineComments.markers = set()
    _FakeGithubClientWithInlineComments.inline_comments = (_FAKE_INLINE_COMMENT,)

    event = tmp_path / "event.json"
    _write_review_event_no_path(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClientWithInlineComments)

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
    assert stub.submitted_prompts, "executor must have been called for the inline comment"
    # processed_key should reflect the inline comment, not the review body
    assert result.processed_key.startswith("review_comment:")


def test_review_body_no_path_without_inline_comments_skips_with_descriptive_reason(
    tmp_path: Path, monkeypatch
) -> None:
    """review_body + no file hint + no inline comments → skip with specific reason."""
    _FakeGithubClientWithInlineComments.markers = set()
    _FakeGithubClientWithInlineComments.inline_comments = ()

    event = tmp_path / "event.json"
    _write_review_event_no_path(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClientWithInlineComments)

    called = {"executor": False}

    def _builder(command, timeout_seconds):
        del command, timeout_seconds
        called["executor"] = True
        raise AssertionError("executor should not run when no inline comments exist")

    monkeypatch.setattr(bot, "build_executor", _builder)

    result = bot.run()

    assert result.reason == "review-body-no-path-no-inline-comments"
    assert result.classification == bot.Classification.skip
    assert called["executor"] is False


def test_review_body_fallback_deduplicates_on_second_run(tmp_path: Path, monkeypatch) -> None:
    """The same pull_request_review event must not trigger re-processing on a second bot run.
    Both the review body key and the inline comment key are marked; the second run must be
    recognised as a duplicate via the GitHub marker."""
    _FakeGithubClientWithInlineComments.markers = set()
    _FakeGithubClientWithInlineComments.inline_comments = (_FAKE_INLINE_COMMENT,)

    event = tmp_path / "event.json"
    _write_review_event_no_path(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClientWithInlineComments)

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

    # New state store to defeat file-based dedupe; GitHub marker dedupe must catch it.
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-2.json"))
    second = bot.run()
    assert second.reason == "duplicate"


def test_review_body_fallback_does_not_affect_diff_comment_events(
    tmp_path: Path, monkeypatch
) -> None:
    """Existing pull_request_review_comment events continue to process without any fallback."""
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
    assert result.processed_key.startswith("review_comment:")


def test_invalid_review_body_path_hint_skips_without_executor(tmp_path: Path, monkeypatch) -> None:
    event = tmp_path / "event.json"
    _write_review_event(event)
    payload = json.loads(event.read_text(encoding="utf-8"))
    payload["review"]["body"] = "file: ../tmp/x.py\nP1 please set range_hit to None"
    event.write_text(json.dumps(payload), encoding="utf-8")

    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review")

    called = {"executor": False}

    def _builder(command, timeout_seconds):
        del command, timeout_seconds
        called["executor"] = True
        raise AssertionError("executor should not run")

    monkeypatch.setattr(bot, "build_executor", _builder)

    result = bot.run()
    assert result.reason == "invalid-review-body-path"
    assert called["executor"] is False


# ---------------------------------------------------------------------------
# Shadow audit integration tests (A – F)
# ---------------------------------------------------------------------------


def _noop_shadow_audit(context, audit_id: str, action_features=None) -> None:
    """Drop-in replacement for _run_shadow_audit that records calls."""


def test_shadow_audit_pre_only_in_detect_only(tmp_path: Path, monkeypatch) -> None:
    """A. detect_only mode: shadow audit is called exactly once (pre-action only)."""
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")
    monkeypatch.setenv("BOT_MODE", "detect_only")

    audit_calls: list[dict] = []

    def _mock_audit(context, audit_id: str, action_features=None) -> None:
        audit_calls.append({"audit_id": audit_id, "action_features": action_features})

    monkeypatch.setattr(bot, "_run_shadow_audit", _mock_audit)

    result = bot.run()

    assert result.reason == "detect-only"
    assert len(audit_calls) == 1, "pre-action audit must be called exactly once"
    assert audit_calls[0]["action_features"] is None, "pre-action audit must have no action_features"


def test_shadow_audit_pre_only_in_propose_only(tmp_path: Path, monkeypatch) -> None:
    """B. propose_only mode: shadow audit is called exactly once (pre-action only)."""
    event = tmp_path / "event.json"
    _write_comment_event(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review_comment")
    monkeypatch.setenv("BOT_MODE", "propose_only")

    audit_calls: list[dict] = []

    def _mock_audit(context, audit_id: str, action_features=None) -> None:
        audit_calls.append({"audit_id": audit_id, "action_features": action_features})

    monkeypatch.setattr(bot, "_run_shadow_audit", _mock_audit)

    result = bot.run()

    assert result.reason == "proposed-only"
    assert len(audit_calls) == 1
    assert audit_calls[0]["action_features"] is None


def test_shadow_audit_pre_and_post_in_apply_and_push(tmp_path: Path, monkeypatch) -> None:
    """C. apply_and_push mode: shadow audit is called twice; first call has no action_features,
    second call has populated FixActionFeatures.  Push behaviour is unaffected."""
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
    monkeypatch.setattr(bot, "get_diff_stats", lambda: (("dummy.py",), 1, 5))

    audit_calls: list[dict] = []

    def _mock_audit(context, audit_id: str, action_features=None) -> None:
        audit_calls.append({"audit_id": audit_id, "action_features": action_features})

    monkeypatch.setattr(bot, "_run_shadow_audit", _mock_audit)

    result = bot.run()

    assert result.reason == "pushed"
    assert len(audit_calls) == 2, "pre-action and post-action audit must both be called"
    assert audit_calls[0]["action_features"] is None, "first call is pre-action"
    assert audit_calls[1]["action_features"] is not None, "second call is post-action"
    # Both calls share the same audit_id.
    assert audit_calls[0]["audit_id"] == audit_calls[1]["audit_id"]


def test_shadow_audit_failure_is_swallowed(tmp_path: Path, monkeypatch) -> None:
    """D. If _run_shadow_audit raises, the bot still proceeds and pushes normally."""
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
    monkeypatch.setattr(bot, "get_diff_stats", lambda: ((), 0, 0))

    def _failing_audit(context, audit_id: str, action_features=None) -> None:
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr(bot, "_run_shadow_audit", _failing_audit)

    # Bot must succeed despite audit failure.
    result = bot.run()
    assert result.reason == "pushed"
    assert result.pushed is True


def test_shadow_audit_runs_on_review_body_inline_fallback(tmp_path: Path, monkeypatch) -> None:
    """E. review-body inline fallback: audit runs on the expanded inline comment context."""
    _FakeGithubClientWithInlineComments.markers = set()
    _FakeGithubClientWithInlineComments.inline_comments = (_FAKE_INLINE_COMMENT,)

    event = tmp_path / "event.json"
    _write_review_event_no_path(event)
    _set_common_env(monkeypatch, tmp_path, event, "pull_request_review")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClientWithInlineComments)

    stub = _ExecutorStub(
        CodexExecutionResult(CodexExecutionStatus.succeeded, True, "ok"),
        CodexApplyResult(changed=True, branch_updated=False, summary="ok"),
    )
    monkeypatch.setattr(bot, "build_executor", lambda command, timeout_seconds: stub)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)
    monkeypatch.setattr(bot, "get_diff_stats", lambda: (("dummy.py",), 1, 3))

    audit_calls: list[dict] = []

    def _mock_audit(context, audit_id: str, action_features=None) -> None:
        audit_calls.append({"context": context, "action_features": action_features})

    monkeypatch.setattr(bot, "_run_shadow_audit", _mock_audit)

    result = bot.run()

    assert result.reason == "pushed"
    # At least the pre-action audit ran on the expanded inline comment context.
    assert len(audit_calls) >= 1
    # The audited context must be the concrete inline comment (has a path).
    assert audit_calls[0]["context"].path == "dummy.py"


def test_extract_fix_action_features_determinism(tmp_path: Path, monkeypatch) -> None:
    """F. extract_fix_action_features is pure and deterministic.

    Covers: same inputs → same output, bounded [0,1], target_file_match logic,
    and absence of git / runtime side effects.
    """
    from ugh_quantamental.review_autofix.feature_extractor import extract_fix_action_features
    from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind

    ctx = ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=1,
        review_id=None,
        review_comment_id=1,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="bot",
        body="set x to None",
        path="src/foo.py",
        diff_hunk="@@",
        line=10,
        start_line=10,
        version_discriminator="v1",
    )

    kwargs = dict(
        context=ctx,
        changed=True,
        validation_ok=True,
        execution_status="succeeded",
        files_changed=2,
        lines_changed=20,
        touched_paths=("src/foo.py", "src/bar.py"),
    )

    result1 = extract_fix_action_features(**kwargs)
    result2 = extract_fix_action_features(**kwargs)

    # Determinism: two calls with the same inputs must produce identical output.
    assert result1 == result2

    # Bounds: all float fields must be in [0, 1].
    assert 0.0 <= result1.target_file_match <= 1.0
    assert 0.0 <= result1.line_anchor_touched <= 1.0
    assert 0.0 <= result1.diff_hunk_overlap <= 1.0
    assert 0.0 <= result1.scope_ratio <= 1.0
    assert 0.0 <= result1.validation_scope_executed <= 1.0
    assert 0.0 <= result1.behavior_preservation_proxy <= 1.0

    # target_file_match: 1.0 because ctx.path is in touched_paths.
    assert result1.target_file_match == 1.0

    # target_file_match: 0.0 when the file is not touched.
    result_no_match = extract_fix_action_features(
        **{**kwargs, "touched_paths": ("src/other.py",)}
    )
    assert result_no_match.target_file_match == 0.0

    # validation_scope_executed: 1.0 when validation passed, 0.0 otherwise.
    assert result1.validation_scope_executed == 1.0
    result_val_fail = extract_fix_action_features(**{**kwargs, "validation_ok": False})
    assert result_val_fail.validation_scope_executed == 0.0

    # behavior_preservation_proxy: 1.0 when changed+validation_ok, 0.3 when changed only.
    assert result1.behavior_preservation_proxy == 1.0
    assert result_val_fail.behavior_preservation_proxy == 0.3

    # execution_status must pass through unchanged.
    assert result1.execution_status == "succeeded"
