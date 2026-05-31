"""_index.md entries must stay compact.

The index is a 1-2 line-per-session lookup table; the full narrative lives in
the dated YYYY-MM-DD.md file. Letting an entry grow into an essay defeats the
index (the upstream repo restored a 53KB -> 5KB index after this drift). Cap
each dated entry bullet at 500 characters.

A bullet may legitimately wrap onto indented continuation lines, so the whole
bullet block (header line + its continuation lines) is measured, not just the
first physical line — otherwise an essay-length continuation slips past the
gate.
"""

from __future__ import annotations

import re

from ._helpers import INDEX_MD

MAX_ENTRY_CHARS = 500

# A real entry bullet, e.g. "- 2026-05-30: ...". The template comment uses
# "- YYYY-MM-DD:" which does not match the digit pattern and is ignored.
_ENTRY = re.compile(r"^-[ \t]+\d{4}-\d{2}-\d{2}:")


def _entry_blocks(lines: list[str]) -> list[list[str]]:
    """Group each dated bullet with its continuation lines into one block.

    A block starts at an `_ENTRY` line and extends until the next boundary: a
    blank line (the markdown list-item separator), another entry, a heading, or
    an HTML comment.
    """
    blocks: list[list[str]] = []
    i, n = 0, len(lines)
    while i < n:
        if not _ENTRY.match(lines[i]):
            i += 1
            continue
        block = [lines[i]]
        j = i + 1
        while j < n:
            nxt = lines[j]
            if not nxt.strip() or _ENTRY.match(nxt):
                break
            if nxt.lstrip().startswith(("#", "<!--")):
                break
            block.append(nxt)
            j += 1
        blocks.append(block)
        i = j
    return blocks


def test_index_entries_are_compact() -> None:
    assert INDEX_MD.exists(), f"{INDEX_MD} is missing"
    lines = INDEX_MD.read_text(encoding="utf-8").splitlines()

    blocks = _entry_blocks(lines)
    assert blocks, "no dated entries found in _index.md"

    offenders = [block for block in blocks if len("\n".join(block)) > MAX_ENTRY_CHARS]
    assert not offenders, (
        f"_index.md entries must be <= {MAX_ENTRY_CHARS} chars (full bullet "
        "block, including continuation lines); move detail into the dated file. "
        "Offending entries:\n  "
        + "\n  ".join(
            f"({len(chr(10).join(b))} chars) {b[0][:80]}..." for b in offenders
        )
    )
