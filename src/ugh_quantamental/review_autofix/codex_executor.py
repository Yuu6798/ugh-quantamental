from __future__ import annotations

import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .executor_models import CodexApplyResult, CodexExecutionResult, CodexExecutionStatus, CodexFixTask, CodexTaskHandle

logger = logging.getLogger(__name__)


class CodexExecutor(Protocol):
    def submit_fix_task(self, task: CodexFixTask) -> CodexTaskHandle: ...

    def wait_for_result(self, handle: CodexTaskHandle) -> CodexExecutionResult: ...

    def apply_or_confirm_branch_update(self, handle: CodexTaskHandle, result: CodexExecutionResult) -> CodexApplyResult: ...


@dataclass(frozen=True)
class _SubmittedTask:
    task: CodexFixTask


class LocalSubprocessCodexExecutor:
    def __init__(self, command: str | None, timeout_seconds: int) -> None:
        self._command = (command or "").strip()
        self._timeout_seconds = timeout_seconds
        self._submitted: dict[str, _SubmittedTask] = {}

    def submit_fix_task(self, task: CodexFixTask) -> CodexTaskHandle:
        self._submitted[task.task_id] = _SubmittedTask(task=task)
        return CodexTaskHandle(task_id=task.task_id)

    def wait_for_result(self, handle: CodexTaskHandle) -> CodexExecutionResult:
        submitted = self._submitted.get(handle.task_id)
        if submitted is None:
            return CodexExecutionResult(CodexExecutionStatus.malformed, False, "unknown-task")
        if not self._command:
            return CodexExecutionResult(CodexExecutionStatus.failed, False, "codex-command-not-configured")

        prompt_path = Path(".autofix-bot") / f"codex-task-{handle.task_id}.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(submitted.task.prompt, encoding="utf-8")

        env = os.environ.copy()
        # Explicitly preserve OPENAI_API_KEY so the Codex subprocess always
        # receives it.  os.environ.copy() already includes it when present, but
        # the explicit assignment makes the dependency visible and ensures it
        # cannot be accidentally dropped by future refactors.
        if "OPENAI_API_KEY" in os.environ:
            env["OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]
        env["CODEX_TASK_FILE"] = str(prompt_path)

        # Safe diagnostics — values are never logged.
        # Use shlex.split for shell-aware tokenization so that quoted values
        # (e.g. SECRET='top secret' codex …) are handled correctly before we
        # skip leading KEY=value env-prefix tokens to find the binary name.
        try:
            _tokens = shlex.split(self._command) if self._command else []
        except ValueError:
            _tokens = []
        _bin = next(
            (t for t in _tokens if not ("=" in t and t.split("=", 1)[0].replace("_", "").isalnum())),
            "(none)",
        )
        logger.debug(
            "codex executor launch: binary=%r OPENAI_API_KEY_present=%s CODEX_TASK_FILE=%s",
            _bin,
            "OPENAI_API_KEY" in env,
            env.get("CODEX_TASK_FILE"),
        )

        try:
            proc = subprocess.run(
                self._command,
                shell=True,
                check=False,
                timeout=self._timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return CodexExecutionResult(CodexExecutionStatus.timeout, False, "codex-timeout")

        if proc.returncode != 0:
            return CodexExecutionResult(CodexExecutionStatus.failed, False, f"codex-command-exit-{proc.returncode}")

        return CodexExecutionResult(CodexExecutionStatus.succeeded, True, "codex-command-succeeded")

    def apply_or_confirm_branch_update(self, handle: CodexTaskHandle, result: CodexExecutionResult) -> CodexApplyResult:
        del handle
        if result.status != CodexExecutionStatus.succeeded:
            return CodexApplyResult(changed=False, branch_updated=False, summary=result.summary)
        return CodexApplyResult(changed=True, branch_updated=False, summary=result.summary)


def build_executor(command: str | None, timeout_seconds: int) -> CodexExecutor:
    return LocalSubprocessCodexExecutor(command=command, timeout_seconds=timeout_seconds)
