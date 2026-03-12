# ugh_replay_v1 — Deterministic Replay / Regression Layer

## Why replay exists in a deterministic repository

`ugh-quantamental` engines are deterministic: given identical inputs, they always produce
identical outputs. Replay exploits this property to verify that a persisted run is still
reproducible against the current version of the engine code.

Use cases:

- **Regression checks** — confirm that an engine refactor has not silently changed any
  outputs for any previously persisted run.
- **Audit trails** — spot-check that the stored JSON payloads faithfully represent what
  the engine would compute today.
- **Snapshot diffing** — detect unexpected drift when engine coefficients or config
  defaults change.

Because the engine is pure and connector-free, replay requires only: a live database
session and a `run_id`.  No network access, no external state, no randomness.

---

## Projection replay flow

```
run_id
  │
  ▼
get_projection_run_bundle(session, run_id)   ← query layer; read-only
  │
  ├── None  →  return None
  │
  ▼
ProjectionRunBundle
  │  .question_features, .signal_features,
  │  .alignment_inputs, .config, .result
  │
  ▼
run_projection_engine(
    projection_id = bundle.projection_id,
    horizon_days  = bundle.result.projection_snapshot.horizon_days,
    question_features = bundle.question_features,
    signal_features   = bundle.signal_features,
    alignment_inputs  = bundle.alignment_inputs,
    config            = bundle.config,
)
  │
  ▼
ProjectionEngineResult  (recomputed)
  │
  ▼
_compare_projection(stored=bundle.result, recomputed=recomputed)
  │
  ▼
ProjectionReplayComparison
  │
  ▼
ProjectionReplayResult(bundle, recomputed_result, comparison)
```

---

## State replay flow

```
run_id
  │
  ▼
get_state_run_bundle(session, run_id)   ← query layer; read-only
  │
  ├── None  →  return None
  │
  ▼
StateRunBundle
  │  .snapshot, .omega, .projection_result,
  │  .event_features, .config, .result
  │
  ▼
run_state_engine(
    snapshot          = bundle.snapshot,
    omega             = bundle.omega,
    projection_result = bundle.projection_result,
    event_features    = bundle.event_features,
    config            = bundle.config,
)
  │
  ▼
StateEngineResult  (recomputed)
  │
  ▼
_compare_state(stored=bundle.result, recomputed=recomputed)
  │
  ▼
StateReplayComparison
  │
  ▼
StateReplayResult(bundle, recomputed_result, comparison)
```

---

## Comparison policy

Comparisons are **explicit and minimal**.  There is no generic recursive diff engine.
Only a small, documented set of fields is compared.

### Projection comparison (`ProjectionReplayComparison`)

| Field | Type | How computed |
|---|---|---|
| `exact_match` | `bool` | `stored.model_dump(mode="json") == recomputed.model_dump(mode="json")` |
| `projection_snapshot_match` | `bool` | snapshot sub-object JSON equality |
| `point_estimate_diff` | `float` | `abs(recomputed.projection_snapshot.point_estimate − stored.projection_snapshot.point_estimate)` |
| `confidence_diff` | `float` | `abs(recomputed.projection_snapshot.confidence − stored.projection_snapshot.confidence)` |
| `mismatch_px_diff` | `float` | `abs(recomputed.mismatch_px − stored.mismatch_px)` |
| `mismatch_sem_diff` | `float` | `abs(recomputed.mismatch_sem − stored.mismatch_sem)` |
| `conviction_diff` | `float` | `abs(recomputed.conviction − stored.conviction)` |
| `urgency_diff` | `float` | `abs(recomputed.urgency − stored.urgency)` |

### State comparison (`StateReplayComparison`)

| Field | Type | How computed |
|---|---|---|
| `exact_match` | `bool` | `stored.model_dump(mode="json") == recomputed.model_dump(mode="json")` |
| `dominant_state_match` | `bool` | `recomputed.dominant_state == stored.dominant_state` |
| `transition_confidence_diff` | `float` | `abs(recomputed.transition_confidence − stored.transition_confidence)` |
| `market_svp_match` | `bool` | market SVP sub-object JSON equality |
| `updated_probabilities_match` | `bool` | updated probabilities sub-object JSON equality |

All scalar diffs are absolute differences (non-negative floats).  No tolerance
thresholds are applied at this milestone — exact determinism is expected.

---

## Read-only guarantee

- Replay runners call `get_projection_run_bundle` / `get_state_run_bundle` only.
- They do not call `save_run`, `load_run`, or any repository write path.
- They do not flush or commit the session.
- They do not create, update, or delete any ORM records.
- The loaded bundles are frozen dataclasses; replay cannot mutate them.

---

## Intentionally deferred

The following are explicitly **out of scope** for this milestone:

| Capability | Reason deferred |
|---|---|
| Batch replay (replay all runs) | Needs pagination, error aggregation, and result collection; separate milestone |
| Replay persistence (storing diff results) | Schema design and migration overhead; separate milestone |
| Historical baselines / golden snapshots | Requires a baseline management strategy; out of scope |
| API / UI reporting layer | No service layer in this repository |
| Configurable tolerance policies | Exact determinism is sufficient; tolerance adds complexity |
| CLI entrypoint | Out of scope per architecture principles |
| Async execution | Repository is synchronous throughout |
