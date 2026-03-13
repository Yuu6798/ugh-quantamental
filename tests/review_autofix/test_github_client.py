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


def test_has_processed_marker_for_review_comment() -> None:
    client = GithubClient("token")
    client.list_review_comments = lambda repo, pr: ({"in_reply_to_id": 44, "body": "ok\n<!-- review-autofix-key:k -->"},)
    context = ReviewContext(
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
    assert client.has_processed_marker(context, "<!-- review-autofix-key:k -->") is True


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
