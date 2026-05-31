"""_index.md entries must stay compact.

The index is a 1-2 line-per-session lookup table; the full narrative lives in
the dated YYYY-MM-DD.md file. Letting an entry grow into an essay defeats the
index (the upstream repo restored a 53KB -> 5KB index after this drift). Cap
each dated entry bullet at 500 characters.
"""

from __future__ import annotations

import re

from ._helpers import INDEX_MD

MAX_ENTRY_CHARS = 500

# A real entry bullet, e.g. "- 2026-05-30: ...". The template comment uses
# "- YYYY-MM-DD:" which does not match the digit pattern and is ignored.
_ENTRY = re.compile(r"^-[ \t]+\d{4}-\d{2}-\d{2}:")


def test_index_entries_are_compact() -> None:
    assert INDEX_MD.exists(), f"{INDEX_MD} is missing"
    lines = INDEX_MD.read_text(encoding="utf-8").splitlines()

    entries = [line for line in lines if _ENTRY.match(line)]
    assert entries, "no dated entries found in _index.md"

    offenders = [line for line in entries if len(line) > MAX_ENTRY_CHARS]
    assert not offenders, (
        f"_index.md entries must be <= {MAX_ENTRY_CHARS} chars; move detail "
        "into the dated file. Offending entries:\n  "
        + "\n  ".join(f"({len(line)} chars) {line[:80]}..." for line in offenders)
    )
