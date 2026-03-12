# ugh_regression_suite_v1 — Regression Suite / Report Layer

## Why a suite layer exists on top of batch replay

Batch replay (Milestone 10) replays a single group of runs and returns a flat list of
per-run outcomes.  Real regression workflows require more structure: a single call that
exercises multiple named test cases (e.g. "projection smoke", "state fire-regime",
"all dormant runs"), collects their results, and produces a deterministic pass/fail report.

The regression suite layer provides that structure.  It:

- Accepts named projection and state cases, each mapping to a batch replay request
- Runs all cases in order via the existing batch replay functions
- Computes a deterministic pass/fail flag per case
- Rolls up a suite-level aggregate across all cases
- Returns a single structured result suitable for inspection or assertion in tests

Because the batch replay layer is already read-only and deterministic, the suite layer adds
only grouping, naming, and aggregation.

---

## Projection vs state cases

A `RegressionSuiteRequest` contains two independent lists:

- `projection_cases: tuple[ProjectionSuiteCase, ...]`
- `state_cases: tuple[StateSuiteCase, ...)`

Each case is a named batch replay request.  Projection and state cases run in declaration
order within their respective groups.  All projection cases run before all state cases.

At least one case overall must be present.  Case names must be non-empty.  Within each
group, case names must be unique.  Cross-group name collisions are allowed.

---

## Run-ID mode vs query-driven mode within a case

Each suite case delegates source selection to the batch replay layer unchanged:

- **Explicit run-ID mode** — `run_ids: tuple[str, ...]` provided; replayed in order
- **Query-driven mode** — `query: ProjectionRunQuery | StateRunQuery` provided;
  run IDs resolved via the summary reader (newest-first)

Exactly one of `run_ids` or `query` must be supplied per case.

---

## Pass/fail policy

A case **passes** if and only if all three conditions hold after its batch result is built:

| Condition | Meaning |
|---|---|
| `aggregate.error_count == 0` | No per-run exceptions |
| `aggregate.missing_count == 0` | All requested run IDs found |
| `aggregate.mismatch_count == 0` | Engine outputs match stored results exactly |

A case **fails** if any condition is violated.  There are no configurable tolerance
thresholds at this milestone.  Exact determinism is required.

A suite with zero ok-items in a case (e.g. all missing or all error) will fail that case.

---

## Aggregate reporting policy

`RegressionSuiteAggregate` sums across all cases:

| Field | Meaning |
|---|---|
| `projection_case_count` | Number of projection cases |
| `state_case_count` | Number of state cases |
| `total_case_count` | Sum of both |
| `passed_case_count` | Cases with `passed == True` |
| `failed_case_count` | Cases with `passed == False` |
| `total_projection_requested` | Sum of `requested_count` across projection cases |
| `total_state_requested` | Sum of `requested_count` across state cases |
| `total_missing_count` | Sum of `missing_count` across all cases |
| `total_error_count` | Sum of `error_count` across all cases |
| `total_mismatch_count` | Sum of `mismatch_count` across all cases |

---

## Read-only guarantee

The suite runner calls only `replay_projection_batch` and `replay_state_batch`.  It does
not call `save_run`, `load_run`, or any repository write path.  It does not flush or commit
the session.  All results are computed from data already in the database at call time.

---

## Intentionally deferred

| Capability | Reason deferred |
|---|---|
| Persisted suite reports (store results to DB) | Schema design and migration overhead |
| Configurable tolerance policies | Exact determinism is sufficient; adds complexity |
| Experiment matrices / cross-product config sweeps | General experiment platform; out of scope |
| Async or scheduled execution | Repository is synchronous throughout |
| API / UI reporting layer | No service layer in this repository |
| Suite-level weighting or scoring | No clear requirement yet |
| CLI entrypoint | Out of scope per architecture principles |
| Baseline management / golden snapshot storage | Requires a separate design |
