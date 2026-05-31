"""STATUS.md ## 次の発行順序 must hold only active items.

When a Phase / Brief / Milestone merges, the wrap-up sweep (step 4) moves it to
## 直近 merged. Leaving a completed item in the queue is the documented stale-
entry anti-pattern, so forbid completion markers on the queue's list items.

Only list items (numbered or bulleted) are inspected — the prose intro of the
section is allowed to *describe* the sweep (it naturally mentions 完走 / merged).
"""

from __future__ import annotations

import re

from ._helpers import STATUS_MD, section_body

# Markers that indicate an item is done and should already have been swept.
COMPLETION_MARKERS = ("✅", "完走", "DONE", "merged", "マージ済")

_LIST_ITEM = re.compile(r"^[ \t]*(?:\d+\.|[-*])[ \t]+(?P<text>.*)$")


def test_next_queue_has_no_completed_items() -> None:
    assert STATUS_MD.exists(), f"{STATUS_MD} is missing"
    body = section_body(STATUS_MD.read_text(encoding="utf-8"), "次の発行順序")

    offenders: list[str] = []
    for line in body.splitlines():
        item = _LIST_ITEM.match(line)
        if not item:
            continue
        text = item.group("text")
        if any(marker in text for marker in COMPLETION_MARKERS):
            offenders.append(line.strip())

    assert not offenders, (
        "Completed items must be swept from 次の発行順序 into ## 直近 merged "
        "(wrap-up step 4). Offending queue items:\n  " + "\n  ".join(offenders)
    )
