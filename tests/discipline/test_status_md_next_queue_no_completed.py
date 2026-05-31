"""STATUS.md ## 次の発行順序 must hold only active items.

When a Phase / Brief / Milestone merges, the wrap-up sweep (step 4) moves it to
## 直近 merged. Leaving a completed item in the queue is the documented stale-
entry anti-pattern, so forbid completion markers on the queue's list items.

Only list items (numbered or bulleted) are inspected — the prose intro of the
section is allowed to *describe* the sweep (it naturally mentions 完走 / merged).
Each list item is grouped with its continuation lines before scanning, so a
marker on a wrapped line is not missed.
"""

from __future__ import annotations

import re

from ._helpers import STATUS_MD, section_body

# Markers that indicate an item is done and should already have been swept.
COMPLETION_MARKERS = ("✅", "完走", "DONE", "merged", "マージ済")

_LIST_ITEM = re.compile(r"^[ \t]*(?:\d+\.|[-*])[ \t]+")


def _list_item_blocks(body: str) -> list[str]:
    """Group each list item with its continuation lines into one block.

    A block starts at a `_LIST_ITEM` line and extends until the next boundary: a
    blank line or another list item. Prose before the first list item (the
    section intro) is never collected, so it may describe the sweep freely.
    """
    lines = body.splitlines()
    blocks: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        if not _LIST_ITEM.match(lines[i]):
            i += 1
            continue
        block = [lines[i]]
        j = i + 1
        while j < n:
            nxt = lines[j]
            if not nxt.strip() or _LIST_ITEM.match(nxt):
                break
            block.append(nxt)
            j += 1
        blocks.append("\n".join(block))
        i = j
    return blocks


def test_next_queue_has_no_completed_items() -> None:
    assert STATUS_MD.exists(), f"{STATUS_MD} is missing"
    body = section_body(STATUS_MD.read_text(encoding="utf-8"), "次の発行順序")

    offenders = [
        block
        for block in _list_item_blocks(body)
        if any(marker in block for marker in COMPLETION_MARKERS)
    ]

    assert not offenders, (
        "Completed items must be swept from 次の発行順序 into ## 直近 merged "
        "(wrap-up step 4). Offending queue items:\n  "
        + "\n  ".join(block.replace("\n", " ").strip() for block in offenders)
    )
