from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ugh_quantamental.review_autofix.validator import (
    _STRIP_FROM_VALIDATION_ENV,
    run_validation,
)


# ---------------------------------------------------------------------------
# _STRIP_FROM_VALIDATION_ENV contract
# ---------------------------------------------------------------------------


def test_strip_set_contains_github_token() -> None:
    assert "GITHUB_TOKEN" in _STRIP_FROM_VALIDATION_ENV


def test_strip_set_contains_openai_api_key() -> None:
    assert "OPENAI_API_KEY" in _STRIP_FROM_VALIDATION_ENV


def test_strip_set_is_nonempty() -> None:
    assert len(_STRIP_FROM_VALIDATION_ENV) > 0


# ---------------------------------------------------------------------------
# run_validation: credential stripping
# ---------------------------------------------------------------------------


def test_github_token_absent_in_subprocess_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """GITHUB_TOKEN must never be forwarded into the validation subprocess."""
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    captured: dict[str, object] = {}

    def _fake_run(
        cmd: str, *, shell: bool, check: bool, env: dict[str, str]
    ) -> MagicMock:
        captured["env"] = env.copy()
        m = MagicMock()
        m.returncode = 0
        return m

    with patch.object(subprocess, "run", side_effect=_fake_run):
        run_validation(("true",))

    assert "GITHUB_TOKEN" not in captured["env"]


def test_openai_api_key_absent_in_subprocess_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPENAI_API_KEY must never be forwarded into the validation subprocess."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    captured: dict[str, object] = {}

    def _fake_run(
        cmd: str, *, shell: bool, check: bool, env: dict[str, str]
    ) -> MagicMock:
        captured["env"] = env.copy()
        m = MagicMock()
        m.returncode = 0
        return m

    with patch.object(subprocess, "run", side_effect=_fake_run):
        run_validation(("true",))

    assert "OPENAI_API_KEY" not in captured["env"]


def test_all_strip_keys_absent_in_subprocess_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every key in _STRIP_FROM_VALIDATION_ENV must be absent from the subprocess env."""
    for key in _STRIP_FROM_VALIDATION_ENV:
        monkeypatch.setenv(key, f"dummy-value-for-{key}")

    captured: dict[str, object] = {}

    def _fake_run(
        cmd: str, *, shell: bool, check: bool, env: dict[str, str]
    ) -> MagicMock:
        captured["env"] = env.copy()
        m = MagicMock()
        m.returncode = 0
        return m

    with patch.object(subprocess, "run", side_effect=_fake_run):
        run_validation(("true",))

    for key in _STRIP_FROM_VALIDATION_ENV:
        assert key not in captured["env"], f"{key} must be stripped from subprocess env"


# ---------------------------------------------------------------------------
# run_validation: result contract
# ---------------------------------------------------------------------------


def test_single_passing_command_returns_ok() -> None:
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_validation(("true",))

    assert result.ok is True
    assert result.command_results == (("true", 0),)


def test_single_failing_command_returns_not_ok() -> None:
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = run_validation(("false",))

    assert result.ok is False
    assert result.command_results == (("false", 1),)


def test_stops_at_first_failure() -> None:
    """Commands after the first failure must not be executed."""
    call_count = 0

    def _fake_run(
        cmd: str, *, shell: bool, check: bool, env: dict[str, str]
    ) -> MagicMock:
        nonlocal call_count
        call_count += 1
        m = MagicMock()
        m.returncode = 1 if call_count == 1 else 0
        return m

    with patch.object(subprocess, "run", side_effect=_fake_run):
        result = run_validation(("fail-cmd", "should-not-run"))

    assert result.ok is False
    assert call_count == 1
    assert len(result.command_results) == 1


def test_empty_commands_returns_ok() -> None:
    result = run_validation(())
    assert result.ok is True
    assert result.command_results == ()
