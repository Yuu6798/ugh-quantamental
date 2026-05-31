"""STATUS.md ## Phase must be exactly one paragraph.

The phase line is the canonical "where are we" snapshot. The recurring drift is
appending a new paragraph on a phase change while leaving the old one in place,
so the section slowly accretes stale state. Enforce overwrite-on-change.
"""

from __future__ import annotations

import re

from ._helpers import STATUS_MD, section_body


def test_phase_section_is_single_paragraph() -> None:
    assert STATUS_MD.exists(), f"{STATUS_MD} is missing"
    body = section_body(STATUS_MD.read_text(encoding="utf-8"), "Phase")
    paragraphs = [p for p in re.split(r"\n[ \t]*\n", body) if p.strip()]
    assert len(paragraphs) == 1, (
        "STATUS.md ## Phase must be exactly one paragraph "
        f"(found {len(paragraphs)}). On a phase change, overwrite the old "
        "paragraph instead of appending a new one."
    )
