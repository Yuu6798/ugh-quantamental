from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    bot_mode: str
    target_reviewers: tuple[str, ...]
    allowed_bot_reviewers: tuple[str, ...]
    self_bot_actors: tuple[str, ...]
    dry_run: bool
    allow_push_on_fork: bool
    validation_format_commands: tuple[str, ...]
    validation_lint_commands: tuple[str, ...]
    validation_typecheck_commands: tuple[str, ...]
    validation_test_commands: tuple[str, ...]
    reply_on_success: bool
    reply_on_failure: bool
    auto_resolve: bool
    log_level: str

    @property
    def all_validation_commands(self) -> tuple[str, ...]:
        return (
            *self.validation_format_commands,
            *self.validation_lint_commands,
            *self.validation_typecheck_commands,
            *self.validation_test_commands,
        )


def _parse_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(name: str, default: str = "") -> tuple[str, ...]:
    raw = os.getenv(name, default)
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _parse_multiline(name: str, default: str = "") -> tuple[str, ...]:
    raw = os.getenv(name, default)
    return tuple(line.strip() for line in raw.splitlines() if line.strip())


def load_config() -> BotConfig:
    return BotConfig(
        bot_mode=os.getenv("BOT_MODE", "detect_only"),
        target_reviewers=_parse_csv("TARGET_REVIEWERS"),
        allowed_bot_reviewers=_parse_csv("ALLOWED_BOT_REVIEWERS"),
        self_bot_actors=_parse_csv("SELF_BOT_ACTORS", "github-actions[bot],chatgpt-codex-connector[bot]"),
        dry_run=_parse_bool("DRY_RUN", True),
        allow_push_on_fork=_parse_bool("ALLOW_PUSH_ON_FORK", False),
        validation_format_commands=_parse_multiline("VALIDATION_FORMAT_COMMANDS"),
        validation_lint_commands=_parse_multiline("VALIDATION_LINT_COMMANDS", "ruff check ."),
        validation_typecheck_commands=_parse_multiline("VALIDATION_TYPECHECK_COMMANDS"),
        validation_test_commands=_parse_multiline("VALIDATION_TEST_COMMANDS", "pytest -q"),
        reply_on_success=_parse_bool("REPLY_ON_SUCCESS", True),
        reply_on_failure=_parse_bool("REPLY_ON_FAILURE", True),
        auto_resolve=_parse_bool("AUTO_RESOLVE", False),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
