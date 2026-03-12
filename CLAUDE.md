# CLAUDE.md

Guidelines for AI assistants working in this repository.

## Repository overview

`ugh-quantamental` is a deterministic Python 3.11+ library. It is schema-first, synchronous, connector-free, and typed throughout. It contains eight active packages:

| Package | Description |
|---|---|
| `schemas` | Frozen Pydantic v2 data contracts — enums, SSVSnapshot, Omega, MarketSVP, ProjectionSnapshot |
| `engine` | Pure projection and state-lifecycle functions; no I/O, no stochastic behaviour |
| `persistence` | SQLAlchemy v2 ORM run records with Alembic migration; naive-UTC `created_at` policy |
| `workflows` | Synchronous composition layer: run engine → persist → reload → return result |
| `query` | Read-only inspection layer: summaries, filtering, and full bundle rehydration from persisted records |
| `replay` | Single-run deterministic replay / regression checker |
| `replay.batch` | Multi-run batch replay with per-run isolation and aggregate reporting |
| `replay.suites` | Named regression suite runner with deterministic pass/fail reporting |

Milestones 1–11 are complete. The codebase is a research/scaffold tool, not a production application.

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
├── __init__.py
├── schemas/
│   ├── enums.py              # MarketRegime, MacroCycleRegime, LifecycleState, QuestionDirection
│   ├── market_svp.py         # StateProbabilities, Phi, MarketSVP
│   ├── ssv.py                # SSVSnapshot and Q/F/T/P/R/X blocks
│   ├── omega.py              # Omega observation-quality envelope
│   └── projection.py         # ProjectionSnapshot output contract
├── engine/
│   ├── __init__.py           # re-exports all public names via __all__
│   ├── projection.py         # 11 pure projection functions
│   ├── projection_models.py  # QuestionFeatures, SignalFeatures, AlignmentInputs, ProjectionConfig, ProjectionEngineResult
│   ├── state.py              # 8 pure state-lifecycle functions
│   └── state_models.py       # StateEventFeatures, StateConfig, StateEngineResult
├── persistence/
│   ├── __init__.py           # package exports
│   ├── models.py             # ProjectionRunRecord, StateRunRecord (SQLAlchemy ORM)
│   ├── repositories.py       # ProjectionRunRepository, StateRunRepository; _normalize_created_at
│   ├── serializers.py        # dump_model_json / load_model_json helpers
│   └── db.py                 # create_db_engine, create_all_tables, create_session_factory
├── workflows/
│   ├── __init__.py            # exports model classes and make_run_id (SQLAlchemy-free)
│   ├── models.py              # request/response models + make_run_id
│   └── runners.py             # run_projection_workflow, run_state_workflow, run_full_workflow
├── query/
│   ├── __init__.py            # exports query/summary/bundle models (SQLAlchemy-free)
│   ├── models.py              # ProjectionRunQuery, StateRunQuery, *Summary, *Bundle
│   └── readers.py             # list_projection_run_summaries, list_state_run_summaries, get_*_bundle
└── replay/
    ├── __init__.py            # exports all model classes (SQLAlchemy-free)
    ├── models.py              # *ReplayRequest, *ReplayComparison, *ReplayResult
    ├── runners.py             # replay_projection_run, replay_state_run
    ├── batch_models.py        # *BatchReplayRequest/Item/Aggregate/Result, BatchReplayStatus
    ├── batch.py               # replay_projection_batch, replay_state_batch
    ├── suite_models.py        # *SuiteCase, RegressionSuiteRequest/Aggregate/Result
    └── suites.py              # run_regression_suite

alembic/                       # Alembic migration environment
alembic/versions/              # migration scripts

tests/
├── test_import_smoke.py
├── engine/
│   ├── test_projection.py
│   ├── test_projection_models.py
│   ├── test_state.py
│   └── test_state_models.py
├── schemas/
│   ├── test_market_svp.py
│   ├── test_omega.py
│   ├── test_projection.py
│   └── test_ssv.py
├── persistence/
│   ├── test_db.py
│   └── test_repositories.py
├── workflows/
│   ├── conftest.py
│   ├── test_models.py
│   └── test_runners.py
├── query/
│   ├── conftest.py
│   └── test_readers.py
└── replay/
    ├── conftest.py
    ├── test_models.py
    ├── test_runners.py
    ├── test_batch_models.py
    ├── test_batch.py
    ├── test_suite_models.py
    └── test_suites.py

docs/specs/                    # formal v1 specifications
```

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

No external network calls, no secrets, no environment variables.

---

## Architecture principles

### Pure engine functions
All engine logic is pure: same inputs always produce the same output. Functions in `engine/projection.py` and `engine/state.py` take plain Python floats/models and return computed values or Pydantic models. No globals, no mutation.

### Frozen immutable schemas
All Pydantic models use `model_config = ConfigDict(extra="forbid", frozen=True)`. Never mutate a schema instance; construct a new one.

### Deterministic and bounded
Both engines are explicitly deterministic. All intermediate values are clamped or normalised to known ranges before being written into output contracts. Validators enforce invariants (probabilities sum to 1, dominant state is unique).

### Persistence: naive-UTC timestamps
`created_at` is normalised to naive UTC at the repository save boundary via `_normalize_created_at`. Timezone-aware inputs are converted to UTC first; naive inputs are treated as already UTC. ORM columns use `DateTime(timezone=False)`.

### Workflow composition
Workflows are thin, synchronous wrappers: call an engine function, persist via the repository, reload the persisted run, return both. The caller owns the session and transaction boundary. Workflows do not commit; they flush only.

### Import isolation
`workflows.models`, `query.__init__`, and `replay.__init__` are all importable without SQLAlchemy. Functions that touch the database must be imported from their respective `runners.py`, `readers.py`, `batch.py`, or `suites.py` submodules and require SQLAlchemy at call time.

### Query layer (read-only)
`query/readers.py` provides list and bundle-fetch functions over persisted run records. Summaries use `load_only` to fetch minimal columns. Bundle fetches use named attribute access (not `__dict__`) so SQLAlchemy's deferred-load mechanism fires correctly.

### Replay layer (read-only, diagnostic)
`replay/runners.py` reloads a persisted bundle via the query layer, reruns the deterministic engine with the recovered typed inputs, and compares stored vs recomputed results. Replay runners never write, flush, or commit the session.

### Batch replay layer (read-only, multi-run)
`replay/batch.py` runs multiple replay operations in a single call. Each run is isolated: an error in one run does not abort the others. Results are collected into per-item comparison results and an aggregate summary (`requested_count`, `replayed_count`, `missing_count`, `error_count`, `mismatch_count`).

### Regression suite layer (read-only, named pass/fail)
`replay/suites.py` runs named batch replay cases and computes a deterministic pass/fail result per case. A case passes iff `requested_count > 0` and `error_count == missing_count == mismatch_count == 0`. A zero-run case is always a failure — it provides no coverage and must not produce a false-positive green result.

---

## Key domain concepts

### Enumerations (`schemas/enums.py`)
- `MarketRegime` — `risk_on | neutral | risk_off`
- `MacroCycleRegime` — `expansion | slowdown | contraction | recovery | reflation | stagflation`
- `LifecycleState` — `dormant | setup | fire | expansion | exhaustion | failure`
- `QuestionDirection` — `positive | negative | neutral`

### Schema contracts
- `StateProbabilities` — 6-float simplex over `LifecycleState` (sums to 1.0 ± 1e-6)
- `Phi` — lifecycle state envelope: `StateProbabilities` + unique `dominant_state`
- `MarketSVP` — top-level market state vector: `regime`, `phi`, `confidence`
- `SSVSnapshot` — multi-block snapshot: Q/F/T/P/R/X blocks
- `Omega` — observation-quality envelope with per-block `BlockObservability`
- `ProjectionSnapshot` — `projection_id`, `horizon_days`, `point_estimate`, `lower_bound`, `upper_bound`, `confidence`

### Projection engine (`engine/projection.py`)
Entry point: `run_projection_engine(projection_id, horizon_days, q, sig, align, cfg)` → `ProjectionEngineResult`.

Functions (in order): `compute_u` → `compute_alignment` → `compute_e_raw` → `compute_gravity_bias` → `compute_e_star` → `compute_mismatch_px` → `compute_mismatch_sem` → `compute_conviction` → `compute_urgency` → `build_projection_snapshot` → composed by `run_projection_engine`.

### State engine (`engine/state.py`)
Entry point: `run_state_engine(snapshot, omega, projection_result, event_features, cfg)` → `StateEngineResult`.

Functions (in order): `compute_block_quality` → `compute_state_evidence` → `normalize_state_probabilities` → `blend_with_prior` → `resolve_dominant_state` → `build_phi` → `build_market_svp` → composed by `run_state_engine`.

### Persistence repositories
- `ProjectionRunRepository.save_run(session, *, run_id, projection_id, ...)` — persists full JSON payload
- `ProjectionRunRepository.load_run(session, run_id)` → `ProjectionRun | None`
- `StateRunRepository.save_run(session, *, run_id, snapshot_id, omega_id, ...)` — persists full JSON payload
- `StateRunRepository.load_run(session, run_id)` → `StateRun | None`

### Workflow layer
- `make_run_id(prefix)` → short `"{prefix}{uuid4_hex[:12]}"` identifier (importable without SQLAlchemy)
- `run_projection_workflow(session, request)` → `ProjectionWorkflowResult`
- `run_state_workflow(session, request)` → `StateWorkflowResult`
- `run_full_workflow(session, request)` → `FullWorkflowResult` (projection then state, same session)
- `FullWorkflowRequest.state` is `FullWorkflowStateRequest` — does not carry `projection_result` (injected automatically)

### Query layer
- `list_projection_run_summaries(session, query)` → `list[ProjectionRunSummary]`
- `list_state_run_summaries(session, query)` → `list[StateRunSummary]`
- `get_projection_run_bundle(session, run_id)` → `ProjectionRunBundle | None`
- `get_state_run_bundle(session, run_id)` → `StateRunBundle | None`
- Import models from `query.__init__`; import reader functions from `query.readers`

### Replay layer
- `replay_projection_run(session, request)` → `ProjectionReplayResult | None`
- `replay_state_run(session, request)` → `StateReplayResult | None`
- Returns `None` if `run_id` is not found; read-only, no writes
- Import models from `replay.__init__`; import runners from `replay.runners`

### Batch replay layer
- `replay_projection_batch(session, request)` → `ProjectionBatchReplayResult`
- `replay_state_batch(session, request)` → `StateBatchReplayResult`
- Each run is isolated: errors do not abort the batch; aggregate counts include `missing_count` and `error_count`
- Import models from `replay.__init__`; import batch functions from `replay.batch`

### Regression suite layer
- `run_regression_suite(session, request)` → `RegressionSuiteResult`
- `RegressionSuiteRequest` — tuple of named `ProjectionSuiteCase` and/or `StateSuiteCase` objects
- Each case provides `name` and exactly one of `run_ids` or `query`
- Pass condition: `requested_count > 0` and `error_count == missing_count == mismatch_count == 0`
- Import models from `replay.suite_models`; import runner from `replay.suites`

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
- All replay runners (`runners.py`, `batch.py`, `suites.py`) must not write, flush, or commit; they are diagnostic only

### Tests
- Do not modify existing tests unless explicitly required
- New tests follow the existing pattern: parametrised for multiple cases, single-case for edge conditions
- No network calls, no file I/O, no randomness
- Test filenames mirror source filenames

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

---

## Specification documents

| File | Covers |
|---|---|
| `docs/specs/ugh_market_ssv_v1.md` | Enum taxonomy and schema contracts (Milestones 1–3) |
| `docs/specs/ugh_projection_engine_v1.md` | Projection engine math and API (Milestone 4) |
| `docs/specs/ugh_state_engine_v1.md` | State lifecycle update functions and API (Milestone 5) |
| `docs/specs/ugh_persistence_v1.md` | Persistence scaffolding policy and schema (Milestone 6) |
| `docs/specs/ugh_workflow_v1.md` | Workflow composition layer and import policy (Milestone 7) |
| `docs/specs/ugh_query_v1.md` | Read-only query layer: summaries, filtering, bundle rehydration (Milestone 8) |
| `docs/specs/ugh_replay_v1.md` | Deterministic replay / regression layer and comparison policy (Milestone 9) |
| `docs/specs/ugh_batch_replay_v1.md` | Batch replay / experiment runner (Milestone 10) |
| `docs/specs/ugh_regression_suite_v1.md` | Regression suite runner and pass/fail policy (Milestone 11) |

When implementing a new milestone, read the corresponding spec first.

---

## What is intentionally out of scope

- ML fitting, calibration, or learned weight matrices
- Stochastic/probabilistic filtering (particle filters, Kalman, etc.)
- External data connectors or API clients
- REST/gRPC service layer
- Async execution or background jobs
- Batch orchestration framework
- Analytics views or derived marts
- Intra-day or high-frequency signal handling
