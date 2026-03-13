from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from dataclasses import dataclass

from .models import ReviewContext, ReviewKind

_REVIEW_EVENTS = {"pull_request_review_comment", "pull_request_review"}


@dataclass(frozen=True)
class GithubEvent:
    delivery_id: str
    event_name: str
    payload: dict


class GithubClient:
    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        self._token = token
        self._api_url = api_url.rstrip("/")

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self._api_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def reply_to_review_comment(self, repo: str, comment_id: int, body: str) -> None:
        self._request("POST", f"/repos/{repo}/pulls/comments/{comment_id}/replies", {"body": body})

    def reply_to_pr(self, repo: str, pr_number: int, body: str) -> None:
        self._request("POST", f"/repos/{repo}/issues/{pr_number}/comments", {"body": body})


def load_event_from_env() -> GithubEvent:
    path = os.environ["GITHUB_EVENT_PATH"]
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    return GithubEvent(
        delivery_id=os.getenv("GITHUB_DELIVERY", ""),
        event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
        payload=payload,
    )


def is_review_event(event: GithubEvent) -> bool:
    return event.event_name in _REVIEW_EVENTS


def _body_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def _build_version_discriminator(item: dict, body: str) -> str:
    timestamp = item.get("updated_at") or item.get("submitted_at") or item.get("created_at") or ""
    return f"{timestamp}:{_body_hash(body)}"


def build_review_context(event: GithubEvent) -> ReviewContext:
    if not is_review_event(event):
        raise ValueError(f"unsupported event: {event.event_name}")

    payload = event.payload
    if "pull_request" not in payload:
        raise ValueError("missing pull_request payload")

    repo = payload["repository"]["full_name"]
    pr = payload["pull_request"]
    base_ref = pr["base"]["ref"]
    head_ref = pr["head"]["ref"]
    head_sha = pr["head"]["sha"]
    same_repo = pr["head"]["repo"]["full_name"] == repo

    if event.event_name == "pull_request_review_comment":
        comment = payload["comment"]
        body = comment.get("body", "")
        return ReviewContext(
            kind=ReviewKind.diff_comment,
            repository=repo,
            pr_number=pr["number"],
            review_id=comment.get("pull_request_review_id"),
            review_comment_id=comment["id"],
            head_sha=head_sha,
            base_ref=base_ref,
            head_ref=head_ref,
            same_repo=same_repo,
            reviewer_login=comment.get("user", {}).get("login"),
            body=body,
            path=comment.get("path"),
            diff_hunk=comment.get("diff_hunk"),
            version_discriminator=_build_version_discriminator(comment, body),
        )

    review = payload["review"]
    body = review.get("body", "")
    path = None
    for line in body.splitlines():
        lower = line.lower()
        if lower.startswith("file:") or lower.startswith("path:"):
            path = line.split(":", 1)[1].strip()
            break
    return ReviewContext(
        kind=ReviewKind.review_body,
        repository=repo,
        pr_number=pr["number"],
        review_id=review["id"],
        review_comment_id=None,
        head_sha=head_sha,
        base_ref=base_ref,
        head_ref=head_ref,
        same_repo=same_repo,
        reviewer_login=review.get("user", {}).get("login"),
        body=body,
        path=path,
        diff_hunk=None,
        version_discriminator=_build_version_discriminator(review, body),
    )
