from __future__ import annotations

import json
from pathlib import Path

from ugh_quantamental.review_autofix import bot


def _write_event(
    path: Path,
    body: str = "P1 please set range_hit to None",
    updated_at: str = "2024-01-01T00:00:00Z",
    reviewer: str = "bob",
) -> None:
    payload = {
        "repository": {"full_name": "acme/repo"},
        "pull_request": {
            "number": 12,
            "base": {"ref": "main"},
            "head": {"ref": "feature", "sha": "abc", "repo": {"full_name": "acme/repo"}},
        },
        "comment": {
            "id": 44,
            "pull_request_review_id": 10,
            "user": {"login": reviewer},
            "body": body,
            "path": "dummy.py",
            "diff_hunk": "@@",
            "line": 1,
            "start_line": 1,
            "updated_at": updated_at,
            "node_id": "PRRC_node_44",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class _FakeGithubClient:
    markers: set[str] = set()
    resolved_node_ids: list[str] = []

    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        del token
        del api_url

    def has_processed_marker(self, context, marker: str) -> bool:
        del context
        return marker in self.markers

    def persist_marker(self, context, marker: str) -> None:
        del context
        self.markers.add(marker)

    def resolve_review_thread(self, comment_node_id: str) -> bool:
        self.resolved_node_ids.append(comment_node_id)
        return True

    def reply_to_review_comment(self, repo: str, comment_id: int, body: str) -> None:
        del repo
        del comment_id
        self.markers.add(body.splitlines()[-1])

    def reply_to_pr(self, repo: str, pr_number: int, body: str) -> None:
        del repo
        del pr_number
        self.markers.add(body.splitlines()[-1])


def _set_common_env(monkeypatch, tmp_path: Path, event_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request_review_comment")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("BOT_MODE", "apply_and_push")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("VALIDATION_LINT_COMMANDS", "true")
    monkeypatch.setenv("VALIDATION_TEST_COMMANDS", "true")


def test_human_actor_comment_is_processed(tmp_path: Path, monkeypatch) -> None:
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path, reviewer="alice")
    _set_common_env(monkeypatch, tmp_path, event_path)

    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    result = bot.run()
    assert result.reason == "pushed"


def test_trusted_bot_actor_comment_is_processed(tmp_path: Path, monkeypatch) -> None:
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path, reviewer="trusted-review-bot[bot]")
    _set_common_env(monkeypatch, tmp_path, event_path)
    monkeypatch.setenv("ALLOWED_BOT_REVIEWERS", "trusted-review-bot[bot]")

    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    result = bot.run()
    assert result.reason == "pushed"


def test_untrusted_bot_actor_comment_is_skipped(tmp_path: Path, monkeypatch) -> None:
    event_path = tmp_path / "event.json"
    _write_event(event_path, reviewer="unknown-bot[bot]")
    _set_common_env(monkeypatch, tmp_path, event_path)

    result = bot.run()
    assert result.reason == "ignored-actor"


def test_self_bot_actor_comment_is_skipped(tmp_path: Path, monkeypatch) -> None:
    event_path = tmp_path / "event.json"
    _write_event(event_path, reviewer="github-actions[bot]")
    _set_common_env(monkeypatch, tmp_path, event_path)

    result = bot.run()
    assert result.reason == "ignored-actor"


def test_bot_applies_rule_and_prevents_duplicate(tmp_path: Path, monkeypatch) -> None:
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path)
    _set_common_env(monkeypatch, tmp_path, event_path)

    monkeypatch.setattr(bot, "has_changes", lambda: True)

    committed: list[str] = []
    pushed: list[str] = []
    monkeypatch.setattr(bot, "commit_changes", lambda msg: committed.append(msg))
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: pushed.append(branch))

    result = bot.run()
    assert result.pushed is True
    assert committed
    assert pushed == ["feature"]

    duplicate = bot.run()
    assert duplicate.reason == "duplicate"


def test_durable_duplicate_detection_across_runs(tmp_path: Path, monkeypatch) -> None:
    _FakeGithubClient.markers = set()
    event_path = tmp_path / "event.json"
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    _write_event(event_path, reviewer="alice")

    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClient)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    _set_common_env(monkeypatch, tmp_path, event_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-1.json"))

    first = bot.run()
    assert first.reason == "pushed"

    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-2.json"))
    second = bot.run()
    assert second.reason == "duplicate"


def test_durable_marker_persists_when_reply_on_success_disabled(tmp_path: Path, monkeypatch) -> None:
    _FakeGithubClient.markers = set()
    event_path = tmp_path / "event.json"
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    _write_event(event_path, reviewer="alice")

    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClient)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    _set_common_env(monkeypatch, tmp_path, event_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("REPLY_ON_SUCCESS", "false")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-1.json"))

    first = bot.run()
    assert first.reason == "pushed"

    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-2.json"))
    second = bot.run()
    assert second.reason == "duplicate"


def test_edited_comment_reprocesses_with_new_version(tmp_path: Path, monkeypatch) -> None:
    _FakeGithubClient.markers = set()
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path, body="set range_hit to None", updated_at="2024-01-01T00:00:00Z")

    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClient)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    _set_common_env(monkeypatch, tmp_path, event_path)
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-1.json"))

    first = bot.run()
    assert first.reason == "pushed"

    _write_event(event_path, body="set range_hit to None #edited", updated_at="2024-01-01T00:02:00Z")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state-2.json"))
    second = bot.run()
    assert second.reason != "duplicate"


def test_apply_push_and_resolve_mode_resolves_thread(tmp_path: Path, monkeypatch) -> None:
    _FakeGithubClient.markers = set()
    _FakeGithubClient.resolved_node_ids = []
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path, reviewer="alice")

    monkeypatch.setattr(bot, "GithubClient", _FakeGithubClient)
    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    _set_common_env(monkeypatch, tmp_path, event_path)
    monkeypatch.setenv("BOT_MODE", "apply_push_and_resolve")
    monkeypatch.setenv("AUTO_RESOLVE", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "x")

    result = bot.run()
    assert result.reason == "pushed"
    assert _FakeGithubClient.resolved_node_ids == ["PRRC_node_44"]


def test_invalid_bot_mode_fails_closed(tmp_path: Path, monkeypatch) -> None:
    event_path = tmp_path / "event.json"
    _write_event(event_path, reviewer="alice")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request_review_comment")
    monkeypatch.setenv("BOT_MODE", "apply_and_push_typo")

    monkeypatch.setattr(bot, "commit_changes", lambda msg: (_ for _ in ()).throw(AssertionError("should not commit")))
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: (_ for _ in ()).throw(AssertionError("should not push")))

    result = bot.run()
    assert result.reason == "invalid-bot-mode"


def test_non_review_event_is_noop(tmp_path: Path, monkeypatch) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")

    result = bot.run()
    assert result.reason == "unsupported-event"


def test_validation_failure_does_not_push(tmp_path: Path, monkeypatch) -> None:
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request_review_comment")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("BOT_MODE", "apply_and_push")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("VALIDATION_LINT_COMMANDS", "false")
    monkeypatch.setenv("VALIDATION_TEST_COMMANDS", "")

    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: (_ for _ in ()).throw(AssertionError("should not commit")))
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: (_ for _ in ()).throw(AssertionError("should not push")))

    result = bot.run()
    assert result.reason == "validation-failed"
    assert result.pushed is False
