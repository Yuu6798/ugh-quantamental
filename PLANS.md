# PLANS.md

## Completed milestones

| # | Milestone | Summary |
|---|---|---|
| 1 | Bootstrap | AGENTS.md, PLANS.md baseline; repo scaffold |
| 2 | Python project bootstrap | pyproject.toml, ruff, pytest, CI |
| 3 | Formal spec and schemas | Enum taxonomy, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot |
| 4 | Projection engine | 11 pure functions; `run_projection_engine` entry point |
| 5 | State engine | 8 pure functions; `run_state_engine` entry point |
| 6 | Persistence scaffolding | SQLAlchemy ORM records, Alembic migration, repositories with naive-UTC `created_at` |
| 7 | Workflow layer | Synchronous composition: run engine → persist → reload; `run_projection_workflow`, `run_state_workflow`, `run_full_workflow` |
| 8 | Query layer | Read-only inspection: summaries, filtering, full bundle rehydration from persisted records |
| 9 | Replay layer | Deterministic single-run replay / regression checking: reruns persisted runs, compares stored vs recomputed results |
| 10 | Batch replay / experiment runner | Multi-run replay in a single call; per-run isolation; aggregate mismatch and error reporting |
| 11 | Regression suite / report layer | Named suite runner over batch replay cases; deterministic pass/fail per case; zero-run guard |
| 12 | Baseline / golden snapshot management | Persist named suite results; compare future reruns against a pinned baseline; per-`(group, name)` case deltas |
| 13 | FX Daily Protocol v1 — schema and calendar | Frozen Pydantic contracts (ForecastRecord, OutcomeRecord, EvaluationRecord), deterministic calendar helpers, deterministic ID generation |
| 14 | FX Daily Forecast Workflow | `run_daily_forecast_workflow`: generates and persists one UGH + three baseline forecasts per business day; idempotent |
| 15 | FX Daily Outcome/Evaluation Workflow | `run_daily_outcome_evaluation_workflow`: records the canonical outcome and four per-forecast evaluations; idempotent |
| 16 | FX Daily Automation | `run_fx_daily_protocol_once`: data-source abstraction, deterministic request builders, GitHub Actions daily schedule, durable SQLite via `fx-daily-data` git branch |
| 17 | FX Weekly Report | Read-only `run_weekly_report`: aggregates persisted evaluation records into strategy metrics, baseline comparisons, state/GRV/mismatch summaries, and curated case examples; `WeeklyReportRequest` / `WeeklyReportResult` frozen models; JST-canonical `report_generated_at_jst` field |
| 18 | FX Monthly Review | Read-only `run_monthly_review` / `rebuild_monthly_review`: aggregates a month of evaluation records into per-strategy / baseline-comparison / state / regime / volatility / intervention / event-tag metrics, provider-health summary, representative cases, rule-based review flags, and recommendation summary; per-variant `range_hit` (v2.3); emits JSON / MD / CSV artifacts; spec `docs/specs/fx_monthly_review_v1.md`; automated via `fx-monthly-review.yml` and `fx-analysis-pipeline.yml` |

## Next up

Milestones 1–18 and the 2026-05 engine review (Phases P0–P4 + Phase B) are
complete. There is no committed next milestone.

The natural next major direction is an **execution / trading layer** that
consumes engine outputs (state lifecycle, conviction, `expected_close_change_bp`,
per-variant `expected_range`) for position sizing — the prerequisite-integration
goal that `docs/engine_review_2026_05_planning.md` §8 / §11.3 deferred to a
trading system. This is a large new scope and requires its own planning doc in
`docs/specs/` before implementation.

## Validation commands

```bash
ruff check .
pytest -q
```
