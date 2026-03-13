from __future__ import annotations

import json
from pathlib import Path

from ugh_quantamental.review_autofix import bot


def _write_event(path: Path, body: str = "P1 please set range_hit to None", updated_at: str = "2024-01-01T00:00:00Z") -> None:
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
            "user": {"login": "bob"},
            "body": body,
            "path": "dummy.py",
            "diff_hunk": "@@",
            "updated_at": updated_at,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_bot_applies_rule_and_prevents_duplicate(tmp_path: Path, monkeypatch) -> None:
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
    monkeypatch.setenv("VALIDATION_LINT_COMMANDS", "true")
    monkeypatch.setenv("VALIDATION_TEST_COMMANDS", "true")

    monkeypatch.setattr(bot, "has_changes", lambda: True)

    committed: list[str] = []
    pushed: list[str] = []
    monkeypatch.setattr(bot, "commit_changes", lambda msg: committed.append(msg))
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: pushed.append(branch))

    result = bot.run()
    assert result.pushed is True
    assert committed
    assert pushed == ["feature"]
    assert dummy.read_text(encoding="utf-8") == "range_hit = None\n"

    duplicate = bot.run()
    assert duplicate.reason == "duplicate"


def test_edited_comment_reprocesses_with_new_version(tmp_path: Path, monkeypatch) -> None:
    dummy = tmp_path / "dummy.py"
    dummy.write_text("range_hit = 1\n", encoding="utf-8")
    event_path = tmp_path / "event.json"
    _write_event(event_path, body="set range_hit to None", updated_at="2024-01-01T00:00:00Z")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request_review_comment")
    monkeypatch.setenv("STATE_STORE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("BOT_MODE", "apply_and_push")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("VALIDATION_LINT_COMMANDS", "true")
    monkeypatch.setenv("VALIDATION_TEST_COMMANDS", "true")

    monkeypatch.setattr(bot, "has_changes", lambda: True)
    monkeypatch.setattr(bot, "commit_changes", lambda msg: None)
    monkeypatch.setattr(bot, "push_head_branch", lambda branch: None)

    first = bot.run()
    assert first.reason == "pushed"

    _write_event(event_path, body="set range_hit to None #edited", updated_at="2024-01-01T00:02:00Z")
    second = bot.run()
    assert second.reason != "duplicate"


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
