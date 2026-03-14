from ugh_quantamental.review_autofix.github_client import GithubClient, GithubEvent, build_review_context, is_review_event
from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind


def test_is_review_event_filters_non_review_event() -> None:
    event = GithubEvent(delivery_id="", event_name="workflow_dispatch", payload={})
    assert is_review_event(event) is False


def test_build_review_context_raises_for_non_review_event() -> None:
    event = GithubEvent(delivery_id="", event_name="workflow_dispatch", payload={})
    try:
        build_review_context(event)
    except ValueError as exc:
        assert "unsupported event" in str(exc)
    else:
        raise AssertionError("expected ValueError")



def _review_body_event(body: str) -> GithubEvent:
    return GithubEvent(
        delivery_id="",
        event_name="pull_request_review",
        payload={
            "repository": {"full_name": "acme/repo"},
            "pull_request": {
                "number": 1,
                "base": {"ref": "main"},
                "head": {"ref": "feature", "sha": "sha", "repo": {"full_name": "acme/repo"}},
            },
            "review": {
                "id": 10,
                "user": {"login": "alice"},
                "body": body,
                "submitted_at": "2024-01-01T00:00:00Z",
            },
        },
    )


def _diff_context() -> ReviewContext:
    return ReviewContext(
        kind=ReviewKind.diff_comment,
        repository="acme/repo",
        pr_number=1,
        review_id=10,
        review_comment_id=44,
        head_sha="sha",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="alice",
        body="b",
        path="a.py",
        diff_hunk="@@",
        line=1,
        start_line=1,
        version_discriminator="v",
    )


def test_has_processed_marker_for_review_comment_trusted_author() -> None:
    client = GithubClient("token")
    client.list_review_comments = lambda repo, pr: (
        {"in_reply_to_id": 44, "body": "ok\n<!-- review-autofix-key:k -->", "user": {"login": "github-actions[bot]"}},
    )
    client.list_issue_comments = lambda repo, pr: ()
    context = _diff_context()
    assert client.has_processed_marker(context, "<!-- review-autofix-key:k -->") is True


def test_has_processed_marker_ignores_untrusted_author() -> None:
    client = GithubClient("token")
    client.list_review_comments = lambda repo, pr: (
        {"in_reply_to_id": 44, "body": "ok\n<!-- review-autofix-key:k -->", "user": {"login": "alice"}},
    )
    client.list_issue_comments = lambda repo, pr: ()
    context = _diff_context()
    assert client.has_processed_marker(context, "<!-- review-autofix-key:k -->") is False


def test_list_paginated_fetches_multiple_pages() -> None:
    client = GithubClient("token")

    def fake_request(method: str, path: str, body=None):
        del method
        del body
        if path.endswith("page=1"):
            return [{"id": n} for n in range(100)]
        if path.endswith("page=2"):
            return [{"id": 101}]
        return []

    client._request = fake_request  # type: ignore[method-assign]
    items = client.list_issue_comments("acme/repo", 7)
    assert len(items) == 101

def test_build_review_context_accepts_valid_review_body_file_hint() -> None:
    context = build_review_context(_review_body_event("file: src/module.py\nset range_hit to None"))
    assert context.kind == ReviewKind.review_body
    assert context.path == "src/module.py"
    assert context.review_body_path_hint_present is True


def test_build_review_context_rejects_absolute_review_body_file_hint() -> None:
    context = build_review_context(_review_body_event("file: /tmp/x.py\nset range_hit to None"))
    assert context.path is None
    assert context.review_body_path_hint_present is True


def test_build_review_context_rejects_traversal_review_body_file_hint() -> None:
    context = build_review_context(_review_body_event("file: ../tmp/x.py\nset range_hit to None"))
    assert context.path is None
    assert context.review_body_path_hint_present is True
