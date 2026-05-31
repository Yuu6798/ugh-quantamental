---
name: new-brief
description: Draft a Task Brief (Claude→Codex handoff) for the ugh-quantamental repo, running a reusable brief-drafting checklist as a pre-flight gate before emitting the AGENTS.md Task Brief format. Use when the user asks to write/draft a new brief, a Phase/Milestone brief, or a Task Brief, or to change an existing brief.
---

# new-brief — Task Brief drafter with pre-flight gate

Drafts a Task Brief in the `AGENTS.md` Task Brief format, but only after running
a reusable checklist that front-loads the checks that historically caused
multi-round review churn (review-round count is the repo's leading quality
indicator — `AGENTS.md` § Experience Externalization Discipline; PR #104 took
13 rounds because the planning doc was drafted without grounding every axis
first). This skill is the **executor**; the policy source of truth is
`AGENTS.md`. If it diverges from this file, it wins — fix this skill rather than
acting on a stale copy.

## 0. Pre-flight reading (Tier B)

Before drafting, read:

- `AGENTS.md` Task Brief format + Escalation Rules + Branch Rules + Experience
  Externalization Discipline.
- The relevant phase plan for the brief at hand:
  `docs/engine_review_2026_05_planning.md` (current P0/P1/P2 phases) or the
  milestone spec under `docs/specs/`.
- `.claude/memory/STATUS.md` § Phase + § 次の発行順序 for current priority.
- `.claude/memory/_index.md` + the 直近 3 dated `YYYY-MM-DD.md` session logs.
  Skipping the memory log re-introduces the "過去 session trap 再発生"
  anti-pattern.

If a required doc is stale or missing, surface that in the draft rather than
inventing context (documented recurring failure mode).

## 1. Reusable checklist (run before writing spec)

### 1a. Schema / symbol grounding  ⚠️ highest-yield
Every module path, function name, ORM column, schema field, CSV column, or
constant you name in the brief MUST be verified to exist in the implementation
by grep, not from memory. Canonical files to grep (paths are repo-root
relative — the source package lives under `src/ugh_quantamental/`):

- `src/ugh_quantamental/schemas/` — Pydantic contracts: enums, SSVSnapshot,
  Omega, MarketSVP, ProjectionSnapshot (field names + validators)
- `src/ugh_quantamental/engine/{projection,state,review_audit}.py`
  (+ `*_models.py`) — pure function names + signatures, `__all__`
- `src/ugh_quantamental/persistence/` — ORM models, repositories, serializers
  (column names, `_normalize_created_at` boundary)
- `src/ugh_quantamental/workflows/models.py` (SQLAlchemy-free) vs
  `.../workflows/runners.py` (DB) — import-isolation boundary
- `src/ugh_quantamental/query/models.py` vs `.../query/readers.py` —
  rehydration attribute names
- `src/ugh_quantamental/replay/` — `models` / `runners` / `batch` / `suites` /
  `baselines` (zero-run guard, per-`(group, name)` delta)
- `src/ugh_quantamental/fx_protocol/` — contracts (`calendar` / `ids` /
  `data_models` / `data_sources` / `request_builders`), `market_ugh_builder`,
  schemas (`models` / `forecast_models` / `outcome_models` / `report_models`),
  application (`forecasting` / `outcomes` / `csv_exports` / `reporting` /
  `automation`). CSV column names (`forecast_batch_id`, `range_hit_count`,
  `ugh_v2_ensemble` row) are a permanent foot-gun — quote them verbatim from
  the producer, not from memory.
- `alembic/versions/` — current migration head before any ORM column change
- `docs/specs/` — the formal v1 spec for the milestone being touched

### 1b. Invariant scope
A brief MUST NOT require a change that violates a core architecture invariant
(`CLAUDE.md` § Architecture invariants). If the work genuinely needs to, that
is an `AGENTS.md` escalation trigger, not a silent assumption. The invariants:

- **Pure engine functions** — same inputs → same output; no globals/mutation/I/O.
- **Frozen schemas** — `extra="forbid", frozen=True`; construct new, never mutate.
- **Deterministic and bounded** — values clamped/normalised; validators enforce.
- **Naive-UTC persistence** — `_normalize_created_at` at the repository boundary.
- **Workflow flush-only** — never commit; caller owns the transaction.
- **Import isolation** — `*.models` / `query.__init__` / `replay.__init__`
  importable without SQLAlchemy; DB code behind function-body imports.
- **Read-only replay** — never write/flush/commit during reads; suites fail on
  `requested_count == 0`.
- **Review-audit boundary** — raw text → extractor → engine, never bypassed.

`fx_protocol` is the explicit exception (intentional HTTP / `datetime.now()`),
so security/determinism constraints there are scoped, not absolute.

### 1c. Determinism & test hygiene
- New tests must avoid network calls, file I/O, and randomness.
- SQLAlchemy-dependent tests use `@pytest.mark.skipif(not HAS_SQLALCHEMY, ...)`
  with imports inside function bodies.
- Don't modify existing tests unless the brief explicitly requires it.
- Persistence changes that touch ORM columns MUST pair with an Alembic migration.

### 1d. Cross-doc consistency
- Reference other phases using their canonical framing from
  `docs/engine_review_2026_05_planning.md` (e.g. "Phase 2 = state classifier
  sharpening, softmax T=0.5 + fire gate weighted sum").
- If the brief changes a CSV schema, a metric definition, or an
  `engine_version` bump cadence, grep the whole brief and sync every occurrence
  — axes-mismatch (e.g. 60 営業日 vs 60 サンプル) was the dominant PR #104
  churn category.

## 2. Emit the brief (AGENTS.md Task Brief format)

```markdown
# Task Brief: <ID> - <short title>

## Phase
<phase / spec reference, e.g. engine_review §4 Phase 2>

## Goal
<1-2 sentences defining completion>

## Acceptance Criteria
- [ ] Verifiable condition 1
- [ ] Verifiable condition 2

## Scope
- IN: <files or modules Codex may change>
- OUT: <files, behavior, or decisions Codex must not change>

## Allowed Dependencies (optional)
<deps Codex may add; if absent, new deps require escalation>

## Implementation Hints (optional)
<suggested approach, design references, existing patterns>

## Required Outputs
- Branch name: `codex/<topic>`
- PR title: <Conventional Commits style>
- Expected files changed: <list>
- Required tests: <test expectations>

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
```

Make every Acceptance Criterion **verifiable** (a command, a test, or a
grep-able assertion). Target task size ≈ 0.5–2 days. Foreseeable blockers
should map to an `AGENTS.md` escalation trigger rather than a silent assumption.

## 3. Closeout
Hand the brief to the user (it is paste-ready for Codex). Note any 1a grep that
surfaced a symbol mismatch, any unresolved design decision the user must settle
(e.g. an Open Question from the planning doc), and any 5+ round dispute that
should be externalized into docs/tests per `AGENTS.md`.
