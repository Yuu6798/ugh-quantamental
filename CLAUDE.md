# CLAUDE.md

Guidelines for AI assistants working in this repository.

## Repository overview

`ugh-quantamental` is a Python 3.11+ library. Core packages (`schemas`, `engine`, `persistence`, `workflows`, `query`, `replay`) are deterministic and make no network calls. `fx_protocol` and `review_autofix` depend on live external state (APIs, GitHub). The codebase is schema-first, synchronous, and typed throughout — a research/scaffold tool, not a production application.

| Package | Description |
|---|---|
| `schemas` | Frozen Pydantic v2 data contracts — enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot |
| `engine` | Pure projection, state-lifecycle, and review-audit functions; no I/O, no stochastic behaviour |
| `persistence` | SQLAlchemy v2 ORM run records with Alembic migration; naive-UTC `created_at` policy |
| `workflows` | Synchronous composition layer: run engine → persist → reload → return result |
| `query` | Read-only inspection layer: summaries, filtering, and full bundle rehydration from persisted records |
| `replay` | Deterministic replay / regression checker (single-run, batch, suites, baselines) |
| `fx_protocol` | FX daily prediction protocol: forecasting, outcomes, evaluation, CSV exports, weekly reports, automation |
| `review_autofix` | PR review autofix bot: classifier, feature extraction, rule engine, GitHub integration |

Milestones 1–17 are complete across two phases. Phase 1 (M1–12): core engine, persistence, workflows, query, replay. Phase 2 (M13–17): `fx_protocol` daily prediction cycle. `review_autofix` ships outside the milestone sequence. See `docs/specs/` for formal specifications per milestone.

---

## Validation commands

Always run these before considering any change done:

```bash
ruff check .   # lint
pytest -q      # tests
```

Both must pass cleanly. CI enforces the same checks on every PR and push.

---

## Project layout

```
src/ugh_quantamental/
├── schemas/          # Enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot
├── engine/           # projection.py, state.py, review_audit.py + their *_models.py
├── persistence/      # ORM models, repositories, serializers, db helpers
├── workflows/        # models.py (SQLAlchemy-free), runners.py (DB-dependent; includes review-audit)
├── query/            # models.py (SQLAlchemy-free), readers.py (DB-dependent; includes review-audit)
├── replay/           # models, runners (includes review-audit), batch, suites, baselines (read-only except baseline writes)
├── fx_protocol/      # calendar, ids, data_models, data_sources, request_builders (contracts);
│                     #   models, forecast_models, outcome_models, report_models (schemas);
│                     #   forecasting, outcomes, csv_exports, reporting, automation (application)
└── review_autofix/   # bot (orchestrator), task_builder, validator, codex_executor (execution);
                      #   models, executor_models (contracts);
                      #   classifier, feature_extractor, rules, config, state_store, git_ops, github_client

alembic/versions/     # 0001 initial → 0002 baselines → 0003–0004 fx → 0005 review_audit
scripts/              # run_fx_daily_protocol.py — CLI entrypoint for FX automation
.github/workflows/    # ci.yml, fx-daily-protocol.yml, review-autofix.yml
                      #   review-autofix.yml uses trusted checkout: base→trusted-bot/, PR→pr-head/,
                      #   PYTHONPATH forced to trusted-bot/src to prevent untrusted code execution
tests/                # mostly mirrors src/; some integration tests span multiple modules
                      #   (e.g. test_automation.py, test_task_builder_executor.py)
docs/specs/           # formal v1 specifications per milestone
```

When implementing a new milestone, read the corresponding spec in `docs/specs/` first.

---

## Technology stack

| Tool | Purpose |
|---|---|
| Python 3.11+ | Language — f-strings, `match`, `Self`, `from __future__ import annotations` |
| Pydantic v2 (`>=2,<3`) | Schema contracts — all models are `extra="forbid", frozen=True` |
| SQLAlchemy v2 (`>=2,<3`) | ORM for persistence run records; `DateTime(timezone=False)` columns |
| Alembic (`>=1.13,<2`) | Schema migration for persistence tables |
| ruff | Linter and formatter — line length 100, target `py311` |
| pytest | Test runner — quiet mode, `src/` on `PYTHONPATH` |
| GitHub Actions | CI on PR and push to main |

Core packages make no external network calls. `fx_protocol` and `review_autofix` contain HTTP-backed integrations (API keys, GitHub/OpenAI).

---

## Architecture invariants

These rules are non-negotiable for core packages (`schemas`, `engine`, `persistence`, `workflows`, `query`, `replay`). `fx_protocol` and `review_autofix` contain intentional side effects (HTTP calls, `datetime.now()`, API integrations) — purity and determinism invariants do not apply to those packages.

- **Pure engine functions.** All engine logic is pure: same inputs → same output. No globals, no mutation, no I/O.
- **Frozen immutable schemas.** All Pydantic models use `model_config = ConfigDict(extra="forbid", frozen=True)`. Never mutate; construct a new instance.
- **Deterministic and bounded.** All intermediate values are clamped or normalised to known ranges. Validators enforce invariants (probabilities sum to 1, dominant state is unique).
- **Naive-UTC persistence.** `created_at` is normalised to naive UTC at the repository boundary via `_normalize_created_at`. ORM columns use `DateTime(timezone=False)`.
- **Workflow flush-only.** Workflows flush but never commit; the caller owns the session and transaction boundary.
- **Import isolation.** `workflows.models`, `query.__init__`, and `replay.__init__` must be importable without SQLAlchemy. DB-dependent functions live in `runners.py`, `readers.py`, `batch.py`, `suites.py`, `baselines.py` and require SQLAlchemy at call time. SQLAlchemy-transitive imports (e.g. `run_regression_suite`) must be deferred inside function bodies.
- **Read-only replay.** All replay runners (`runners.py`, `batch.py`, `suites.py`) and `baselines.py` never write, flush, or commit during read operations. Regression suites fail when `requested_count == 0` to prevent false-positive passes on empty queries. Baseline deltas are computed per `(group, name)` pair — never flatten to a single-name map.
- **Review-audit boundary.** Raw review text never enters `run_review_audit_engine` directly — it must pass through the extractor first. Extractor replay is separate from engine replay. Bot integration is shadow-only: verdicts are persisted and logged but never block pushes.

---

## Development conventions

### Code style
- Line length: 100 characters (ruff enforces this)
- Python 3.11+ syntax only; `from __future__ import annotations` on all new modules
- Type annotations on all function signatures
- Docstrings on public functions and classes
- No bare `except`; be explicit about exception types

### Adding new schemas
1. Define the model in `src/ugh_quantamental/schemas/` with `extra="forbid", frozen=True`
2. Add validators with `@field_validator` or `@model_validator`
3. Add a corresponding test file in `tests/schemas/`

### Adding new engine functions
1. Add the pure function to the appropriate `engine/*.py` module
2. Add it to `engine/__init__.py` `__all__`
3. All inputs must be normalised/bounded before use
4. Return typed output (Pydantic model or plain scalar)
5. Add tests in the corresponding `tests/engine/` file

### Working with persistence
- Do not redesign ORM column types without a migration
- Keep `DateTime(timezone=False)` — use `_normalize_created_at` at the repository boundary
- SQLAlchemy-dependent tests use `@pytest.mark.skipif(not HAS_SQLALCHEMY, ...)`
- Persistence test imports that need SQLAlchemy go inside test function bodies

### Working with workflows
- `workflows.models` must remain importable without SQLAlchemy
- Runner imports go inside test function bodies or behind `HAS_SQLALCHEMY` guards
- Workflows flush but do not commit; the caller owns the transaction

### Working with query and replay
- `query.__init__` and `replay.__init__` must remain importable without SQLAlchemy
- Reader and runner imports go inside test function bodies or behind `HAS_SQLALCHEMY` guards
- All replay runners (`runners.py`, `batch.py`, `suites.py`) and `baselines.py` must not write, flush, or commit during read operations
- `baselines.py` defers `run_regression_suite` import inside DB-dependent function bodies to avoid transitive SQLAlchemy imports at module load time
- Query bundle rehydration must use named attribute access (`record.foo_json`), never `record.__dict__` — deferred `load_only(...)` columns are silently omitted from `__dict__` when the row is already in the identity map

### Tests
- Do not modify existing tests unless explicitly required
- New tests follow the existing pattern: parametrised for multiple cases, single-case for edge conditions
- No network calls, no file I/O, no randomness
- Test filenames mostly mirror source filenames; some integration tests span multiple modules

### Commits and PRs
- Do not commit, push, or open a PR unless explicitly asked
- Keep diffs tightly scoped
- Use `/plan` for non-trivial work

### How to create a pull request

This environment has no GitHub API credentials, so PRs cannot be created programmatically.
After committing and pushing the branch, provide the user with this URL to open a PR manually:

```
https://github.com/Yuu6798/ugh-quantamental/compare/main...<branch-name>
```

Always include a ready-to-paste PR title and body (markdown) alongside the link.
