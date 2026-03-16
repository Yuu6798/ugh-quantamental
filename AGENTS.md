# AGENTS.md

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
- **fx_protocol** — FX daily prediction cycle: frozen contracts, calendar helpers, deterministic ID generation, daily forecast/outcome/evaluation workflows, GitHub Actions automation, and read-only weekly report aggregation

Milestones 1–17 are complete. All code is deterministic, synchronous, and connector-free.

## Durable working rules

- Keep diffs tightly scoped to the requested task.
- Use `/plan` for non-trivial work.
- Avoid network-dependent tests and checks.
- Do not modify tests unless explicitly required.
- Do not commit, push, or open a PR unless explicitly asked.

## Validation

Run these local checks when relevant:

```bash
ruff check .
pytest -q
```

Both must pass cleanly. CI enforces the same checks on every PR and push.
