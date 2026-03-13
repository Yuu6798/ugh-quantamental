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
        version_discriminator="v",
    )
    assert client.has_processed_marker(context, "<!-- review-autofix-key:k -->") is True
