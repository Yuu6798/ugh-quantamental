# CLAUDE.md

Guidelines for AI assistants working in this repository.

## Repository overview

`ugh-quantamental` is a Python 3.11+ library. Core packages (`schemas`, `engine`, `persistence`, `workflows`, `query`, `replay`) are deterministic with no network calls. `fx_protocol` depends on live external state (APIs). Schema-first, synchronous, typed throughout.

| Package | Description |
|---|---|
| `schemas` | Frozen Pydantic v2 data contracts — enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot |
| `engine` | Pure projection, state-lifecycle, and review-audit functions; no I/O |
| `persistence` | SQLAlchemy v2 ORM run records with Alembic migration; naive-UTC `created_at` |
| `workflows` | Synchronous composition: run engine → persist → reload → return result |
| `query` | Read-only inspection: summaries, filtering, bundle rehydration |
| `replay` | Deterministic replay / regression checker (single-run, batch, suites, baselines) |
| `fx_protocol` | FX daily prediction: market-derived UGH input builder, forecasting, outcomes, evaluation, CSV exports, weekly/monthly reports, automation |

Milestones 1–17 complete. Phase 1 (M1–12): core engine→baselines. Phase 2 (M13–17): `fx_protocol`. See `docs/specs/`.

## Current status

The day-to-day project snapshot (current phase, recently merged PRs, and the
`次の発行順序` action queue) lives in `.claude/memory/STATUS.md` so this policy
doc stays stable while the snapshot can be edited freely.

- Live status: [`.claude/memory/STATUS.md`](.claude/memory/STATUS.md)
- Per-session log: [`.claude/memory/_index.md`](.claude/memory/_index.md) + the
  dated `YYYY-MM-DD.md` files
- Canonical milestone table: `PLANS.md`; phase plan:
  `docs/engine_review_2026_05_planning.md` / `docs/specs/`

When another doc needs to point at the live tracker, link to
`.claude/memory/STATUS.md` § 次の発行順序 — not to this file.

## Workflow (design / implementation split)

This repository separates design and implementation (handoff format in
`AGENTS.md`):

- **Claude Code**: design, specification, review judgment, phase planning
- **Codex**: implementation, tests, PR creation, Completion Summary
- **User**: final approval and handoff trigger

Default cycle:

1. Claude issues a Task Brief using `AGENTS.md` (via `/new-brief`).
2. User gives the brief to Codex.
3. Codex implements on `codex/<topic>`, runs checks, prepares a PR with a
   Completion Summary.
4. User shares the PR back to Claude.
5. Claude reviews and either approves, requests repair, or emits the next brief.

This split was already in use before being formalized: PR #104 ran the full
Claude-design → Codex-review loop (13 rounds). Solo Claude work and small fixes
need not round-trip, but anything ≈ 1 day or larger should go through a brief.

## Required reading (tiered)

Read up to the tier that matches your task scope, to keep startup attention
bounded.

### Tier A — always at startup
1. **This file (`CLAUDE.md`)** — policy, architecture invariants, session memory
2. **`.claude/memory/STATUS.md` § `## Phase` + § `次の発行順序`** — current
   state + active queue (skip `## 直近 merged` unless investigating a PR)
3. **`.claude/memory/_index.md` の直近 5 entries** — 1–2 line index form
4. **`AGENTS.md` §1–§4** — Message Flow + Task Brief / Completion Summary +
   Escalation + Branch Rules

### Tier B — before drafting a new brief
1. **`AGENTS.md` §5** — Experience Externalization Discipline
2. **The relevant phase plan** — `docs/engine_review_2026_05_planning.md` or the
   milestone spec under `docs/specs/`
3. **`.claude/memory/` の直近 3 dated session logs**

### Tier C — on-demand for the task
- Full read of the relevant `docs/specs/<milestone>.md`
- `alembic/versions/` head before any ORM column change
- Related dated session log in full

If a required doc is stale or incomplete, surface that in the response rather
than acting without it.

## Validation commands

Always run before considering any change done:

```bash
ruff check .   # lint
pytest -q      # tests
```

## Project layout

```
src/ugh_quantamental/
├── schemas/          # Enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot
├── engine/           # projection.py, state.py, review_audit.py + *_models.py
├── persistence/      # ORM models, repositories, serializers, db helpers
├── workflows/        # models.py (SQLAlchemy-free), runners.py (DB-dependent)
├── query/            # models.py (SQLAlchemy-free), readers.py (DB-dependent)
├── replay/           # models, runners, batch, suites, baselines (read-only except baseline writes)
├── fx_protocol/      # contracts: calendar, ids, data_models, data_sources, request_builders
│                     # pure: market_ugh_builder (snapshot→UGH feature derivation)
│                     # schemas: models, forecast_models, outcome_models, report_models
│                     # application: forecasting, outcomes, csv_exports, reporting, automation
alembic/versions/     # 0001–0005 migrations
scripts/              # run_fx_daily_protocol.py, run_fx_analysis_pipeline.py, etc.
tests/                # mirrors src/; some integration tests span modules
docs/specs/           # formal v1 specifications per milestone
```

When implementing a new milestone, read the corresponding spec in `docs/specs/` first.

## Technology stack

| Tool | Purpose |
|---|---|
| Python 3.11+ | `from __future__ import annotations` on all modules |
| Pydantic v2 | `extra="forbid", frozen=True` on all models |
| SQLAlchemy v2 | ORM; `DateTime(timezone=False)` columns |
| Alembic | Schema migration |
| ruff | Lint + format — line length 100, target `py311` |
| pytest | Test runner — quiet mode |

## Architecture invariants

Non-negotiable for core packages. `fx_protocol` has intentional side effects (HTTP, `datetime.now()`).

- **Pure engine functions.** Same inputs → same output. No globals, mutation, or I/O.
- **Frozen schemas.** `ConfigDict(extra="forbid", frozen=True)`. Never mutate; construct new.
- **Deterministic and bounded.** Values clamped/normalised. Validators enforce invariants.
- **Naive-UTC persistence.** `_normalize_created_at` at repository boundary.
- **Workflow flush-only.** Never commit; caller owns the transaction.
- **Import isolation.** `workflows.models`, `query.__init__`, `replay.__init__` importable without SQLAlchemy. DB-dependent code in `runners.py`/`readers.py`/`batch.py`/`suites.py`/`baselines.py`; transitive imports deferred inside function bodies.
- **Read-only replay.** Never write/flush/commit during reads. Suites fail on `requested_count == 0`. Baseline deltas per `(group, name)`.
- **Review-audit boundary.** Raw text → extractor → engine (never bypassed).

## Development conventions

### Code style
- Line length 100; Python 3.11+ syntax; type annotations on all signatures
- Docstrings on public functions/classes; no bare `except`

### Adding schemas
1. Define in `schemas/` with `extra="forbid", frozen=True` + validators
2. Add tests in `tests/schemas/`

### Adding engine functions
1. Pure function in `engine/*.py`, add to `__all__`
2. Inputs normalised/bounded; return typed output
3. Tests in `tests/engine/`

### Persistence
- No ORM column redesign without migration; keep `DateTime(timezone=False)`
- SQLAlchemy tests: `@pytest.mark.skipif(not HAS_SQLALCHEMY, ...)`, imports inside function bodies

### Workflows / Query / Replay
- `*.models` importable without SQLAlchemy; runner imports behind guards
- Workflows flush only; replay never writes
- `baselines.py` defers `run_regression_suite` import inside function bodies
- Query rehydration: named attribute access (`record.foo_json`), never `__dict__`

### Tests
- Don't modify existing tests unless required
- No network calls, file I/O, or randomness
- Parametrised for multiple cases; single-case for edge conditions

### Commits and PRs
- Don't commit/push/open PR unless explicitly asked; keep diffs scoped

## Session Memory / 永続記憶ワークフロー

長期にわたる設計会話を `.claude/memory/` に記録し、後続セッションがコンテキスト
を失わずに続きから着手できるようにする。convention は `Yuu6798/semantic-ci-code`
から移植。

### 仕組み

- 場所: `.claude/memory/`
- ファイル: `YYYY-MM-DD.md` (同日に複数セッションあれば「Session 2」「Session 3」
  と節を切って 1 ファイルに追記)
- 索引: `_index.md` に各セッションの 1 行要約を追記

### 起動時ルール

1. セッション開始時に `_index.md` を読んで過去の決定事項を把握する
2. 直近 3 件のサマリーは必要に応じて詳細参照する
3. 過去の設計判断に関する質問はサマリーを確認してから回答する

### 終了時ルール (自動トリガー)

ユーザーが終了意図を示すフレーズを発したら、確認なしで即座に `/wrap-up`
を実行する。`/wrap-up` skill が**実行系**、本セクションが**方針の source of
truth** で、両者が乖離したら本セクションが勝つ (skill を直す)。

トリガーフレーズの例:
- 「今日はここまで」「今日は終わり」「今日はおわり」
- 「セッション終了」「セッション閉じて」
- 「また明日」「また今度」「お疲れ様」「お疲れさま」
- 「done for today」「that's all」
- 手動: `/wrap-up`

実行内容 (この順序を守る — step 4 は step 5 より先、step 8 は push より先):

1. 会話の振り返りサマリーを `.claude/memory/YYYY-MM-DD.md` に保存 (新規 file
   or 同日 `## Session N` として追記)
2. `_index.md` § エントリ に **1–2 行** bullet を追記
   (`- YYYY-MM-DD: <主題> (PR #NNN, ...)`、最新が下、≤ 500 chars)
3. **30 日以上前の dated entries を `archive/YYYY-MM/` に移送** (原文保存、
   `_index.md` 該当行は 1 行 summary + archive path に書換、`archive/INDEX.md`
   更新)
4. **`STATUS.md 次の発行順序` の sweep** ⚠️ step 5 より先。完走/merged した
   Phase / Brief / Milestone を `## 直近 merged` の新 entry に移送する。
   `tests/discipline/test_status_md_next_queue_no_completed.py` で enforce
5. **`STATUS.md ## 直近 merged` を最新 5 entries に compact**。超過分 (古い順)
   を `archive/STATUS_MERGED_LOG.md` 末尾に原文移送。step 4 の後に行うことで
   「sweep が cap 超過を再導入する」 race を回避
6. **`STATUS.md ## Phase` の単一段落 check**。新 paragraph 追加時は旧
   paragraph を必ず削除。`tests/discipline/test_status_md_phase_single_paragraph.py`
   で enforce
7. **5+ round 論点の encode check**。当 session で review / 壁打ちが 5 round
   以上に達した曖昧 spec があれば、その解決を docs / tests に encode 済か確認し、
   未 encode なら externalize する (round 数の test 化はしない — fragile proxy。
   `tests/discipline/README.md` 参照)。`CLAUDE.md` / `AGENTS.md` への更新候補が
   あればユーザーに提案する
8. **memory 直 push 前に `python -m pytest tests/discipline/` を実行し全 test
   pass を確認** ⚠️ gate。fail があれば step 4–6 の drift が残っているので push
   せず修正。memory exception (`.claude/memory/` 直 main push 許可) は
   **post-hoc 検出のみ** なので、discipline test 違反があると main が直接 red に
   なる。step 8 (数秒) で構造的に抑止する

### Archive policy (compaction TTL)

| Artifact | TTL | 移送先 | 移送後の本体 |
|---|---|---|---|
| dated session log `YYYY-MM-DD.md` | 30 日 | `archive/YYYY-MM/` | 原文保存 (情報損失ゼロ) |
| `_index.md` の対応 entry | 同上 | inline → 1 行 summary + archive path | archive file 経由で参照可 |
| `STATUS.md ## 直近 merged` entry | 直近 5 超過時 | `archive/STATUS_MERGED_LOG.md` 末尾 | 原文保存 |
| `STATUS.md 次の発行順序` の完走 entry | merge と同時 | `## 直近 merged` の新 entry | 完走宣言として保存 |
| `STATUS.md ## Phase` paragraph | 上書き時 | (保存しない、1 paragraph 厳守) | history は dated log / `_index.md` に分散 |

### サマリーの構成 (慣例フォーマット)

過去ファイルに合わせて以下のセクションで構成する:

- **コンテキスト** — そのセッションが何を扱ったか 1〜2 段落
- **設計判断** — なぜその選択をしたか
- **成功パターン** — 効いたアプローチ
- **修正・訂正** — バグ・誤認識の記録
- **工程サマリー** — 表形式で工程と成果
- **成果物** — マージされた PR / 追加ファイル
- **次セッションへの引き継ぎ** — 残課題
- **メモ** — 雑多な気づき

### Git Workflow の例外

`.claude/memory/` の運用ログのみ、main 直 push の唯一の例外として認められている。
これ以外の変更はすべて feature branch + PR の通常フローを守る。直 push の前に
`/wrap-up` step 8 gate (`python -m pytest tests/discipline/`) を必ず通すこと。

## Experience Externalization (経験値の外部化)

AI 開発 (Claude / Codex / 並列 agent 運用) は session 跨ぎの暗黙知を継承しない:
Claude は long-term memory を持たず、Codex は PR 単位の review trail 以外を学習
しない。user の壁打ち経験も永続化しない限り消失する。この制約下で再現性を維持
する唯一の方法は、経験値を **明示 artifact** に強制外部化することである:

- **docs** に encode (`docs/specs/` / `docs/*_planning.md`)
- **test** に encode (`tests/discipline/` の構造規律 test、engine の決定性 test)
- **checklist** に encode (`/new-brief` の §1 grounding gate)
- **STATUS / memory** に encode (`.claude/memory/`)

review round 数は leading quality indicator として運用する (詳細は `AGENTS.md`
§5)。PR #104 (13 rounds) はその base case で、planning doc を grounding 前に
起草した churn を吸収しきった経験を `/new-brief` の pre-flight gate に encode
した。新 brief 起草前 / 新 architectural pattern 導入前は `AGENTS.md` §5 を
逐語参照する。
