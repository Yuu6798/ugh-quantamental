from __future__ import annotations

import logging
import os

from .classifier import classify_review
from .codex_executor import build_executor
from .config import BotConfig, load_config
from .executor_models import CodexExecutionStatus
from .git_ops import commit_changes, has_changes, push_head_branch
from .github_client import GithubClient, build_review_context, is_review_event, load_event_from_env
from .models import Classification, ProcessResult
from .state_store import FileStateStore
from .task_builder import build_fix_task
from .validator import run_validation

_VALID_BOT_MODES = {"detect_only", "propose_only", "apply_and_push", "apply_push_and_resolve"}


def should_process_actor(login: str | None, config: BotConfig) -> bool:
    logging.debug(
        "review_autofix actor_check: login=%r allowed_bot_reviewers=%r self_bot_actors=%r",
        login,
        config.allowed_bot_reviewers,
        config.self_bot_actors,
    )
    if not login:
        return False
    if login in config.self_bot_actors:
        return False
    return login in config.allowed_bot_reviewers


def _processed_key(context) -> str:
    if context.review_comment_id is not None:
        return f"review_comment:{context.review_comment_id}:{context.head_sha}:{context.version_discriminator}"
    return f"review:{context.review_id}:{context.head_sha}:{context.version_discriminator}"


def _reply(client: GithubClient, context, body: str) -> None:
    if context.review_comment_id is not None:
        client.reply_to_review_comment(context.repository, context.review_comment_id, body)
    else:
        client.reply_to_pr(context.repository, context.pr_number, body)


def _dedupe_marker(key: str) -> str:
    return f"<!-- review-autofix-key:{key} -->"


def run() -> ProcessResult:
    config = load_config()
    logging.basicConfig(level=config.log_level)
    event = load_event_from_env()

    if not is_review_event(event):
        return ProcessResult("event:unsupported", Classification.skip, None, False, False, False, False, "unsupported-event")

    try:
        context = build_review_context(event)
    except ValueError:
        return ProcessResult("event:invalid", Classification.skip, None, False, False, False, False, "invalid-event-payload")

    if not should_process_actor(context.reviewer_login, config):
        return ProcessResult("actor:ignored", Classification.skip, None, False, False, False, False, "ignored-actor")

    if config.bot_mode not in _VALID_BOT_MODES:
        return ProcessResult("mode:invalid", Classification.skip, None, False, False, False, False, "invalid-bot-mode")

    if config.bot_mode in {"apply_and_push", "apply_push_and_resolve"} and not config.target_reviewers:
        return ProcessResult("reviewer:missing-allowlist", Classification.skip, None, False, False, False, False, "reviewer-allowlist-required")

    state = FileStateStore(os.getenv("STATE_STORE_PATH", ".autofix-bot/state.json"))
    key = _processed_key(context)
    marker = _dedupe_marker(key)
    token = os.getenv("GITHUB_TOKEN", "")
    client = GithubClient(token) if token else None

    if client is not None and client.has_processed_marker(context, marker):
        return ProcessResult(key, Classification.skip, None, False, False, False, False, "duplicate")

    if state.seen(key):
        return ProcessResult(key, Classification.skip, None, False, False, False, False, "duplicate")

    if config.target_reviewers and (context.reviewer_login or "") not in config.target_reviewers:
        return ProcessResult(key, Classification.skip, None, False, False, False, False, "reviewer-filter")

    classification = classify_review(context)
    if classification == Classification.skip:
        state.mark(key)
        return ProcessResult(key, classification, None, False, False, False, False, "skip")

    if not context.same_repo and not config.allow_push_on_fork:
        classification = Classification.propose_only

    task = build_fix_task(context, key)
    changed = False
    pushed = False
    validation_ok = False
    reason = "skip"

    if config.bot_mode in {"detect_only"}:
        reason = "detect-only"
    elif config.bot_mode in {"propose_only"} or config.dry_run or classification == Classification.propose_only:
        reason = "proposed-only"
    else:
        executor = build_executor(command=config.codex_command, timeout_seconds=config.codex_timeout_seconds)
        handle = executor.submit_fix_task(task)
        result = executor.wait_for_result(handle)
        apply_result = executor.apply_or_confirm_branch_update(handle, result)
        changed = apply_result.changed

        if result.status == CodexExecutionStatus.timeout:
            reason = "codex-timeout"
        elif result.status == CodexExecutionStatus.malformed:
            reason = "codex-malformed-response"
        elif result.status == CodexExecutionStatus.failed:
            reason = apply_result.summary or "codex-failed"
        elif result.status == CodexExecutionStatus.no_op or not changed:
            reason = "codex-no-op"
        elif not has_changes() and not apply_result.branch_updated:
            reason = "no-change-after-codex"
        else:
            validation = run_validation(config.all_validation_commands)
            validation_ok = validation.ok
            if not validation_ok:
                reason = "validation-failed"
            else:
                if has_changes():
                    commit_changes(f"AUTO: apply codex fix task for PR #{context.pr_number} ({key})")
                    push_head_branch(context.head_ref)
                    pushed = True
                    reason = "pushed"
                elif apply_result.branch_updated:
                    pushed = True
                    reason = "pushed"
                else:
                    reason = "no-change-after-validation"

    replied = False
    if client is not None:
        nonfatal_comment_writes = (reason != "pushed") and (classification == Classification.propose_only) and (not context.same_repo)
        if reason == "pushed" and config.bot_mode == "apply_push_and_resolve" and config.auto_resolve and context.review_comment_node_id:
            try:
                client.resolve_review_thread(context.review_comment_node_id)
            except Exception:
                logging.exception("failed to resolve review thread")
        if reason == "pushed" and config.reply_on_success:
            try:
                _reply(
                    client,
                    context,
                    f"✅ Codex fix applied and pushed to `{context.head_ref}`.\n\n{marker}",
                )
                replied = True
            except Exception:
                logging.exception("failed to post success reply")
        if reason == "pushed" and not replied:
            client.persist_marker(context, marker)
        if reason != "pushed" and config.reply_on_failure:
            try:
                _reply(client, context, f"ℹ️ Codex autofix processed: {reason}. No push was performed.\n\n{marker}")
                replied = True
            except Exception:
                if not nonfatal_comment_writes:
                    raise

    state.mark(key)
    return ProcessResult(key, classification, "codex-task", changed, validation_ok, pushed, replied, reason)


if __name__ == "__main__":
    result = run()
    print(result)
