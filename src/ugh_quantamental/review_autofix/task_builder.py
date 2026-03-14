from __future__ import annotations

from .executor_models import CodexFixTask
from .models import ReviewContext, ReviewKind


def build_fix_task(context: ReviewContext, processed_key: str) -> CodexFixTask:
    location = []
    if context.path:
        location.append(f"file: {context.path}")
    if context.start_line is not None:
        location.append(f"start_line: {context.start_line}")
    if context.line is not None:
        location.append(f"line: {context.line}")
    if context.diff_hunk:
        location.append(f"diff_hunk:\n{context.diff_hunk}")

    review_type = "review comment" if context.kind == ReviewKind.diff_comment else "review body"
    location_block = "\n".join(location) if location else "(no precise file location provided)"

    prompt = "\n".join(
        (
            "You are fixing a GitHub pull request based on a codex review finding.",
            "Hard constraints:",
            "- same branch update only",
            "- no new PR",
            "- minimal change only",
            "- fix only the cited review finding",
            "- run relevant tests",
            "- do not perform unrelated refactor",
            "- preserve existing behavior except for the bug being fixed",
            "",
            "Review context:",
            f"- repository: {context.repository}",
            f"- pr_number: {context.pr_number}",
            f"- base_ref: {context.base_ref}",
            f"- head_ref: {context.head_ref}",
            f"- head_sha: {context.head_sha}",
            f"- review_kind: {review_type}",
            f"- reviewer: {context.reviewer_login or '(unknown)'}",
            f"- review_id: {context.review_id}",
            f"- review_comment_id: {context.review_comment_id}",
            f"- processed_key: {processed_key}",
            "",
            "Target location:",
            location_block,
            "",
            "Review finding:",
            context.body or "(empty review body)",
        )
    )

    return CodexFixTask(
        task_id=processed_key,
        prompt=prompt,
        repository=context.repository,
        pr_number=context.pr_number,
        head_ref=context.head_ref,
        base_ref=context.base_ref,
        head_sha=context.head_sha,
    )
