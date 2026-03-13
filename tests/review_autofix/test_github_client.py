from ugh_quantamental.review_autofix.github_client import GithubEvent, build_review_context, is_review_event


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
