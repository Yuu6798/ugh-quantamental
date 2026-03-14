from ugh_quantamental.review_autofix import git_ops


def test_commit_changes_excludes_operational_state(monkeypatch) -> None:
    commands: list[str] = []

    def fake_run(command: str, shell: bool, check: bool, **kwargs):
        del shell
        del check
        del kwargs
        commands.append(command)

        class Result:
            returncode = 0
            stdout = ""

        return Result()

    monkeypatch.setattr(git_ops.subprocess, "run", fake_run)
    git_ops.commit_changes("msg")

    assert commands[0] == "git add -A -- . ':(exclude).autofix-bot/**'"
    assert commands[1].startswith("git commit -m ")


def test_has_changes_ignores_autofix_bot_state_file(monkeypatch) -> None:
    def fake_run(command: str, shell: bool, capture_output: bool, text: bool, check: bool):
        del command
        del shell
        del capture_output
        del text
        del check

        class Result:
            stdout = "?? .autofix-bot/state.json\n"

        return Result()

    monkeypatch.setattr(git_ops.subprocess, "run", fake_run)
    assert git_ops.has_changes() is False


def test_has_changes_detects_real_code_changes(monkeypatch) -> None:
    def fake_run(command: str, shell: bool, capture_output: bool, text: bool, check: bool):
        del command
        del shell
        del capture_output
        del text
        del check

        class Result:
            stdout = "?? .autofix-bot/state.json\n M src/mod.py\n"

        return Result()

    monkeypatch.setattr(git_ops.subprocess, "run", fake_run)
    assert git_ops.has_changes() is True


def test_push_head_branch_uses_safe_arg_list(monkeypatch) -> None:
    calls: list[tuple[object, bool]] = []

    def fake_run(command, check: bool, **kwargs):
        calls.append((command, check))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(git_ops.subprocess, "run", fake_run)
    git_ops.push_head_branch("feature")
    assert calls == [(["git", "push", "origin", "HEAD:feature"], True)]


def test_has_changes_ignores_other_autofix_bot_artifacts(monkeypatch) -> None:
    def fake_run(command: str, shell: bool, capture_output: bool, text: bool, check: bool):
        del command
        del shell
        del capture_output
        del text
        del check

        class Result:
            stdout = "?? .autofix-bot/codex-task-k1.txt\n"

        return Result()

    monkeypatch.setattr(git_ops.subprocess, "run", fake_run)
    assert git_ops.has_changes() is False
