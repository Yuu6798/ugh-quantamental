"""STATUS.md must have exactly its three sections, once each, in order.

``## Phase`` → ``## 次の発行順序`` → ``## 直近 merged``, no other ``## `` line, and
every mention of one of those headings in the prose kept inside a closed
`` `code span` ``.

The other STATUS.md tests read one section through ``section_body``: the first
line that *is* the heading, up to the next ``## `` line. They cannot see what
lies outside that span, so a rewrite that leaves an old section behind passes
them.

That happened on 2026-11-10 (the sweep after #144). A script located each
section by the first *occurrence* of its heading text, and that text first
appears inside the file's own prose (the intro links to `` `## 次の発行順序` ``,
the queue intro mentions `` `## 直近 merged` ``). The rewritten file kept the old
Phase paragraph and the old queue after the new ones, plus two fragment lines
starting with ``## 次の発行順序``` and ``## 直近 merged```. The Phase and queue
tests still passed, because each read only the new span up to the first
fragment. The diff review caught it before the push.

A split at the same prose occurrence can also leave no fragment heading at all
(cut right after the heading text, resume at the next ``## `` line): the new
section then lands in the prose and the old one stays under the real heading,
with the heading lines intact. Its only trace is the cut prose, whose
`` `## 次の発行順序` `` span is left unclosed — hence the code-span rule.
"""

from __future__ import annotations

import re

import pytest

from ._helpers import STATUS_MD, level2_headings

EXPECTED_SECTIONS = ("Phase", "次の発行順序", "直近 merged")

_BACKTICK_RUN = re.compile(r"`+")


def _code_span_ranges(line: str) -> list[tuple[int, int]]:
    """Character ranges of the closed inline code spans on one line.

    As in CommonMark, a span opened by a run of N backticks closes at the next
    run of exactly N backticks; an unmatched run opens nothing.
    """
    runs = [(m.start(), m.end()) for m in _BACKTICK_RUN.finditer(line)]
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(runs):
        start, end = runs[i]
        for j in range(i + 1, len(runs)):
            if runs[j][1] - runs[j][0] == end - start:
                spans.append((end, runs[j][0]))
                i = j + 1
                break
        else:
            i += 1
    return spans


def section_structure_problems(text: str) -> list[str]:
    """Describe every way ``text`` departs from the expected section layout."""
    headings = level2_headings(text)
    heading_lines = {number for number, _ in headings}
    problems: list[str] = []
    for number, title in headings:
        if title not in EXPECTED_SECTIONS:
            problems.append(
                f"line {number}: unexpected heading '## {title}' — a fragment like this "
                "usually means a rewrite split the file at heading text inside prose; "
                "a deliberate new section must be added to EXPECTED_SECTIONS"
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
    for number, line in enumerate(text.split("\n"), start=1):
        if number in heading_lines:
            continue
        spans = _code_span_ranges(line)
        for section in EXPECTED_SECTIONS:
            token = f"## {section}"
            for match in re.finditer(re.escape(token), line):
                inside = any(a <= match.start() and match.end() <= b for a, b in spans)
                if not inside:
                    problems.append(
                        f"line {number}: '{token}' sits outside a closed `code span` — "
                        "a rewrite probably split the file at this prose mention"
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
        "STATUS.md must hold exactly ## Phase → ## 次の発行順序 → ## 直近 merged, once each, "
        "with no other `## ` line and heading mentions in prose kept inside a code span. "
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


def _splice_at_first_mention(text: str, section: str, new_body: str) -> str:
    """The buggy rewrite that leaves no fragment heading: cut right after the
    first occurrence of the heading text and resume at the next ``## `` line."""
    token = f"## {section}"
    start = text.index(token) + len(token)
    end = text.find("\n## ", start)
    return text[:start] + new_body + text[end:]


@pytest.mark.parametrize(
    ("text", "expected_substrings"),
    [
        pytest.param(_VALID, [], id="valid"),
        pytest.param(_VALID.replace("## Phase\n", "## Phase  \n"), [], id="trailing-space"),
        pytest.param(
            _VALID.replace("new phase\n", "new phase\n\n### detail\n"), [], id="h3-ignored"
        ),
        pytest.param(
            _VALID.replace("1. item\n", "1. item\n\n```\n## step 2: push\n```\n"),
            ["unexpected heading '## step 2: push'"],
            id="fenced-heading-counts-like-section_body",
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
            _splice_at_first_mention(_VALID, "次の発行順序", "\n\n1. new item\n"),
            ["'## 次の発行順序' sits outside a closed `code span`"],
            id="splice-queue-into-intro",
        ),
        pytest.param(
            _splice_at_first_mention(_VALID, "直近 merged", "\n\n- **PR #2** entry\n"),
            ["'## 直近 merged' sits outside a closed `code span`"],
            id="splice-merged-into-queue",
        ),
        pytest.param(
            _VALID.replace("`## 次の発行順序` にリンク", "## 次の発行順序 にリンク"),
            ["'## 次の発行順序' sits outside a closed `code span`"],
            id="bare-mention-in-prose",
        ),
        pytest.param(
            _VALID.replace("`## 次の発行順序` にリンク", "``## 次の発行順序`` にリンク"),
            [],
            id="double-backtick-span",
        ),
        pytest.param(
            _VALID.replace("## 直近 merged\n\n- **PR #1** entry\n", ""),
            ["'## 直近 merged' is missing"],
            id="missing-section",
        ),
        pytest.param(
            _VALID + "\n## 直近 merged\n\n- **PR #2** entry\n",
            ["'## 直近 merged' appears 2 times"],
            id="duplicate-merged",
        ),
        pytest.param(
            _VALID.replace("## Phase\n\nnew phase\n\n", "") + "\n## Phase\n\nnew phase\n",
            ["sections out of order"],
            id="out-of-order",
        ),
        pytest.param(
            _VALID + "\n## Notes\n\nextra\n",
            ["unexpected heading '## Notes'", "EXPECTED_SECTIONS"],
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
