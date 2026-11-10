"""Shared helpers for memory-hygiene discipline tests."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = REPO_ROOT / ".claude" / "memory"
STATUS_MD = MEMORY_DIR / "STATUS.md"
INDEX_MD = MEMORY_DIR / "_index.md"


def section_body(text: str, heading: str) -> str:
    """Return the body of a top-level ``## <heading>`` section.

    The body runs from the heading line to the next ``## `` heading (or EOF).
    Raises ``AssertionError`` if the heading is absent so a missing section is
    a loud failure rather than a silent pass.
    """
    pattern = re.compile(
        r"^##[ \t]+" + re.escape(heading) + r"[ \t]*$(?P<body>.*?)(?=^##[ \t]|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    assert match is not None, f"## {heading} section not found"
    return match.group("body").strip()


_H2_LINE = re.compile(r"^##[ \t]+(?P<title>.*?)[ \t]*$")


def level2_headings(text: str) -> list[tuple[int, str]]:
    """Return ``(line_number, title)`` for every ``## `` heading line, in order.

    Line numbers are 1-based and lines are split on ``\\n`` only. ``###`` and
    deeper headings are not level 2. Every line that starts with ``## `` counts,
    fenced code blocks included, because ``section_body`` ends a section at any
    such line too: the two helpers must agree on where sections start and end,
    or a fenced ``## `` line would hide the rest of a section from the tests that
    read it. A line such as ``## Phase  `` yields the title ``Phase``.
    """
    headings: list[tuple[int, str]] = []
    for number, line in enumerate(text.split("\n"), start=1):
        match = _H2_LINE.match(line)
        if match is not None:
            headings.append((number, match.group("title")))
    return headings
