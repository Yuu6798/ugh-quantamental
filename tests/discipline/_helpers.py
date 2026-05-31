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
