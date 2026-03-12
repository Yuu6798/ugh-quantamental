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

## Next up

**Milestone 12 — Baseline / golden snapshot management**

Persist a named "golden" replay result so that future regression suites can compare
against a pinned baseline rather than only the live engine output.
Requires: a new persistence table or JSON sidecar policy, a formal spec in `docs/specs/`.

## Validation commands

```bash
ruff check .
pytest -q
```
