# ugh-quantamental

Minimal Python 3.11+ library implementing deterministic quantamental engines with persistence, workflow composition, read-only query inspection, deterministic replay, multi-run batch replay, and regression suite execution. All logic is synchronous, typed, schema-first, and connector-free.

## Features

- **Projection engine** — computes directional point estimates, conviction, urgency, and bounded projection snapshots from question/signal/alignment inputs
- **State engine** — updates lifecycle state probabilities via deterministic softmax blending over a 6-state simplex, driven by observable event features
- **Persistence scaffolding** — SQLAlchemy ORM-backed run records for projection and state runs; Alembic migration; naive-UTC `created_at` normalisation
- **Workflow layer** — synchronous composition: run engine → persist result → reload → return both (`run_projection_workflow`, `run_state_workflow`, `run_full_workflow`)
- **Query layer** — read-only inspection of persisted runs: lightweight summaries with filtering/pagination, full bundle rehydration with all typed models recovered from JSON
- **Replay layer** — deterministic single-run regression checking: reload a persisted run, rerun the engine with the original inputs, compare stored vs recomputed results field-by-field
- **Batch replay** — multi-run replay in one call: per-run isolation, aggregate mismatch / error / missing counts, optional deduplication
- **Regression suite** — named suite runner over batch replay cases: deterministic pass/fail per case, zero-run guard prevents false-positive green results
- **Frozen schema contracts** — all data models use `ConfigDict(extra="forbid", frozen=True)`; invariants enforced at construction time
- **Pure engine functions** — same inputs always produce the same output; no globals, no mutation, no I/O

## Requirements

- Python 3.11+
- Pydantic v2 (`>=2,<3`)
- SQLAlchemy v2 (`>=2,<3`)
- Alembic (`>=1.13,<2`)

## Installation

```bash
pip install -e .
```

## Project layout

```
src/ugh_quantamental/
├── schemas/              # frozen Pydantic v2 data contracts
│   ├── enums.py          # MarketRegime, MacroCycleRegime, LifecycleState, QuestionDirection
│   ├── market_svp.py     # StateProbabilities, Phi, MarketSVP
│   ├── ssv.py            # SSVSnapshot and Q/F/T/P/R/X blocks
│   ├── omega.py          # Omega observation-quality envelope
│   └── projection.py     # ProjectionSnapshot output contract
├── engine/               # pure deterministic engine functions
│   ├── projection.py     # 11 pure projection functions
│   ├── projection_models.py  # QuestionFeatures, SignalFeatures, AlignmentInputs, …
│   ├── state.py          # 8 pure state-lifecycle functions
│   └── state_models.py   # StateEventFeatures, StateConfig, StateEngineResult
├── persistence/          # SQLAlchemy/Alembic run persistence
│   ├── models.py         # ProjectionRunRecord, StateRunRecord ORM models
│   ├── repositories.py   # ProjectionRunRepository, StateRunRepository
│   ├── serializers.py    # Pydantic ↔ JSON helpers
│   └── db.py             # engine/session factory helpers
├── workflows/            # synchronous workflow composition layer
│   ├── models.py          # request/response models + make_run_id
│   └── runners.py         # run_projection_workflow, run_state_workflow, run_full_workflow
├── query/                # read-only inspection layer
│   ├── models.py          # ProjectionRunQuery, StateRunQuery, *Summary, *Bundle
│   └── readers.py         # list_*_summaries, get_*_bundle
└── replay/               # deterministic replay / regression layer
    ├── models.py          # *ReplayRequest, *ReplayComparison, *ReplayResult
    ├── runners.py         # replay_projection_run, replay_state_run
    ├── batch_models.py    # *BatchReplayRequest/Item/Aggregate/Result, BatchReplayStatus
    ├── batch.py           # replay_projection_batch, replay_state_batch
    ├── suite_models.py    # *SuiteCase, RegressionSuiteRequest/Aggregate/Result
    └── suites.py          # run_regression_suite

alembic/                  # Alembic migration environment
docs/specs/               # formal v1 specifications
tests/                    # mirrors src layout
```

## Usage

### Projection engine

```python
from ugh_quantamental.engine import (
    run_projection_engine,
    QuestionFeatures, SignalFeatures, AlignmentInputs, ProjectionConfig,
)
from ugh_quantamental.engine.projection_models import QuestionDirectionSign

q = QuestionFeatures(
    question_direction=QuestionDirectionSign.positive,
    q_strength=0.8, s_q=0.7, temporal_score=0.6,
)
sig = SignalFeatures(
    fundamental_score=0.4, technical_score=0.2, price_implied_score=0.1,
    context_score=1.0, grv_lock=0.7, regime_fit=0.6,
    narrative_dispersion=0.2, evidence_confidence=0.8, fire_probability=0.6,
)
align = AlignmentInputs(d_qf=0.2, d_qt=0.3, d_qp=0.4, d_ft=0.2, d_fp=0.2, d_tp=0.3)

result = run_projection_engine("my-question-id", 30, q, sig, align, ProjectionConfig())
print(result.projection_snapshot.point_estimate)   # float in [-1, 1]
print(result.projection_snapshot.confidence)       # float in [0, 1]
```

### State engine

```python
from ugh_quantamental.engine import run_state_engine, StateEventFeatures, StateConfig

events = StateEventFeatures(
    catalyst_strength=0.6, follow_through=0.5, pricing_saturation=0.3,
    disconfirmation_strength=0.2, regime_shock=0.1, observation_freshness=0.9,
)
result = run_state_engine(snapshot, omega, projection_result, events, StateConfig())
print(result.updated_market_svp.phi.dominant_state)   # LifecycleState member
print(result.transition_confidence)                   # float in [0, 1]
```

### Workflow (engine + persistence in one call)

```python
from sqlalchemy.orm import Session
from ugh_quantamental.persistence.db import create_db_engine, create_all_tables, create_session_factory
from ugh_quantamental.workflows.models import ProjectionWorkflowRequest
from ugh_quantamental.workflows.runners import run_projection_workflow

engine = create_db_engine()          # defaults to in-memory SQLite
create_all_tables(engine)
session: Session = create_session_factory(engine)()

req = ProjectionWorkflowRequest(
    projection_id="my-question-id", horizon_days=30,
    question_features=q, signal_features=sig,
    alignment_inputs=align,
)
result = run_projection_workflow(session, req)
session.commit()

print(result.engine_result.projection_snapshot.point_estimate)
print(result.persisted_run.created_at)   # naive UTC datetime
```

### Query (read-only inspection)

```python
from ugh_quantamental.query import ProjectionRunQuery
from ugh_quantamental.query.readers import list_projection_run_summaries, get_projection_run_bundle

summaries = list_projection_run_summaries(session, ProjectionRunQuery(projection_id="my-question-id"))
bundle = get_projection_run_bundle(session, run_id=summaries[0].run_id)
print(bundle.result.projection_snapshot.point_estimate)
```

### Replay (single-run regression check)

```python
from ugh_quantamental.replay import ProjectionReplayRequest
from ugh_quantamental.replay.runners import replay_projection_run

replay = replay_projection_run(session, ProjectionReplayRequest(run_id="proj-abc123"))
if replay is not None:
    print(replay.comparison.exact_match)          # True if engine output unchanged
    print(replay.comparison.point_estimate_diff)  # absolute diff (0.0 if exact match)
```

### Batch replay (multi-run regression check)

```python
from ugh_quantamental.replay import ProjectionBatchReplayRequest
from ugh_quantamental.replay.batch import replay_projection_batch

batch_req = ProjectionBatchReplayRequest(run_ids=("proj-abc123", "proj-def456"))
result = replay_projection_batch(session, batch_req)
print(result.aggregate.requested_count)   # 2
print(result.aggregate.mismatch_count)    # 0 if engine unchanged
```

### Regression suite (named pass/fail report)

```python
from ugh_quantamental.replay.suite_models import (
    RegressionSuiteRequest, ProjectionSuiteCase,
)
from ugh_quantamental.replay.suites import run_regression_suite

req = RegressionSuiteRequest(
    projection_cases=(
        ProjectionSuiteCase(name="smoke", run_ids=("proj-abc123",)),
    )
)
result = run_regression_suite(session, req)
print(result.aggregate.passed_case_count)  # 1 if exact match and at least one run
print(result.projection_cases[0].passed)   # True / False
```

## Development

```bash
ruff check .   # lint
pytest -q      # tests
```

Both must pass cleanly. CI enforces the same checks on every PR and push.

## Specification documents

Formal v1 specs live in `docs/specs/`:

| File | Covers |
|---|---|
| `ugh_market_ssv_v1.md` | Enum taxonomy and schema contracts (Milestones 1–3) |
| `ugh_projection_engine_v1.md` | Projection engine math and API (Milestone 4) |
| `ugh_state_engine_v1.md` | State lifecycle update functions and API (Milestone 5) |
| `ugh_persistence_v1.md` | Persistence scaffolding policy and schema (Milestone 6) |
| `ugh_workflow_v1.md` | Workflow composition layer and import policy (Milestone 7) |
| `ugh_query_v1.md` | Read-only query layer: summaries, filtering, bundle rehydration (Milestone 8) |
| `ugh_replay_v1.md` | Deterministic replay / regression layer and comparison policy (Milestone 9) |
| `ugh_batch_replay_v1.md` | Batch replay / experiment runner (Milestone 10) |
| `ugh_regression_suite_v1.md` | Regression suite runner and pass/fail policy (Milestone 11) |

## Out of scope

The following are intentionally not implemented:

- ML fitting, calibration, or learned weight matrices
- Stochastic/probabilistic filtering (particle filters, Kalman, etc.)
- External data connectors or API clients
- REST/gRPC service layer
- Async execution or background jobs
- Intra-day or high-frequency signal handling
