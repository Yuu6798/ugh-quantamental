from __future__ import annotations

import subprocess


def has_changes() -> bool:
    proc = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    commitworthy = [line for line in lines if not line[3:].startswith(".autofix-bot/")]
    return bool(commitworthy)


def commit_changes(message: str) -> None:
    subprocess.run("git add -A -- . ':(exclude).autofix-bot/**'", shell=True, check=True)
    subprocess.run(f"git commit -m {message!r}", shell=True, check=True)


def push_head_branch(branch: str) -> None:
    subprocess.run(["git", "push", "origin", f"HEAD:{branch}"], check=True)
