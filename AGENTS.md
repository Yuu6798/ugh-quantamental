# AGENTS.md — Claude × Codex Handoff Protocol

This repository uses a design / implementation split. Claude Code owns design
briefs and review judgment. Codex owns implementation, tests, and PR
preparation. The user triggers handoff between them.

Both agents should read this file before starting repository work. Repository
policy and architecture invariants live in `CLAUDE.md`; the live project
snapshot lives in `.claude/memory/STATUS.md`.

## Message Flow

```text
Claude -> Task Brief -> User -> Codex
Claude <- Completion Summary <- User <- PR URL <- Codex
```

Agents do not need to communicate directly. The user moves the structured
messages between them.

## 1. Task Brief: Claude to Codex

Claude issues tasks in this format so the user can paste them directly into
Codex. Target task size ≈ 0.5 to 2 days. Use the `/new-brief` skill, which runs
a pre-flight grounding checklist before emitting this format.

````markdown
# Task Brief: <ID> - <short title>

## Phase
<phase / spec reference, e.g. engine_review §4 Phase 2, or docs/specs/<milestone>>

## Goal
<1-2 sentences defining completion>

## Acceptance Criteria
- [ ] Verifiable condition 1
- [ ] Verifiable condition 2

## Scope
- IN: <files or modules Codex may change>
- OUT: <files, behavior, or decisions Codex must not change>

## Allowed Dependencies (optional)
<Dependencies Codex may add to pyproject.toml. If absent, new dependencies require escalation.>

## Implementation Hints (optional)
<Suggested approach, design references, existing patterns>

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
````

## 2. Completion Summary: Codex to Claude

Codex places this at the top of the PR body.

````markdown
# Completion Summary: <Task ID>

## Phase
<copied from Task Brief>

## What Changed
- <high-level change 1>
- <high-level change 2>

## Acceptance Criteria Status
- [x] Condition 1 - <evidence>
- [ ] Condition 2 - <reason if incomplete>

## Tests
- Added: <test names or count>
- Result: <pass / fail / skipped>

## Files Changed
<git diff --stat equivalent>

## Deviations from Brief
<None, or list deviations>

## Open Questions / Deferred
<Questions for Claude or next phase>

## Next Handoff
<What Claude should review next>
````

## 3. Escalation Rules

Codex should stop and report a blocked Completion Summary when:

1. Acceptance criteria are technically impossible.
2. The brief requires an unstated design decision.
3. Existing tests fail in a way that suggests a behavior regression.
4. A new dependency is needed but not listed in Allowed Dependencies.
5. The implementation would violate a core architecture invariant
   (`CLAUDE.md` § Architecture invariants — pure engine functions, frozen
   schemas, naive-UTC persistence, workflow flush-only, import isolation,
   read-only replay, review-audit boundary). `fx_protocol` is the explicit
   exception (intentional HTTP / `datetime.now()`).

## 4. Branch Rules

- Claude design branches: `claude/<topic>`
- Codex implementation branches: `codex/<topic>`
- Direct changes on `main` are reserved for explicit user-approved exceptions
  and for `.claude/memory/` operational logs (see `CLAUDE.md` § Git Workflow
  の例外).

## 5. Experience Externalization Discipline (経験値の外部化規律)

Required reading **before drafting any new Task Brief** or **introducing a new
architectural pattern**.

### 5.1 Principle

AI 開発は session 跨ぎの暗黙知を継承しない (Claude = no long-term memory、
Codex = PR 単位の review trail のみ、 user 壁打ち経験 = session 跨ぎで消失)。
再現性維持の唯一の方法は経験値を **明示 artifact** (docs / tests / checklists /
STATUS.md) に強制外部化すること。 Claude が forget する制約が逆説的に
**強制的 externalization discipline** として働く。

### 5.2 Review Round Count as Leading Quality Indicator

review / 壁打ち round 数は brief 規律の leading indicator として運用する。

| Round | 解釈 | Action |
|---|---|---|
| **0–3** | brief 規律が機能、 schema grounding 済 | acceptable (base case) |
| **5–10** | brief 内で曖昧だった spec が表面化 | 該当 spec を docs / test に encode |
| **10+** | grounding skip / axes-mismatch / spec の self-consistency 崩れ | 「同じ trap 二度発生させない」 encode work を follow-up / next brief で必ず実施 |

**Empirical base case**: PR #104 (`docs/engine_review_2026_05_planning.md`) は
Codex P2 review を **13 rounds / 22 threads** 受けた — 本リポジトリ最多。主因は
planning doc を schema / axes grounding 前に起草したこと (60 営業日 vs 60
サンプル、 fire 1/60 vs 3/60、 static epsilon vs 動的閾値、 `ugh_v2_ensemble`
行構造未指定、 `is_ugh_kind` 更新漏れ、 auto-detect 拡張欠落)。この churn を
planning doc 側に吸収させた結果、後続の実装 PR は少ない round で landing できる
はず — これが `/new-brief` の pre-flight grounding gate を設けた理由。

### 5.3 Practice + Anti-Pattern (combined)

| Practice | Anti-Pattern |
|---|---|
| brief 起草前に `_index.md` + 直近 3 dated entries + STATUS.md を読む | memory log skip → 過去 session trap 再発生 |
| brief で名指す path / 関数 / ORM column / CSV column を実装で grep 確認 (`/new-brief` §1a) | 思い込みで symbol を書く → compile-pass / runtime-fail 系 trap |
| CSV schema / metric 定義 / `engine_version` bump cadence を変えたら brief 全体を grep sync | axes-mismatch を放置 → PR #104 型の多 round chase |
| ORM column 変更時は Alembic migration を必ずペア | migration 漏れ → schema drift |
| review 5+ round → PR merge 後に「曖昧だった spec」を docs / tests に encode | round 内修正のみで完了 → trail が消失して再参照されない |
| PR merge 直後に STATUS.md `次の発行順序` を sweep (完走 entry 削除) | 「後で」と先送り → stale entry 蓄積 (`tests/discipline/test_status_md_next_queue_no_completed.py` で検出) |
| STATUS.md `## Phase` は 1 paragraph 厳守 | 新 paragraph 追加 + 旧 paragraph 残置 (`tests/discipline/test_status_md_phase_single_paragraph.py` で検出) |
| `_index.md` 各 entry を 1–2 行に保つ | essay 化 (`tests/discipline/test_index_md_entry_compactness.py` で検出) |

### 5.4 Three-Tier Externalization

| Tier | Type | 主要 artifact |
|---|---|---|
| 1 (codified) | 別 repo 持ち運び可 | `CLAUDE.md` / `AGENTS.md` / `.claude/skills/` / `tests/discipline/` |
| 2 (repo-specific) | 同 domain で再利用可 | `docs/specs/` / `docs/engine_review_2026_05_planning.md` |
| 3 (session-tacit) | memory 読み返しで部分継承 | `.claude/memory/STATUS.md` / `_index.md` / dated `YYYY-MM-DD.md` |

## Repository status

`ugh-quantamental` is a deterministic Python 3.11+ library containing:

- **schemas** — frozen Pydantic v2 data contracts (enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot)
- **engine** — pure projection and state-lifecycle functions
- **persistence** — SQLAlchemy/Alembic-backed run records for projection, state runs, and regression suite baselines
- **workflows** — synchronous composition layer: run engine → persist → reload → return
- **query** — read-only inspection layer: summaries, filtering, and full bundle rehydration
- **replay** — deterministic single-run regression checker: rerun persisted runs against current engine
- **batch replay** — multi-run replay with per-run isolation and aggregate mismatch reporting
- **regression suite** — named suite runner over batch replay cases with deterministic pass/fail reporting
- **baseline / golden snapshot** — persist named suite results; compare future reruns against a pinned baseline
- **fx_protocol** — FX daily prediction cycle: frozen contracts, calendar helpers, deterministic ID generation, daily forecast/outcome/evaluation workflows, CSV exports, GitHub Actions automation, and read-only weekly report aggregation

Milestones 1–17 are complete. Core packages are deterministic, synchronous, and connector-free. `fx_protocol` contains intentional side effects (HTTP calls, API integrations). Day-to-day status (current phase, next-issue queue, recently merged PRs) lives in `.claude/memory/STATUS.md`.

## Durable working rules

- Keep diffs tightly scoped to the requested task.
- Use `/plan` for non-trivial work, and `/new-brief` to draft a Task Brief.
- Avoid network-dependent tests and checks.
- Do not modify tests unless explicitly required.
- Do not commit, push, or open a PR unless explicitly asked.

## Validation

Run these local checks when relevant:

```bash
ruff check .
pytest -q
```

Both must pass cleanly. CI enforces the same checks on every PR and push. Before
a direct `.claude/memory/` push, also run `python -m pytest tests/discipline/`
(the `/wrap-up` gate).

## Related Documents

- `CLAUDE.md` — repository policy, architecture invariants, session-memory workflow
- `.claude/memory/STATUS.md` — live project snapshot (phase / queue / merged)
- `docs/specs/` — formal milestone specifications
- `docs/engine_review_2026_05_planning.md` — current P0/P1/P2 phase plan
