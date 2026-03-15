from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from ugh_quantamental.review_autofix.codex_executor import LocalSubprocessCodexExecutor
from ugh_quantamental.review_autofix.executor_models import CodexExecutionStatus
from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind
from ugh_quantamental.review_autofix.task_builder import build_fix_task


def _make_context() -> ReviewContext:
    return ReviewContext(
        kind=ReviewKind.review_body,
        repository="acme/repo",
        pr_number=1,
        review_id=1,
        review_comment_id=None,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="chatgpt-codex-connector[bot]",
        body="fix this",
        path="a.py",
        diff_hunk=None,
        line=None,
        start_line=None,
        version_discriminator="v1",
    )


def _fake_run_ok(*_args, **kwargs) -> MagicMock:
    m = MagicMock()
    m.returncode = 0
    return m


# ---------------------------------------------------------------------------
# A. OPENAI_API_KEY is passed into the subprocess env
# ---------------------------------------------------------------------------


def test_executor_passes_openai_api_key_when_present(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """OPENAI_API_KEY must appear in the env dict forwarded to subprocess.run."""
    import pathlib

    monkeypatch.chdir(pathlib.Path(str(tmp_path)))  # type: ignore[arg-type]
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-abc123")

    captured: dict[str, str] = {}

    def _capture(*_args, **kwargs):
        captured.update(kwargs.get("env") or {})
        return _fake_run_ok()

    task = build_fix_task(_make_context(), "k1")
    executor = LocalSubprocessCodexExecutor(command="true", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    with patch("ugh_quantamental.review_autofix.codex_executor.subprocess.run", side_effect=_capture):
        executor.wait_for_result(handle)

    assert "OPENAI_API_KEY" in captured
    assert captured["OPENAI_API_KEY"] == "test-key-abc123"


def test_executor_omits_openai_api_key_when_absent(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """When OPENAI_API_KEY is not in the parent env it must not appear in the child env."""
    import pathlib

    monkeypatch.chdir(pathlib.Path(str(tmp_path)))  # type: ignore[arg-type]
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    captured: dict[str, str] = {}

    def _capture(*_args, **kwargs):
        captured.update(kwargs.get("env") or {})
        return _fake_run_ok()

    task = build_fix_task(_make_context(), "k1")
    executor = LocalSubprocessCodexExecutor(command="true", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    with patch("ugh_quantamental.review_autofix.codex_executor.subprocess.run", side_effect=_capture):
        result = executor.wait_for_result(handle)

    # executor must not crash when the key is absent
    assert result.status == CodexExecutionStatus.succeeded
    assert "OPENAI_API_KEY" not in captured


# ---------------------------------------------------------------------------
# B. Secret value never appears in log output
# ---------------------------------------------------------------------------


def test_executor_does_not_log_api_key_value(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The OPENAI_API_KEY value must never appear in any log record."""
    import pathlib

    monkeypatch.chdir(pathlib.Path(str(tmp_path)))  # type: ignore[arg-type]
    secret = "sk-should-never-appear-in-logs-xyz9876"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    task = build_fix_task(_make_context(), "k1")
    executor = LocalSubprocessCodexExecutor(command="true", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    with caplog.at_level(logging.DEBUG):
        with patch(
            "ugh_quantamental.review_autofix.codex_executor.subprocess.run", side_effect=_fake_run_ok
        ):
            executor.wait_for_result(handle)

    for record in caplog.records:
        assert secret not in record.getMessage(), f"Secret leaked in log: {record.getMessage()!r}"


# ---------------------------------------------------------------------------
# C. CODEX_TASK_FILE is injected and points to the written prompt file
# ---------------------------------------------------------------------------


def test_executor_injects_codex_task_file(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """CODEX_TASK_FILE must be present in env and point to an existing .txt file."""
    import pathlib

    monkeypatch.chdir(pathlib.Path(str(tmp_path)))  # type: ignore[arg-type]

    captured: dict[str, str] = {}

    def _capture(*_args, **kwargs):
        captured.update(kwargs.get("env") or {})
        return _fake_run_ok()

    task = build_fix_task(_make_context(), "k1")
    executor = LocalSubprocessCodexExecutor(command="true", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    with patch("ugh_quantamental.review_autofix.codex_executor.subprocess.run", side_effect=_capture):
        executor.wait_for_result(handle)

    assert "CODEX_TASK_FILE" in captured
    task_file = pathlib.Path(captured["CODEX_TASK_FILE"])
    assert task_file.suffix == ".txt"
    assert task_file.exists()
    assert len(task_file.read_text(encoding="utf-8")) > 0


# ---------------------------------------------------------------------------
# D. Command launch behavior remains intact
# ---------------------------------------------------------------------------


def test_executor_passes_command_string_to_shell(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """The exact command string must be forwarded to subprocess.run with shell=True."""
    import pathlib

    monkeypatch.chdir(pathlib.Path(str(tmp_path)))  # type: ignore[arg-type]

    captured_cmd: list[str] = []
    captured_shell: list[bool] = []

    def _capture(cmd, **kwargs):
        captured_cmd.append(cmd)
        captured_shell.append(kwargs.get("shell", False))
        return _fake_run_ok()

    cmd = 'echo "test-command"'
    task = build_fix_task(_make_context(), "k1")
    executor = LocalSubprocessCodexExecutor(command=cmd, timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    with patch("ugh_quantamental.review_autofix.codex_executor.subprocess.run", side_effect=_capture):
        executor.wait_for_result(handle)

    assert captured_cmd == [cmd]
    assert captured_shell == [True]


def test_executor_debug_log_shows_binary_not_key(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Debug log must mention binary name and key presence flag — never the key value."""
    import pathlib

    monkeypatch.chdir(pathlib.Path(str(tmp_path)))  # type: ignore[arg-type]
    secret = "sk-debuglog-should-not-leak-abc"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    task = build_fix_task(_make_context(), "k1")
    executor = LocalSubprocessCodexExecutor(command="mycodex exec ...", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    # Attach a handler directly to the module logger so root-logger level
    # settings from other tests (e.g. logging.basicConfig(WARNING)) cannot
    # prevent DEBUG records from being captured.
    # Also reset `disabled` in case alembic's fileConfig (disable_existing_loggers=True)
    # ran earlier in the suite and silently disabled this logger.
    _module_logger = logging.getLogger("ugh_quantamental.review_autofix.codex_executor")
    _records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            _records.append(record)

    handler = _Capture(level=logging.DEBUG)
    _orig_level = _module_logger.level
    _orig_disabled = _module_logger.disabled
    _module_logger.disabled = False
    _module_logger.setLevel(logging.DEBUG)
    _module_logger.addHandler(handler)
    try:
        with patch(
            "ugh_quantamental.review_autofix.codex_executor.subprocess.run",
            side_effect=_fake_run_ok,
        ):
            executor.wait_for_result(handle)
    finally:
        _module_logger.removeHandler(handler)
        _module_logger.setLevel(_orig_level)
        _module_logger.disabled = _orig_disabled

    debug_messages = [r.getMessage() for r in _records if r.levelno == logging.DEBUG]
    assert any("mycodex" in m for m in debug_messages), "binary name should appear in debug log"
    assert any("OPENAI_API_KEY_present=True" in m for m in debug_messages), "key presence flag should appear"
    for msg in debug_messages:
        assert secret not in msg, f"Secret leaked in debug log: {msg!r}"
