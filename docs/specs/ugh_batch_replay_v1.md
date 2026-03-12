# ugh_batch_replay_v1 — Batch Replay / Experiment Runner

## Why batch replay exists

The single-run replay layer (Milestone 9) verifies one persisted run at a time.  In
practice, regression checking after an engine refactor or config change requires replaying
many runs, not just one.  Manually looping over run IDs and accumulating results is
repetitive and error-prone.

Batch replay provides a single-call wrapper that:

- Accepts a list of run IDs or a query-driven selection
- Replays each run using the existing single-run replay helpers
- Isolates per-run errors so one failing run cannot abort the entire batch
- Returns per-run items with status flags and an aggregate summary

Because the underlying engines are deterministic and the single-run replay layer is already
read-only, batch replay adds only the orchestration loop and the aggregation step.

---

## Modes of operation

### Explicit run-ID mode

```
ProjectionBatchReplayRequest(run_ids=("run-a", "run-b", "run-c"))
```

Runs are replayed in the provided order.  If `deduplicate_run_ids=True` (default), the
first occurrence of each `run_id` is kept and later duplicates are silently dropped while
preserving the original insertion order.

### Query-driven mode

```
ProjectionBatchReplayRequest(query=ProjectionRunQuery(projection_id="proj-1", limit=50))
```

Run IDs are resolved by calling the existing summary reader (`list_projection_run_summaries`
or `list_state_run_summaries`) and collecting the `run_id` from each returned summary.  The
ordering is **newest-first by `created_at DESC`**, which matches the summary reader's
default ordering.  `deduplicate_run_ids` applies as usual (duplicates are unlikely in
query-driven mode but the policy is consistent).

Exactly one of `run_ids` or `query` must be provided.  Supplying both, or neither, is a
validation error at request construction time.

---

## Pagination strategy

Batch replay delegates pagination entirely to the query layer.  Callers control the result
window via the `limit` and `offset` fields on the `ProjectionRunQuery` / `StateRunQuery`
embedded in the request.  Default `limit` is 100; maximum is 1000.  For larger corpora,
callers should issue multiple batch requests with incrementing `offset` values.

Batch replay itself does not implement cursor-based pagination.  There is no internal
pagination loop — one batch request corresponds to one reader call.

---

## Per-run error isolation

For each resolved run ID the batch runner calls the single-run replay helper and handles
three outcomes:

| Outcome | Item status | Notes |
|---|---|---|
| `replay_*_run` returns a result | `ok` | Normal path |
| `replay_*_run` returns `None` | `missing` | Run ID not found in the database |
| `replay_*_run` raises any exception | `error` | Exception message captured in `error_message`; batch continues |

A single failing run never aborts the entire batch.  The `error_message` field captures
`str(exc)` for diagnostic purposes.

---

## Aggregate mismatch reporting

After all per-run items are collected, the batch runner builds an aggregate summary:

### `ProjectionBatchReplayAggregate`

| Field | Meaning |
|---|---|
| `requested_count` | Total deduplicated run IDs attempted |
| `processed_count` | `ok` + `error` (runs where a bundle was found) |
| `exact_match_count` | `ok` items with `comparison.exact_match == True` |
| `mismatch_count` | `ok` items with `comparison.exact_match == False` |
| `missing_count` | `missing` items |
| `error_count` | `error` items |
| `max_point_estimate_diff` | Max absolute `point_estimate_diff` across all `ok` items |
| `max_confidence_diff` | Max absolute `confidence_diff` across all `ok` items |

### `StateBatchReplayAggregate`

| Field | Meaning |
|---|---|
| `requested_count` | Total deduplicated run IDs attempted |
| `processed_count` | `ok` + `error` |
| `exact_match_count` | `ok` items with `comparison.exact_match == True` |
| `mismatch_count` | `ok` items with `comparison.exact_match == False` |
| `missing_count` | `missing` items |
| `error_count` | `error` items |
| `max_transition_confidence_diff` | Max absolute `transition_confidence_diff` across all `ok` items |

Aggregate max-diff metrics use `0.0` as the default when no `ok` items exist.

---

## Read-only guarantee

Batch replay inherits the read-only guarantee of the single-run replay layer.

- Calls only `replay_projection_run` / `replay_state_run` and the summary readers
- Does not call `save_run`, `load_run`, or any repository write path
- Does not flush or commit the session
- Does not create, update, or delete any ORM records
- The caller owns the session and transaction boundary

---

## Intentionally deferred

| Capability | Reason deferred |
|---|---|
| Persisted replay reports (store batch results to DB) | Schema design and migration overhead; separate milestone |
| Async execution | Repository is synchronous throughout |
| Scheduling / periodic batch jobs | No orchestration framework in this repo |
| General experiment matrices (cross-product of configs) | Beyond the scope of regression checking |
| API / UI reporting layer | No service layer in this repository |
| Cursor-based pagination | Offset/limit is sufficient at this milestone |
| Configurable tolerance policies | Exact determinism expected; tolerance adds complexity |
| CLI entrypoint | Out of scope per architecture principles |
