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
