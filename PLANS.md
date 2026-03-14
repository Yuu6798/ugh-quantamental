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

## Next up

**Milestone 17 — Weekly FX reporting**

Aggregate per-day evaluation records (direction hit rate, MAE, range hit rate) into
a weekly summary report for USDJPY.  Requires: a reporting layer function, a formal
spec in `docs/specs/`, and a scheduled GitHub Actions step that runs on Saturdays.

## Validation commands

```bash
ruff check .
pytest -q
```
