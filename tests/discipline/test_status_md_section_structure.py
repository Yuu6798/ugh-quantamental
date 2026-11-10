"""STATUS.md must have exactly its three sections, once each, in order.

``## Phase`` → ``## 次の発行順序`` → ``## 直近 merged``, and no other ``## `` line.

The other STATUS.md tests read one section through ``section_body``: the first
line that *is* the heading, up to the next ``## `` line. They cannot see what
lies outside that span, so a rewrite that duplicates a section or leaves a
heading-like fragment passes them.

That happened on 2026-11-10 (the sweep after #144). A script located each
section by the first *occurrence* of its heading text, and that text first
appears inside the file's own prose (the intro links to `` `## 次の発行順序` ``,
the queue intro mentions `` `## 直近 merged` ``). The rewritten file kept the old
Phase paragraph and the old queue after the new ones, plus two fragment lines
starting with ``## 次の発行順序``` and ``## 直近 merged```. The Phase and queue
tests still passed, because each read only the new span up to the first
fragment. The diff review caught it before the push; this test catches it
without relying on that.
"""

from __future__ import annotations

import pytest

from ._helpers import STATUS_MD, level2_headings

EXPECTED_SECTIONS = ("Phase", "次の発行順序", "直近 merged")


def section_structure_problems(text: str) -> list[str]:
    """Describe every way ``text`` departs from the expected section layout."""
    headings = level2_headings(text)
    problems: list[str] = []
    for number, title in headings:
        if title not in EXPECTED_SECTIONS:
            problems.append(
                f"line {number}: unexpected heading '## {title}' — a fragment like this "
                "usually means a rewrite split the file at heading text inside prose"
            )
    for section in EXPECTED_SECTIONS:
        lines = [number for number, title in headings if title == section]
        if not lines:
            problems.append(f"'## {section}' is missing")
        elif len(lines) > 1:
            problems.append(
                f"'## {section}' appears {len(lines)} times (lines {lines}); "
                "the old section was left beside the new one"
            )
    order = [title for _, title in headings if title in EXPECTED_SECTIONS]
    if not problems and tuple(order) != EXPECTED_SECTIONS:
        problems.append(
            f"sections out of order: {' → '.join(order)} (expected {' → '.join(EXPECTED_SECTIONS)})"
        )
    return problems


def test_status_md_sections_appear_once_in_order() -> None:
    assert STATUS_MD.exists(), f"{STATUS_MD} is missing"
    problems = section_structure_problems(STATUS_MD.read_text(encoding="utf-8"))
    assert not problems, (
        "STATUS.md must hold exactly ## Phase → ## 次の発行順序 → ## 直近 merged, once each. "
        "Rewrite sections by their heading lines, never by searching for the heading "
        "text (it also appears in the file's prose):\n  " + "\n  ".join(problems)
    )


_INTRO = (
    "# STATUS\n\n"
    "他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。\n\n"
)
_QUEUE_INTRO = "active queue - 終了した項目は wrap-up step 4 で `## 直近 merged` に移す。\n"
_VALID = (
    _INTRO
    + "## Phase\n\nnew phase\n\n"
    + "## 次の発行順序\n\n"
    + _QUEUE_INTRO
    + "\n1. item\n\n"
    + "## 直近 merged\n\n- **PR #1** entry\n"
)
# The 2026-11-10 incident, reduced: new Phase, a fragment, the old Phase, the
# queue with new items, a fragment, the old items, then the merged section.
_INCIDENT = (
    _INTRO
    + "## Phase\n\nnew phase\n\n"
    + "## 次の発行順序` にリンクする。\n\n"
    + "## Phase\n\nold phase\n\n"
    + "## 次の発行順序\n\n"
    + _QUEUE_INTRO
    + "\n1. new item\n\n"
    + "## 直近 merged` に移す。\n\n1. old item\n\n"
    + "## 直近 merged\n\n- **PR #1** entry\n"
)


@pytest.mark.parametrize(
    ("text", "expected_substrings"),
    [
        pytest.param(_VALID, [], id="valid"),
        pytest.param(_VALID.replace("## Phase\n", "## Phase  \n"), [], id="trailing-space"),
        pytest.param(
            _VALID.replace("new phase\n", "new phase\n\n### detail\n"), [], id="h3-ignored"
        ),
        pytest.param(
            _VALID.replace("1. item\n", "1. item\n\n```\n## Phase\n```\n"),
            [],
            id="fenced-heading-ignored",
        ),
        pytest.param(
            _INCIDENT,
            [
                "'## Phase' appears 2 times",
                "unexpected heading '## 次の発行順序` にリンクする。'",
                "unexpected heading '## 直近 merged` に移す。'",
            ],
            id="2026-11-10-incident",
        ),
        pytest.param(
            _VALID.replace("## 直近 merged\n\n- **PR #1** entry\n", ""),
            ["'## 直近 merged' is missing"],
            id="missing-section",
        ),
        pytest.param(
            _VALID.replace("## Phase\n\nnew phase\n\n", "") + "\n## Phase\n\nnew phase\n",
            ["sections out of order"],
            id="out-of-order",
        ),
        pytest.param(
            _VALID + "\n## Notes\n\nextra\n",
            ["unexpected heading '## Notes'"],
            id="extra-section",
        ),
    ],
)
def test_section_structure_checker(text: str, expected_substrings: list[str]) -> None:
    problems = section_structure_problems(text)
    if not expected_substrings:
        assert problems == []
        return
    joined = "\n".join(problems)
    for substring in expected_substrings:
        assert substring in joined, joined
