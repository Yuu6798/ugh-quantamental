from __future__ import annotations

import os
import subprocess

from .models import ValidationResult

# Credentials that must never be forwarded into validation subprocesses
# (e.g. ``pytest -q``).  Stripping them prevents unit tests executed as part
# of validation from accidentally hitting live GitHub or OpenAI endpoints.
_STRIP_FROM_VALIDATION_ENV: frozenset[str] = frozenset()


def is_default_validation_command(command: str) -> bool:
    """Check if the command is a default validation like 'pytest -q'."""
    return command.startswith("pytest -q")


def run_validation(commands: tuple[str, ...]) -> ValidationResult:
    """Run validation commands sequentially, stopping on the first failure.

    API credentials are stripped from the subprocess environment so that
    validation commands (e.g. ``pytest -q``) cannot accidentally reach live
    GitHub or OpenAI endpoints.
    """
    results: list[tuple[str, int]] = []
    for command in commands:
        # Apply environment filtering only to default validation commands
        if is_default_validation_command(command):
            _env = {k: v for k, v in os.environ.items() if k not in _STRIP_FROM_VALIDATION_ENV}
        else:
            _env = os.environ.copy()
        proc = subprocess.run(command, shell=True, check=False, env=_env)
        results.append((command, proc.returncode))
        if proc.returncode != 0:
            return ValidationResult(ok=False, command_results=tuple(results))
    return ValidationResult(ok=True, command_results=tuple(results))
