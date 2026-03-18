from __future__ import annotations

import pytest

from ugh_quantamental.review_autofix import bot


@pytest.fixture(autouse=True)
def _block_live_github(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no test can accidentally call the live GitHub API.

    - Removes GITHUB_TOKEN from os.environ for the duration of every test.
    - Replaces bot.GithubClient with a guard class that raises AssertionError
      if instantiated, so even a stray setenv("GITHUB_TOKEN", ...) cannot
      silently create a live client.

    Tests that need a fake GitHub client must override bot.GithubClient
    explicitly with a second monkeypatch.setattr call inside the test body.
    That second setattr takes precedence during the test, and both patches
    are torn down atomically at the end of the test.
    """
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    class _NoLiveGithubClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError(
                "Live GitHub API must not be used in unit tests. "
                "Use monkeypatch.setattr(bot, 'GithubClient', _FakeGithubClient) "
                "inside the test body to provide a fake client."
            )

    monkeypatch.setattr(bot, "GithubClient", _NoLiveGithubClient)
