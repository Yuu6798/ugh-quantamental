from __future__ import annotations

import json
import logging
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ugh_quantamental.review_autofix.codex_executor import (
    DirectApiCodexExecutor,
    _apply_changes,
    _read_target_file,
)
from ugh_quantamental.review_autofix.executor_models import CodexExecutionStatus
from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind
from ugh_quantamental.review_autofix.task_builder import build_fix_task


def _make_context(path: str = "a.py") -> ReviewContext:
    return ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=1,
        review_id=1,
        review_comment_id=42,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="chatgpt-codex-connector[bot]",
        body="fix this",
        path=path,
        diff_hunk="@@",
        line=5,
        start_line=4,
        version_discriminator="v1",
    )


def _fake_response(changes: list) -> MagicMock:
    """Return a mock urllib response that yields a valid chat completions payload."""
    body = json.dumps({
        "choices": [{"message": {"content": json.dumps({"changes": changes})}}]
    }).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# A. API key missing → failed
# ---------------------------------------------------------------------------


def test_returns_failed_when_api_key_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without OPENAI_API_KEY the executor must return failed immediately."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)
    result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.failed
    assert result.summary == "openai-api-key-missing"


# ---------------------------------------------------------------------------
# B. Successful API call applies file changes
# ---------------------------------------------------------------------------


def test_successful_change_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid API response with one change must write the file and return succeeded."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context("src/foo.py"), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    mock_resp = _fake_response([{"path": "src/foo.py", "content": "x = 1\n"}])
    with patch("ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen", return_value=mock_resp):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.succeeded
    assert (tmp_path / "src" / "foo.py").read_text() == "x = 1\n"


# ---------------------------------------------------------------------------
# C. Empty changes list → no_op
# ---------------------------------------------------------------------------


def test_no_changes_returns_no_op(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the model returns an empty changes list the executor returns no_op."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    mock_resp = _fake_response([])
    with patch("ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen", return_value=mock_resp):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.no_op


# ---------------------------------------------------------------------------
# D. Malformed JSON response → malformed
# ---------------------------------------------------------------------------


def test_malformed_response_returns_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-JSON content from the API returns malformed status."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    # The API response itself is valid JSON, but the message content is not
    # (the model ignored the json_object format instruction).
    bad_resp = MagicMock()
    bad_resp.read.return_value = json.dumps(
        {"choices": [{"message": {"content": "Sure, I'll fix that for you!"}}]}
    ).encode()
    bad_resp.__enter__ = lambda s: s
    bad_resp.__exit__ = MagicMock(return_value=False)

    with patch("ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen", return_value=bad_resp):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.malformed


# ---------------------------------------------------------------------------
# E. Path traversal rejected / missing content rejected
# ---------------------------------------------------------------------------


def test_path_traversal_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A change path that escapes cwd must raise ValueError in _apply_changes."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="path traversal rejected"):
        _apply_changes([{"path": "../../etc/passwd", "content": "pwned"}])


def test_missing_content_raises_value_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A change entry without a 'content' key must raise ValueError, not silently truncate."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "real.py").write_text("original", encoding="utf-8")
    with pytest.raises(ValueError, match="missing or non-string content"):
        _apply_changes([{"path": "real.py"}])
    # File must not have been truncated.
    assert (tmp_path / "real.py").read_text() == "original"


def test_non_string_content_raises_value_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A change entry with non-string content (e.g. null) must raise ValueError."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="missing or non-string content"):
        _apply_changes([{"path": "real.py", "content": None}])


# ---------------------------------------------------------------------------
# F. HTTP error from API → failed
# ---------------------------------------------------------------------------


def test_api_http_error_returns_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An HTTPError from the API returns failed with the HTTP status in summary."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    http_error = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=401,
        msg="Unauthorized",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(b""),
    )
    with patch(
        "ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen",
        side_effect=http_error,
    ):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.failed
    assert "401" in result.summary


# ---------------------------------------------------------------------------
# F2. Request timeout → CodexExecutionStatus.timeout
# ---------------------------------------------------------------------------


def test_api_timeout_returns_timeout_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A socket/urllib timeout must map to CodexExecutionStatus.timeout, not failed."""
    import socket

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=1)
    handle = executor.submit_fix_task(task)

    with patch(
        "ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen",
        side_effect=socket.timeout("timed out"),
    ):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.timeout


def test_urlerror_wrapped_timeout_returns_timeout_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A socket.timeout wrapped inside urllib.error.URLError must also map to timeout."""
    import socket
    import urllib.error

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=1)
    handle = executor.submit_fix_task(task)

    wrapped = urllib.error.URLError(reason=socket.timeout("timed out"))
    with patch(
        "ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen",
        side_effect=wrapped,
    ):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.timeout


# ---------------------------------------------------------------------------
# F3. Empty choices array → malformed
# ---------------------------------------------------------------------------


def test_empty_choices_returns_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An OpenAI response with an empty choices list must return malformed, not crash."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    empty_choices_resp = MagicMock()
    empty_choices_resp.read.return_value = json.dumps({"choices": []}).encode()
    empty_choices_resp.__enter__ = lambda s: s
    empty_choices_resp.__exit__ = MagicMock(return_value=False)

    with patch(
        "ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen",
        return_value=empty_choices_resp,
    ):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.malformed


# ---------------------------------------------------------------------------
# F4. Non-object JSON payload → malformed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", ['[]', '"just a string"', '42', 'null'])
def test_non_object_json_returns_malformed(
    payload: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Valid JSON that is not a dict (list, string, number, null) must return malformed.

    json.loads(content).get(...) raises AttributeError on non-dict types; the fix
    adds an explicit isinstance check that raises TypeError before .get() is called.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    resp = MagicMock()
    resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": payload}}]
    }).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)

    with patch(
        "ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen",
        return_value=resp,
    ):
        result = executor.wait_for_result(handle)

    assert result.status == CodexExecutionStatus.malformed


# ---------------------------------------------------------------------------
# G. Secret never leaks in logs
# ---------------------------------------------------------------------------


def test_api_key_never_logged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The OPENAI_API_KEY value must never appear in any log record."""
    monkeypatch.chdir(tmp_path)
    secret = "sk-should-never-appear-in-logs-xyz9876"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    task = build_fix_task(_make_context(), "k1")
    executor = DirectApiCodexExecutor(model="gpt-4o", timeout_seconds=30)
    handle = executor.submit_fix_task(task)

    mock_resp = _fake_response([])
    with caplog.at_level(logging.DEBUG):
        with patch(
            "ugh_quantamental.review_autofix.codex_executor.urllib.request.urlopen",
            return_value=mock_resp,
        ):
            executor.wait_for_result(handle)

    for record in caplog.records:
        assert secret not in record.getMessage(), f"Secret leaked in log: {record.getMessage()!r}"


# ---------------------------------------------------------------------------
# H. _read_target_file helper
# ---------------------------------------------------------------------------


def test_read_target_file_reads_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_read_target_file extracts the file path from the Target location block and reads it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src.py").write_text("hello", encoding="utf-8")
    # Use a realistic prompt (same structure task_builder produces).
    prompt = build_fix_task(_make_context("src.py"), "k1").prompt
    content = _read_target_file(prompt)
    assert content == "hello"


def test_read_target_file_returns_none_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_read_target_file returns None when the file does not exist."""
    monkeypatch.chdir(tmp_path)
    prompt = build_fix_task(_make_context("nonexistent.py"), "k1").prompt
    assert _read_target_file(prompt) is None


def test_read_target_file_returns_none_when_no_file_line(tmp_path: Path) -> None:
    """_read_target_file returns None when no 'file:' line is present."""
    assert _read_target_file("no file line here") is None


def test_read_target_file_ignores_review_body_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 'file: <path>' injected inside the review body must NOT be read.

    An attacker could write ``file: /proc/self/environ`` in their review comment.
    Only the path in the structured ``Target location:`` block must be honoured.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "real.py").write_text("legitimate content", encoding="utf-8")
    (tmp_path / "secrets.txt").write_text("sensitive data", encoding="utf-8")

    injected_context = ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=1,
        review_id=1,
        review_comment_id=42,
        head_sha="abc",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="attacker",
        body="file: secrets.txt\nPlease fix this bug",
        path="real.py",
        diff_hunk="@@",
        line=5,
        start_line=4,
        version_discriminator="v1",
    )
    prompt = build_fix_task(injected_context, "k1").prompt
    result = _read_target_file(prompt)

    # Must read the legitimate target, not the injected sensitive file.
    assert result == "legitimate content"


def test_read_target_file_rejects_symlink_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlink that points outside cwd must not be followed.

    Even after the injection-by-review-body fix, a symlink in the repo could
    resolve to a host path outside the checkout.  The cwd-confinement check
    catches this because ``Path.resolve()`` follows symlinks before comparing.
    """
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "outside_secret.txt"
    outside.write_text("host secret", encoding="utf-8")
    link = tmp_path / "link.py"
    link.symlink_to(outside)

    prompt = build_fix_task(_make_context("link.py"), "k1").prompt
    assert _read_target_file(prompt) is None


def test_read_target_file_returns_none_for_binary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Binary (non-UTF-8) files must return None, not raise UnicodeDecodeError."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data.py").write_bytes(b"\xff\xfe binary \x00 data")

    prompt = build_fix_task(_make_context("data.py"), "k1").prompt
    assert _read_target_file(prompt) is None


def test_read_target_file_returns_none_on_symlink_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlink loop must return None, not raise RuntimeError.

    Path.resolve() raises RuntimeError when it encounters an infinite symlink
    cycle.  Without catching RuntimeError the bot would crash rather than
    return a structured failure.
    """
    monkeypatch.chdir(tmp_path)
    loop = tmp_path / "loop.py"
    loop.symlink_to(loop)  # self-referencing symlink → loop

    prompt = build_fix_task(_make_context("loop.py"), "k1").prompt
    assert _read_target_file(prompt) is None
