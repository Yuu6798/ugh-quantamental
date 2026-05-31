# tests/discipline — memory-hygiene enforcement

These tests enforce the structural rules of the session-memory workflow
(`CLAUDE.md` § Session Memory + the `/wrap-up` skill). They exist because the
`.claude/memory/` main-push exception is **post-hoc-only**: a normal change is
blocked by PR CI before it lands, but a direct memory push turns `main` red the
moment the drift is committed. The `/wrap-up` step 8 gate
(`python -m pytest tests/discipline/`) catches that drift *before* the push.

Convention ported from `Yuu6798/semantic-ci-code` and localized to this repo's
memory layout (bullet-style `_index.md`, no `--no-cov` since this repo declares
no `pytest-cov`).

## What is enforced

| Test | Rule |
|---|---|
| `test_status_md_phase_single_paragraph.py` | `STATUS.md ## Phase` is exactly one paragraph (overwrite-on-change, never append). |
| `test_status_md_next_queue_no_completed.py` | `STATUS.md ## 次の発行順序` holds only active items — no completed/merged markers leak in. |
| `test_index_md_entry_compactness.py` | Each `_index.md` entry bullet stays ≤ 500 chars (essay-cell anti-pattern). |

## What is deliberately NOT enforced

**Review-round count is not tested.** The "encode any 5+ round dispute into
docs/tests" rule (wrap-up step 7) is a checklist item, not a test: a
round-count proxy is fragile and would pass exactly in the "encode 忘れ" case
it is meant to catch. Keep it as human judgment in the wrap-up procedure.
