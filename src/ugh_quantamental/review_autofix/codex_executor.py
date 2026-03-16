from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .executor_models import CodexApplyResult, CodexExecutionResult, CodexExecutionStatus, CodexFixTask, CodexTaskHandle

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an automated code fixer working inside a git checkout.
Apply the minimal fix described in the review finding.
You MUST respond with ONLY a JSON object in this exact format:
{"changes": [{"path": "relative/path/to/file", "content": "...complete new file content..."}]}
Use the exact file path from the "Target location: file:" line in the task.
Do not add explanations, markdown fences, or extra keys.
If no code change is needed, return: {"changes": []}
"""


class CodexExecutor(Protocol):
    def submit_fix_task(self, task: CodexFixTask) -> CodexTaskHandle: ...

    def wait_for_result(self, handle: CodexTaskHandle) -> CodexExecutionResult: ...

    def apply_or_confirm_branch_update(self, handle: CodexTaskHandle, result: CodexExecutionResult) -> CodexApplyResult: ...


@dataclass(frozen=True)
class _SubmittedTask:
    task: CodexFixTask


class DirectApiCodexExecutor:
    """Calls the OpenAI chat completions API directly to generate and apply code fixes.

    Uses ``/v1/chat/completions`` with JSON mode.  The model returns a structured
    ``{"changes": [...]}`` object; this executor writes the changed files to disk.
    No external CLI dependency — authentication is read from ``OPENAI_API_KEY``.
    """

    def __init__(self, model: str, timeout_seconds: int) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._submitted: dict[str, _SubmittedTask] = {}

    def submit_fix_task(self, task: CodexFixTask) -> CodexTaskHandle:
        self._submitted[task.task_id] = _SubmittedTask(task=task)
        return CodexTaskHandle(task_id=task.task_id)

    def wait_for_result(self, handle: CodexTaskHandle) -> CodexExecutionResult:
        submitted = self._submitted.get(handle.task_id)
        if submitted is None:
            return CodexExecutionResult(CodexExecutionStatus.malformed, False, "unknown-task")

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return CodexExecutionResult(CodexExecutionStatus.failed, False, "openai-api-key-missing")

        task = submitted.task
        user_content = _build_user_content(task)

        logger.debug(
            "api executor: model=%r task_id=%r OPENAI_API_KEY_present=True",
            self._model,
            task.task_id,
        )

        try:
            response = _call_openai_chat(
                api_key=api_key,
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                timeout=self._timeout_seconds,
            )
        except urllib.error.HTTPError as exc:
            logger.warning("api executor: HTTP %s from OpenAI", exc.code)
            return CodexExecutionResult(CodexExecutionStatus.failed, False, f"api-http-{exc.code}")
        except Exception as exc:
            logger.warning("api executor: request failed: %s", exc)
            return CodexExecutionResult(CodexExecutionStatus.failed, False, "api-call-failed")

        try:
            content = response["choices"][0]["message"]["content"]
            changes = json.loads(content).get("changes", [])
        except (KeyError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("api executor: malformed response: %s", exc)
            return CodexExecutionResult(CodexExecutionStatus.malformed, False, "malformed-api-response")

        if not changes:
            return CodexExecutionResult(CodexExecutionStatus.no_op, False, "no-changes")

        try:
            _apply_changes(changes)
        except Exception as exc:
            logger.warning("api executor: apply failed: %s", exc)
            return CodexExecutionResult(CodexExecutionStatus.failed, False, f"apply-failed: {exc}")

        return CodexExecutionResult(CodexExecutionStatus.succeeded, True, "api-executor-succeeded")

    def apply_or_confirm_branch_update(
        self, handle: CodexTaskHandle, result: CodexExecutionResult
    ) -> CodexApplyResult:
        del handle
        if result.status != CodexExecutionStatus.succeeded:
            return CodexApplyResult(changed=False, branch_updated=False, summary=result.summary)
        return CodexApplyResult(changed=True, branch_updated=False, summary=result.summary)


def _build_user_content(task: CodexFixTask) -> str:
    """Append current target file content to the task prompt for context."""
    file_content = _read_target_file(task.prompt)
    if file_content is None:
        return task.prompt
    return f"{task.prompt}\n\nCurrent file content:\n```\n{file_content}\n```"


def _read_target_file(prompt: str) -> str | None:
    """Extract the target file path from the 'Target location:' block only.

    Scanning the whole prompt is unsafe: the review body (user-supplied text) comes
    after ``Review finding:`` and could contain ``file: /proc/self/environ`` or any
    other path, causing arbitrary local files to be forwarded to the OpenAI API.
    Restricting the search to the structured ``Target location:`` block (which is
    generated by ``task_builder`` from sanitised ``ReviewContext.path``) eliminates
    that injection vector.
    """
    block_match = re.search(
        r"^Target location:\n(.*?)(?=\n\n|\Z)",
        prompt,
        re.MULTILINE | re.DOTALL,
    )
    if not block_match:
        return None
    block = block_match.group(1)
    file_match = re.search(r"^file: (.+)$", block, re.MULTILINE)
    if not file_match:
        return None
    file_path = file_match.group(1).strip()
    try:
        cwd = Path.cwd().resolve()
        target = (cwd / file_path).resolve()
        # Reject symlinks or paths that resolve outside the checkout root.
        if not (str(target) + os.sep).startswith(str(cwd) + os.sep):
            return None
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _apply_changes(changes: list[dict]) -> None:
    """Write file changes to disk; rejects path traversal outside cwd."""
    cwd = Path.cwd().resolve()
    for change in changes:
        raw_path = change.get("path", "")
        content = change.get("content", "")
        if not raw_path or not isinstance(raw_path, str):
            raise ValueError(f"invalid path: {raw_path!r}")
        target = (cwd / raw_path).resolve()
        if not (str(target) + os.sep).startswith(str(cwd) + os.sep):
            raise ValueError(f"path traversal rejected: {raw_path!r}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _call_openai_chat(api_key: str, model: str, messages: list, timeout: int) -> dict:
    """POST to /v1/chat/completions with JSON-mode response format."""
    data = json.dumps({
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def build_executor(model: str, timeout_seconds: int) -> CodexExecutor:
    """Return a ``DirectApiCodexExecutor`` for the given model and timeout."""
    return DirectApiCodexExecutor(model=model, timeout_seconds=timeout_seconds)
