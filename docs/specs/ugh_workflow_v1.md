# UGH Workflow v1 — Deterministic workflow composition layer

## Why this layer exists

Milestones 1–6 established deterministic engine math (projection, state) and a persistence adapter
(run records stored as JSON-backed SQLAlchemy rows). Those layers are intentionally decoupled — the
engines know nothing about persistence, and the repositories know nothing about engine sequencing.

The workflow layer exists to compose them into a single callable unit:
- run engine → persist result → reload persisted run → return both.

This removes repetitive glue code from callers and provides a stable, testable boundary for
end-to-end deterministic execution.

---

## Workflow functions

### `run_projection_workflow(session, request) -> ProjectionWorkflowResult`

1. Calls `run_projection_engine(projection_id, horizon_days, question_features, signal_features,
   alignment_inputs, config)`.
2. Persists the result via `ProjectionRunRepository.save_run(...)`.
3. Reloads the persisted run via `ProjectionRunRepository.load_run(run_id)`.
4. Returns a `ProjectionWorkflowResult` containing both the engine result and the reloaded run.

**Inputs (`ProjectionWorkflowRequest`):**
- `projection_id: str` — caller-supplied stable identifier for the question/projection
- `horizon_days: int` — forecast horizon in calendar days (ge=1)
- `question_features: QuestionFeatures`
- `signal_features: SignalFeatures`
- `alignment_inputs: AlignmentInputs`
- `config: ProjectionConfig` — defaults to `ProjectionConfig()`
- `run_id: str | None` — optional; generated internally if omitted
- `created_at: datetime | None` — optional; defaults to current UTC at persistence boundary

**Outputs (`ProjectionWorkflowResult`):**
- `run_id: str`
- `engine_result: ProjectionEngineResult`
- `persisted_run: ProjectionRun`

---

### `run_state_workflow(session, request) -> StateWorkflowResult`

1. Calls `run_state_engine(snapshot, omega, projection_result, event_features, config)`.
2. Persists the result via `StateRunRepository.save_run(...)`.
3. Reloads via `StateRunRepository.load_run(run_id)`.
4. Returns a `StateWorkflowResult` containing both.

**Inputs (`StateWorkflowRequest`):**
- `snapshot: SSVSnapshot`
- `omega: Omega`
- `projection_result: ProjectionEngineResult`
- `event_features: StateEventFeatures`
- `config: StateConfig` — defaults to `StateConfig()`
- `snapshot_id: str | None` — optional; taken from `snapshot.snapshot_id` if omitted
- `omega_id: str | None` — optional; taken from `omega.omega_id` if omitted
- `projection_id: str | None` — optional; taken from `projection_result.projection_snapshot.projection_id`
- `run_id: str | None` — optional; generated internally if omitted
- `created_at: datetime | None` — optional

**Outputs (`StateWorkflowResult`):**
- `run_id: str`
- `engine_result: StateEngineResult`
- `persisted_run: StateRun`

---

### `run_full_workflow(session, request) -> FullWorkflowResult`

Composes projection and state workflows in sequence:

1. Runs `run_projection_workflow` with the projection sub-request.
2. Passes the resulting `ProjectionEngineResult` as `projection_result` into the state sub-request.
3. Propagates `projection_id` from the projection snapshot into state persistence.
4. Both runs share the same `session`; the caller owns the transaction boundary (commit/rollback).

**Inputs (`FullWorkflowRequest`):**
- `projection: ProjectionWorkflowRequest`
- `state: FullWorkflowStateRequest` — a dedicated model that omits `projection_result`;
  the workflow injects it automatically from the projection step output.
  `projection_id` is also derived from the projection snapshot and does not need to be supplied.

**`FullWorkflowStateRequest` fields:**
- `snapshot: SSVSnapshot`
- `omega: Omega`
- `event_features: StateEventFeatures`
- `config: StateConfig` — defaults to `StateConfig()`
- `snapshot_id: str | None` — optional; taken from `snapshot.snapshot_id` if omitted
- `omega_id: str | None` — optional; taken from `omega.omega_id` if omitted
- `run_id: str | None` — optional; generated internally if omitted
- `created_at: datetime | None` — optional

**Outputs (`FullWorkflowResult`):**
- `projection: ProjectionWorkflowResult`
- `state: StateWorkflowResult`

---

## ID generation

`make_run_id(prefix: str) -> str` generates a short opaque identifier using `uuid4`, prefixed with
the supplied string for readability (e.g. `"proj-"`, `"state-"`). The format is
`"{prefix}{uuid4_hex[:12]}"`. Callers may supply their own `run_id` in the request to override.

## Import policy

Request/response model classes are importable without SQLAlchemy:

```python
from ugh_quantamental.workflows.models import (
    ProjectionWorkflowRequest, StateWorkflowRequest,
    FullWorkflowRequest, FullWorkflowStateRequest,
)
```

Runner functions require SQLAlchemy and must be imported directly from the submodule:

```python
from ugh_quantamental.workflows.runners import (
    run_projection_workflow, run_state_workflow,
    run_full_workflow, make_run_id,
)
```

---

## Transaction policy

- Workflows call `session.flush()` (via the repository `save_run` methods) but **do not commit**.
- The caller owns the session and is responsible for committing or rolling back.
- Persistence errors propagate directly to the caller; workflows do not swallow exceptions.

---

## Intentionally deferred beyond v1

- Batch orchestration (multiple runs in a single call)
- Background/async execution
- Queue-based or event-driven triggering
- REST/gRPC API layer
- External data connectors or feed adapters
- Analytics views, derived marts, or reporting pipelines
- Retry logic or circuit breakers
- Dependency injection framework
