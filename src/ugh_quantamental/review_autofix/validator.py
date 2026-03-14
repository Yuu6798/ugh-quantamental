from __future__ import annotations

import subprocess

from .models import ValidationResult


def run_validation(commands: tuple[str, ...]) -> ValidationResult:
    results: list[tuple[str, int]] = []
    for command in commands:
        proc = subprocess.run(command, shell=True, check=False)
        results.append((command, proc.returncode))
        if proc.returncode != 0:
            return ValidationResult(ok=False, command_results=tuple(results))
    return ValidationResult(ok=True, command_results=tuple(results))
