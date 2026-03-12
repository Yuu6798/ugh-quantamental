# AGENTS.md

## Repository status

`ugh-quantamental` is a deterministic Python 3.11+ library containing:

- **schemas** — frozen Pydantic v2 data contracts (enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot)
- **engine** — pure projection and state-lifecycle functions (Milestones 4–5)
- **persistence** — SQLAlchemy/Alembic-backed run records for projection and state runs (Milestone 6)
- **workflows** — synchronous composition layer: run engine → persist → reload → return (Milestone 7)

Milestones 1–7 are complete. All code is deterministic, synchronous, and connector-free.

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
