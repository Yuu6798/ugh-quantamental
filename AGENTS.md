# AGENTS.md

## Repository status
This repository is currently a very small bootstrap utility/library-style repo with almost no application code yet.

## Durable working rules
- Keep diffs tightly scoped to the requested task.
- Use `/plan` for non-trivial work.
- Avoid network-dependent tests and checks.
- Do not modify tests unless explicitly required.
- Do not commit, push, or open a PR unless explicitly asked.

## Validation
Run these local checks when relevant:
- `ruff check .`
- `pytest -q`
