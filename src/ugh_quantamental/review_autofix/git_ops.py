from __future__ import annotations

import subprocess


def get_diff_stats() -> tuple[tuple[str, ...], int, int]:
    """Return ``(touched_paths, files_changed, lines_changed)`` for uncommitted changes.

    Runs ``git diff HEAD --numstat`` to enumerate modified files and line deltas.
    Returns ``((), 0, 0)`` on any error.  Intended for best-effort shadow audit use only.
    """
    try:
        proc = subprocess.run(
            ["git", "diff", "HEAD", "--numstat"],
            capture_output=True,
            text=True,
            check=False,
        )
        paths: list[str] = []
        total_lines = 0
        for line in proc.stdout.splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                try:
                    total_lines += int(parts[0]) + int(parts[1])
                except ValueError:
                    pass
                paths.append(parts[2])
        return tuple(paths), len(paths), total_lines
    except Exception:
        return (), 0, 0


def has_changes() -> bool:
    proc = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    commitworthy = [line for line in lines if ".autofix-bot/" not in line]
    return bool(commitworthy)


def commit_changes(message: str) -> None:
    subprocess.run("git add -A -- . ':(exclude).autofix-bot/**'", shell=True, check=True)
    subprocess.run(f"git commit -m {message!r}", shell=True, check=True)


def push_head_branch(branch: str) -> None:
    subprocess.run(["git", "push", "origin", f"HEAD:{branch}"], check=True)


def revert_working_tree_changes(preserve_paths: tuple[str, ...] = ()) -> None:
    """Restore all tracked files to HEAD state and remove untracked files created by the bot.

    Called when validation fails after the executor writes new file content to disk, so that
    subsequent bot runs start from a clean working tree rather than a partially-broken state.
    Untracked files (new files created by the executor) are removed; tracked files are
    restored to their HEAD versions.  Best-effort — any error is silently ignored so that
    a revert failure never blocks the bot from completing its run.

    Files under ``.autofix-bot/`` are always preserved, and any additional paths supplied
    via *preserve_paths* (e.g. a custom ``STATE_STORE_PATH``) are also skipped so that
    ``state.mark(key)`` can still complete after a validation failure regardless of where
    the state file lives.
    """
    import os

    try:
        subprocess.run(["git", "checkout", "HEAD", "--", "."], check=False)
    except Exception:
        pass
    try:
        for path in list_untracked_files():
            if ".autofix-bot/" in path:
                continue
            if any(path == p or path.startswith(p.rstrip("/") + "/") for p in preserve_paths):
                continue
            try:
                os.remove(path)
            except OSError:
                pass
    except Exception:
        pass


def list_untracked_files() -> list[str]:
    """Return a list of untracked file paths in the working directory.

    Raises ``subprocess.CalledProcessError`` if git exits non-zero (e.g. when
    called outside a git worktree).
    """
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()
