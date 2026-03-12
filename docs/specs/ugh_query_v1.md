# UGH Query v1 — Read-only inspection layer for persisted runs

## Why this layer exists

Milestones 1–7 established deterministic engines, persistence scaffolding, and workflow
composition. The persistence layer can store projection and state runs durably, but provided
no structured way to retrieve or inspect them beyond single-record `load_run` lookups.

The query layer fills that gap: it exposes lightweight, synchronous, read-only helpers for
listing and reconstructing persisted runs. It does not write, mutate, or recompute anything.

---

## What can be queried

### Projection runs (`projection_runs` table)

Filter by:
- `projection_id` — exact match on the stable question/projection identifier
- `created_at_from` / `created_at_to` — closed-ended naive-UTC range on the run timestamp

### State runs (`state_runs` table)

Filter by:
- `snapshot_id` — exact match
- `omega_id` — exact match
- `projection_id` — exact match (nullable column; filter only applies to non-null rows)
- `dominant_state` — exact match on the string value (e.g. `"fire"`, `"dormant"`)
- `created_at_from` / `created_at_to` — closed-ended naive-UTC range

---

## Summary vs bundle reads

### Summary reads

`list_projection_run_summaries` and `list_state_run_summaries` return flat typed views
over the most useful metadata per run. Summaries are cheap — state run summaries are
built entirely from typed columns; projection run summaries additionally extract
`point_estimate` and `confidence` from `result_json`.

Summaries are suitable for listing, inspection, and lightweight reporting.

**`ProjectionRunSummary`** fields:
- `run_id`, `created_at`, `projection_id` — from typed columns
- `point_estimate`, `confidence` — from `result_json["projection_snapshot"]`

**`StateRunSummary`** fields:
- `run_id`, `created_at`, `snapshot_id`, `omega_id`, `projection_id` — from typed columns
- `dominant_state`, `transition_confidence` — from typed columns

### Bundle reads

`get_projection_run_bundle` and `get_state_run_bundle` look up a single run by `run_id`
and reconstruct all typed Pydantic models via the existing serializer helpers. They return
`None` if the run does not exist.

Bundles are suitable for audit, replay, and deep inspection of individual runs.

**`ProjectionRunBundle`** contains: `run_id`, `created_at`, `projection_id`,
`question_features`, `signal_features`, `alignment_inputs`, `config`, `result`.

**`StateRunBundle`** contains: `run_id`, `created_at`, `snapshot_id`, `omega_id`,
`projection_id`, `dominant_state`, `transition_confidence`, `snapshot`, `omega`,
`projection_result`, `event_features`, `config`, `result`.

---

## Filtering and ordering rules

- All filters are optional. An unset filter field does not restrict the result set.
- String filters use exact equality. No partial matching or wildcards.
- `created_at_from` is inclusive (`>=`). `created_at_to` is inclusive (`<=`).
- Callers must supply naive UTC datetimes for `created_at` comparisons to match the
  repository's naive-UTC storage policy. Aware datetimes are not normalised by the
  query layer.
- Results are always ordered **newest-first** by `created_at DESC`.
- `offset` and `limit` are applied after filtering and ordering.
- Default `limit` is 100; maximum is 1000.

---

## Query model validation

- `limit` must be in `[1, 1000]`.
- `offset` must be `>= 0`.
- `CreatedAtRange` is a standalone model for `created_at_from` / `created_at_to` pairs
  when used outside the query models.

---

## Why deeper analytics is deferred

The current requirement is structured inspection of individual runs. Aggregation,
cross-run analytics, derived metrics, and reporting pipelines require stable query
patterns and use-case requirements that do not yet exist. Introducing them now would
add complexity before runtime requirements are known.

---

## Intentionally out of scope

- Write operations of any kind
- CLI, REPL, or notebook interface
- External connectors or data exports
- Async execution
- Result caching or materialisation
- Analytics views or derived marts
- Batch aggregation or cross-run statistics
- Fuzzy or convenience date parsing
- Full-text or partial string search
- Pagination cursors (offset/limit only)
