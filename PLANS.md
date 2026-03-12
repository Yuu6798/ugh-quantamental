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

## Next up

**Milestone 8 — TBD**

Candidate directions (not yet specced):
- Analytics or query layer over persisted runs
- Batch/multi-run orchestration
- Richer projection bounds or asymmetric confidence intervals

Do not implement any of the above without a formal spec in `docs/specs/`.

## Validation commands

```bash
ruff check .
pytest -q
```
