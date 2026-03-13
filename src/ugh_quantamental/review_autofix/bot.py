from __future__ import annotations

import logging
import os

from .classifier import classify_review
from .config import load_config
from .git_ops import commit_changes, has_changes, push_head_branch
from .github_client import GithubClient, build_review_context, load_event_from_env
from .models import Classification, ProcessResult
from .rules import RuleRegistry
from .state_store import FileStateStore
from .validator import run_validation


def _processed_key(context) -> str:
    if context.review_comment_id is not None:
        return f"review_comment:{context.review_comment_id}:{context.head_sha}"
    return f"review:{context.review_id}:{context.head_sha}"


def _reply(client: GithubClient, context, body: str) -> None:
    if context.review_comment_id is not None:
        client.reply_to_review_comment(context.repository, context.review_comment_id, body)
    else:
        client.reply_to_pr(context.repository, context.pr_number, body)


def run() -> ProcessResult:
    config = load_config()
    logging.basicConfig(level=config.log_level)
    event = load_event_from_env()
    context = build_review_context(event)
    state = FileStateStore(os.getenv("STATE_STORE_PATH", ".autofix-bot/state.json"))
    key = _processed_key(context)
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

    registry = RuleRegistry()
    rule = registry.match(context)
    if rule is None:
        state.mark(key)
        return ProcessResult(key, Classification.skip, None, False, False, False, False, "no-matching-rule")

    changed = False
    pushed = False
    validation_ok = False

    if config.bot_mode in {"detect_only"}:
        reason = "detect-only"
    else:
        applied = rule.apply(context)
        changed = applied.changed
        if not changed:
            reason = "no-change"
        elif config.bot_mode in {"propose_only"} or config.dry_run or classification == Classification.propose_only:
            reason = "proposed-only"
        else:
            validation = run_validation(config.all_validation_commands)
            validation_ok = validation.ok
            if not validation_ok:
                reason = "validation-failed"
            else:
                if has_changes():
                    commit_changes(f"AUTO: apply {rule.rule_id} for PR #{context.pr_number} ({key})")
                    push_head_branch(context.head_ref)
                    pushed = True
                    reason = "pushed"
                else:
                    reason = "no-change-after-validation"

    token = os.getenv("GITHUB_TOKEN", "")
    replied = False
    if token:
        client = GithubClient(token)
        if reason == "pushed" and config.reply_on_success:
            _reply(client, context, f"✅ Auto-fix applied by rule `{rule.rule_id}` and pushed to `{context.head_ref}`.")
            replied = True
        if reason != "pushed" and config.reply_on_failure:
            _reply(client, context, f"ℹ️ Auto-fix processed (`{rule.rule_id}`): {reason}. No push was performed.")
            replied = True

    state.mark(key)
    return ProcessResult(key, classification, rule.rule_id, changed, validation_ok, pushed, replied, reason)


if __name__ == "__main__":
    result = run()
    print(result)
