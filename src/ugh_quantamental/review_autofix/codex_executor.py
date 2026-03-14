from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .executor_models import CodexApplyResult, CodexExecutionResult, CodexExecutionStatus, CodexFixTask, CodexTaskHandle


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
        env["CODEX_TASK_FILE"] = str(prompt_path)
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
