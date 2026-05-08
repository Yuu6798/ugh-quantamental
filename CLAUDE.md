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

ユーザーが終了意図を示すフレーズを発したら、確認なしで即座に `/wrap-up` 相当の
処理 (memory への振り返りサマリー保存 + `_index.md` 追記) を実行する。

トリガーフレーズの例:
- 「今日はここまで」「今日は終わり」「今日はおわり」
- 「セッション終了」「セッション閉じて」
- 「また明日」「また今度」「お疲れ様」「お疲れさま」
- 「done for today」「that's all」
- 手動: `/wrap-up`

実行内容:
- 会話の振り返りサマリーを `.claude/memory/YYYY-MM-DD.md` に保存
- `_index.md` に 1 行サマリーを追記
- `CLAUDE.md` への更新候補があればユーザーに提案する

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
これ以外の変更はすべて feature branch + PR の通常フローを守る。
