from __future__ import annotations

import logging
import os

from .classifier import classify_codex_review
from .codex_executor import build_executor
from .config import BotConfig, load_config
from .executor_models import CodexExecutionStatus
from .git_ops import commit_changes, has_changes, push_head_branch
from .github_client import (
    GithubClient,
    build_context_from_inline_comment,
    build_review_context,
    is_review_event,
    load_event_from_env,
)
from .models import Classification, ProcessResult, ReviewKind
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


def _process_classified_context(
    context,
    classification: Classification,
    config,
    client: GithubClient | None,
    state,
    key: str,
    marker: str,
) -> ProcessResult:
    """Execute codex, validate, commit/push, and reply for a context that has already been
    classified as non-skip.  Marks *key* in the state store before returning."""
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
        nonfatal_comment_writes = (
            (reason != "pushed") and (classification == Classification.propose_only) and (not context.same_repo)
        )
        if (
            reason == "pushed"
            and config.bot_mode == "apply_push_and_resolve"
            and config.auto_resolve
            and context.review_comment_node_id
        ):
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


def _run_review_body_inline_fallback(
    review_body_context,
    config,
    client: GithubClient,
    state,
    review_body_key: str,
) -> ProcessResult:
    """Fallback for a review_body event with no concrete path hint.

    Fetches inline diff comments that share the same review_id and processes each one
    independently (with per-comment dedupe, classification, and codex execution).  Returns
    the result of the last comment processed.  If no inline comments are found the
    review_body key is marked and a skip is returned with a descriptive reason.
    """
    review_id = review_body_context.review_id
    inline_comments = client.list_review_comments_for_review(
        review_body_context.repository, review_body_context.pr_number, review_id
    )

    if not inline_comments:
        logging.info(
            "review_autofix fallback: review_id=%s has no inline diff comments; skipping",
            review_id,
        )
        state.mark(review_body_key)
        return ProcessResult(
            review_body_key,
            Classification.skip,
            None,
            False,
            False,
            False,
            False,
            "review-body-no-path-no-inline-comments",
        )

    logging.info(
        "review_autofix fallback: review_id=%s expanded to %d inline comment(s)",
        review_id,
        len(inline_comments),
    )

    last_result: ProcessResult | None = None
    for comment in inline_comments:
        inline_ctx = build_context_from_inline_comment(review_body_context, comment)
        inline_key = _processed_key(inline_ctx)
        inline_marker = _dedupe_marker(inline_key)

        if client.has_processed_marker(inline_ctx, inline_marker) or state.seen(inline_key):
            logging.debug("review_autofix fallback: inline comment %s already processed", inline_key)
            last_result = ProcessResult(
                inline_key, Classification.skip, None, False, False, False, False, "duplicate"
            )
            continue

        if config.target_reviewers and (inline_ctx.reviewer_login or "") not in config.target_reviewers:
            last_result = ProcessResult(
                inline_key, Classification.skip, None, False, False, False, False, "reviewer-filter"
            )
            continue

        inline_classification = classify_codex_review(inline_ctx)
        if inline_classification == Classification.skip:
            state.mark(inline_key)
            last_result = ProcessResult(
                inline_key, inline_classification, None, False, False, False, False, "skip"
            )
            continue

        last_result = _process_classified_context(
            inline_ctx, inline_classification, config, client, state, inline_key, inline_marker
        )

    # Mark the original review body key so the same pull_request_review event is not
    # re-expanded on the next bot invocation.
    state.mark(review_body_key)
    assert last_result is not None  # loop ran at least once because inline_comments is non-empty
    return last_result


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

    # A "file:" / "path:" line-start hint was found but the path could not be sanitized
    # (e.g. path traversal).  Reject before classification so the reason is distinct from
    # a plain "no hint" skip and the state store still records it as processed.
    if context.kind.value == "review_body" and context.review_body_path_hint_present and context.path is None:
        state.mark(key)
        return ProcessResult(key, Classification.skip, None, False, False, False, False, "invalid-review-body-path")

    classification = classify_codex_review(context)
    if classification == Classification.skip:
        # Fallback: review_body with no concrete path → look for inline diff comments
        # belonging to the same review before giving up.
        if (
            context.kind == ReviewKind.review_body
            and context.path is None
            and not context.review_body_path_hint_present
            and client is not None
            and context.review_id is not None
        ):
            return _run_review_body_inline_fallback(context, config, client, state, key)
        state.mark(key)
        return ProcessResult(key, classification, None, False, False, False, False, "skip")

    return _process_classified_context(context, classification, config, client, state, key, marker)


if __name__ == "__main__":
    result = run()
    print(result)
