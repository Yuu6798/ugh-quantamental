# ugh_baseline_v1 — Baseline / Golden Snapshot Management

**Milestone 12** — synchronous, read-mostly, SQLite-friendly.

---

## Why this milestone exists

The regression suite (Milestone 11) can detect regressions between the _current_ engine and persisted
run records. However, it has no memory: every suite run compares against the live engine output, so
there is no way to ask "has the suite result _changed since we last checked_?"

Baseline management fills this gap by persisting a named suite result (a "golden snapshot") and
supporting future comparisons against that pinned record.

Use cases:
- Pin a known-good suite run before a refactor; confirm the suite is still green after the refactor.
- Detect when a previously passing case starts failing (or vice versa) without relying on CI alone.
- Provide a lightweight audit trail of suite outcomes at specific points in development.

---

## What a baseline stores

A `RegressionSuiteBaselineRecord` stores:

| Field | Type | Notes |
|---|---|---|
| `baseline_id` | `str` (PK, 64 chars) | Short `base_` + 12-hex identifier |
| `baseline_name` | `str` (unique, indexed) | Human-readable name; unique across all baselines |
| `created_at` | `datetime` (naive UTC) | Same policy as other persistence records |
| `description` | `str \| None` | Optional free-text annotation |
| `suite_request_json` | `dict` | Serialized `RegressionSuiteRequest` |
| `suite_result_json` | `dict` | Serialized suite result: aggregate + per-case summary |

The stored `suite_result_json` captures:
```json
{
  "aggregate": { /* RegressionSuiteAggregate fields */ },
  "projection_cases": [
    { "name": "...", "passed": true, "batch_aggregate": { /* ProjectionBatchReplayAggregate */ } }
  ],
  "state_cases": [
    { "name": "...", "passed": true, "batch_aggregate": { /* StateBatchReplayAggregate */ } }
  ]
}
```

Individual per-run replay results are _not_ stored in the baseline. The aggregate and per-case
pass/fail flags are sufficient to detect all meaningful regressions.

---

## Create flow

```
create_regression_baseline(session, request)
  → run_regression_suite(session, request.suite_request)
  → persist RegressionSuiteBaselineRecord (flush only; caller commits)
  → reload persisted record
  → reconstruct typed RegressionSuiteBaseline
  → return RegressionSuiteBaselineBundle
```

- `baseline_id` defaults to `make_baseline_id()` if not provided.
- `created_at` defaults to `datetime.now(timezone.utc)` (normalized to naive UTC) if not provided.
- If `baseline_name` already exists in the DB, the session will raise an `IntegrityError`
  (unique constraint). The caller is responsible for handling this.
- Writes exactly one baseline record per call. Does not commit; caller owns the transaction.

---

## Get flow

```
get_regression_baseline(session, *, baseline_id=..., baseline_name=...)
  → load RegressionSuiteBaselineRecord by id or by name
  → reconstruct RegressionSuiteBaseline (typed request + raw result JSON)
  → return RegressionSuiteBaselineBundle | None
```

- Exactly one of `baseline_id` or `baseline_name` must be provided.
- Returns `None` if the record is not found.
- Read-only: no writes, flushes, or commits.

---

## Compare flow

```
compare_regression_baseline(session, request)
  → load stored baseline (by id or name)  → returns None if not found
  → rerun run_regression_suite(session, stored_suite_request)
  → serialize current result with same _dump_suite_result() function
  → compute RegressionBaselineComparison
  → return RegressionBaselineCompareResult
```

- Read-only: no writes, flushes, or commits.
- Returns `None` if the baseline is not found.
- The current rerun uses the exact same `RegressionSuiteRequest` stored in the baseline.

---

## Comparison policy

| Field | How computed |
|---|---|
| `exact_match` | `stored_suite_result_json == _dump_suite_result(current_result)` |
| `case_count_match` | `stored_total_case_count == current_total_case_count` |
| `passed_case_count_diff` | `current - stored` (positive = more passing now) |
| `failed_case_count_diff` | `current - stored` |
| `total_missing_count_diff` | `current - stored` |
| `total_error_count_diff` | `current - stored` |
| `total_mismatch_count_diff` | `current - stored` |
| `case_deltas` | Per-case by name: `exists_in_baseline`, `exists_in_current`, `passed_match` |

`exact_match` is the primary signal. It is `True` iff the stored and current result JSON are
byte-for-byte equal. All aggregate diffs are provided for diagnostics even when `exact_match` is
`True` (they will all be zero in that case).

No configurable tolerances are supported in this milestone.

---

## Read/write policy

| Function | Writes? |
|---|---|
| `create_regression_baseline` | Yes — one baseline record; flush only |
| `get_regression_baseline` | No |
| `compare_regression_baseline` | No |

---

## Per-case delta semantics

`RegressionSuiteCaseDelta` is computed per unique case name across both baseline and current result:

- `exists_in_baseline`: case name appeared in stored result
- `exists_in_current`: case name appeared in current rerun
- `passed_match`: `True/False` when both sides have the case in the same group
  (projection–projection or state–state); `None` when the case is missing on one side or when
  case type changed

---

## What is deferred

The following are intentionally out of scope for this milestone:

- **Version graph**: baselines are immutable and there is no prev/next linkage.
- **Active/inactive flags**: no promotion or archival workflow.
- **Persisted compare reports**: comparison results are computed in memory and not stored.
- **Approval workflow**: no sign-off or gating concept.
- **Generic metadata blob**: the description field is the only annotation.
- **Configurable tolerance**: all comparisons are exact in this milestone.
- **Baseline listing / pagination**: `load_baseline` and `load_baseline_by_name` only; no list API.
