# FX Daily Outcome and Evaluation Workflow v1 (Phase 2 Milestone 15)

**Milestone:** 15
**Status:** Implemented
**Date:** 2026-03-14

---

## 1. Why this workflow exists

Milestone 13 froze the FX Daily Protocol contracts. Milestone 14 generates and persists one
deterministic forecast batch per business day (four forecasts: UGH + three baselines).

Milestone 15 closes the cycle: once a forecast window has elapsed and realized OHLC prices are
available, this workflow:

1. Records one canonical `OutcomeRecord` for the completed window.
2. Loads the matching forecast batch (produced by Milestone 14).
3. Generates one `EvaluationRecord` per forecast in that batch, capturing atomic diagnostic
   metrics.

This milestone does **not** add new theory, engine math, weekly/monthly reporting, scheduling,
CLI, external data connectors, or any API surface.

---

## 2. Canonical outcome construction

### 2.1 Inputs

`DailyOutcomeWorkflowRequest` carries:

- `pair` — the currency pair (e.g. `USDJPY`)
- `window_start_jst` — 08:00 JST on the forecast day (T)
- `window_end_jst` — 08:00 JST on the next business day (T+1)
- `market_data_provenance` — source metadata for the realized OHLC data
- `realized_open`, `realized_high`, `realized_low`, `realized_close` — observed prices
- `event_tags` — zero or more `EventTag` values that occurred during the window
- `schema_version`, `protocol_version` — version metadata
- `evaluated_at_utc` — optional; defaults to `datetime.now(UTC)` if absent

### 2.2 Validation rules (fail fast at request construction)

- Both `window_start_jst` and `window_end_jst` must be exactly 08:00 JST on a Mon–Fri.
- `window_end_jst` must equal `next_as_of_jst(window_start_jst)` — i.e. the immediately
  following protocol business day.
- All four OHLC prices must be finite and strictly positive.
- The model validator in `OutcomeRecord` enforces `high >= low`, open/close within range,
  direction/bp consistency, and event-tag consistency.

### 2.3 Derived market facts

| Field                    | Derivation                                              |
|--------------------------|---------------------------------------------------------|
| `outcome_id`             | `make_outcome_id(pair, window_start_jst, window_end_jst, schema_version)` |
| `realized_direction`     | `up` if close > open; `down` if close < open; `flat` if close == open |
| `realized_close_change_bp` | `(close - open) / open × 10_000`                    |
| `realized_range_price`   | `high - low`                                            |
| `event_happened`         | `len(event_tags) > 0`                                   |

These are passed directly into `OutcomeRecord`, whose model validator cross-checks them.

---

## 3. Forecast batch lookup

The matching forecast batch is identified deterministically:

```
forecast_batch_id = make_forecast_batch_id(pair, window_start_jst, protocol_version)
```

because `window_start_jst` equals the `as_of_jst` of the forecast batch for day T.

**Fail-fast rules:**

- If no batch exists for `forecast_batch_id`, raise `ValueError` with a clear message.
- If the batch exists but contains fewer or more than 4 forecasts, raise `ValueError`.

---

## 4. Realized state proxy lookup

The `realized_state_proxy` is an evaluation-layer field (absent from `OutcomeRecord`) that
represents the UGH lifecycle state at the close of the window.

**Lookup procedure:**

1. Compute the next-day batch ID:
   ```
   next_batch_id = make_forecast_batch_id(pair, window_end_jst, protocol_version)
   ```
2. Load that batch (if it exists).
3. If found, extract the UGH forecast's `dominant_state` as `realized_state_proxy`.
4. If the next-day batch does not exist or contains no UGH forecast:
   - `realized_state_proxy = None`
   - All state-proxy-dependent evaluation fields remain `None`.

This is always a **read-only** lookup — no batch is generated or inferred.

---

## 5. Per-forecast evaluation rules

One `EvaluationRecord` is generated per forecast. All four evaluations share the same canonical
`OutcomeRecord`.

### 5.1 `direction_hit` (all strategies)

```
direction_hit = (forecast.forecast_direction == outcome.realized_direction)
```

### 5.2 `range_hit`

- **UGH only:** `True` iff
  `expected_range.low_price <= outcome.realized_close <= expected_range.high_price`
- **Baselines:** must be `None` (no forecast price envelope)

### 5.3 `close_error_bp` and `magnitude_error_bp` (all strategies)

```
close_error_bp     = abs(forecast.expected_close_change_bp - outcome.realized_close_change_bp)
magnitude_error_bp = abs(abs(forecast.expected_close_change_bp) - abs(outcome.realized_close_change_bp))
```

### 5.4 State-proxy diagnostics (UGH only)

If `forecast.dominant_state` and `realized_state_proxy` are both non-`None`:

```
state_proxy_hit    = (forecast.dominant_state.value == realized_state_proxy)
actual_state_change = (forecast.dominant_state.value != realized_state_proxy)
```

Otherwise both are `None`.

### 5.5 `mismatch_change_bp` (UGH only)

```
mismatch_change_bp = outcome.realized_close_change_bp - forecast.expected_close_change_bp
```

### 5.6 `disconfirmer_explained`

```
disconfirmer_explained = (not direction_hit) and (len(disconfirmers_hit) > 0)
```

---

## 6. Disconfirmer audit rules

`compute_disconfirmers_hit` evaluates each `DisconfirmerRule` in `forecast.disconfirmers`
against the canonical outcome and the optional `realized_state_proxy`. It returns the tuple
of `rule_id` values for fired rules.

### A) `audit_kind="event_tag"`

- `threshold_value` is an event-tag string.
- Fired iff that tag appears in `outcome.event_tags`.

### B) `audit_kind="close_change_bp"`

- `threshold_value` is a numeric value.
- `operator` must be one of: `gt`, `gte`, `lt`, `lte`, `eq`, `ne`.
- Compares `outcome.realized_close_change_bp` against `threshold_value`.

### C) `audit_kind="state_proxy"`

- `threshold_value` is a string state name.
- `operator` must be `eq` or `ne`.
- Compares `realized_state_proxy` against `threshold_value`.
- If `realized_state_proxy is None`, the rule does not fire (returns `False`).

### D) `audit_kind="range_break"`

- Requires `forecast.expected_range` (non-`None`); fails fast if absent.
- `threshold_value` must be one of `"below_expected_low"`, `"above_expected_high"`,
  `"outside_expected_range"`.
- Uses `outcome.realized_close` as the comparison target.
- Interpretations:
  - `"below_expected_low"` — fired iff `realized_close < expected_range.low_price`
  - `"above_expected_high"` — fired iff `realized_close > expected_range.high_price`
  - `"outside_expected_range"` — fired iff either of the above

### Unsupported combinations

Any `audit_kind` / `operator` / `threshold_value` combination not listed above raises a
`ValueError` immediately. Rules must never be silently skipped.

---

## 7. Persistence design

### 7.1 `fx_outcome_records` table (ORM: `FxOutcomeRecord`)

| Column             | Type                    | Notes             |
|--------------------|-------------------------|-------------------|
| `outcome_id`       | `String(128)` — PK      | Deterministic ID  |
| `pair`             | `String(16)`            | Searchable        |
| `window_start_jst` | `DateTime(timezone=False)` | Naive UTC stored |
| `window_end_jst`   | `DateTime(timezone=False)` | Naive UTC stored |
| `protocol_version` | `String(32)`            | Searchable        |
| `payload_json`     | `JSON`                  | Full `OutcomeRecord` |

### 7.2 `fx_evaluation_records` table (ORM: `FxEvaluationRecord`)

| Column             | Type                    | Notes             |
|--------------------|-------------------------|-------------------|
| `evaluation_id`    | `String(512)` — PK      | Deterministic ID  |
| `forecast_id`      | `String(128)` — indexed |                   |
| `outcome_id`       | `String(128)` — indexed |                   |
| `pair`             | `String(16)`            |                   |
| `strategy_kind`    | `String(64)`            |                   |
| `window_start_jst` | `DateTime(timezone=False)` |                |
| `window_end_jst`   | `DateTime(timezone=False)` |                |
| `protocol_version` | `String(32)`            |                   |
| `payload_json`     | `JSON`                  | Full `EvaluationRecord` |

### 7.3 Repository helpers

`FxOutcomeEvaluationRepository`:

- `save_fx_outcome_record(session, *, outcome)` → `FxOutcomeRecord`
- `load_fx_outcome_record(session, outcome_id)` → `OutcomeRecord | None`
- `save_fx_evaluation_batch(session, *, outcome_id, evaluations)` → `tuple[FxEvaluationRecord, ...]`
- `load_fx_evaluation_batch(session, outcome_id)` → `tuple[EvaluationRecord, ...] | None`

Both save operations flush but do not commit. The caller owns the transaction.

---

## 8. Idempotency policy

### 8.1 Canonical outcome

The `outcome_id` is deterministic from `(pair, window_start_jst, window_end_jst, schema_version)`.
If a record with the same `outcome_id` already exists, the workflow returns the persisted outcome
without inserting a duplicate.

### 8.2 Evaluation batch

If all 4 evaluations for the current `outcome_id` already exist (loaded by `outcome_id` from
`fx_evaluation_records`), the workflow returns them without reinserting.

### 8.3 Partial evaluation batch (fail fast)

If the evaluation store contains 1–3 records for the given `outcome_id`, the workflow raises
`ValueError` with a clear message indicating a partial batch and the counts. This prevents
silent mixing of old and new records.

### 8.4 Note on re-runs

Because all IDs are deterministic, a full re-run of `run_daily_outcome_evaluation_workflow`
with the same inputs will always take the idempotent path and return the persisted records.

---

## 9. What is intentionally deferred

- **Weekly reporting** — rolling direction accuracy, MAE/RMSE/sMAPE per strategy
- **Monthly review and protocol version updates** — version bump policy and migration
- **Scheduling and automation** — cron, task queues, event-driven triggers
- **External data connectors** — market data feeds, vendor APIs
- **CLI and notebooks** — no command-line interface in this milestone
- **Multi-run aggregate diagnostics** — MASE, rolling accuracy windows
- **Outcome correction / amendment** — once an outcome is persisted it is immutable in v1
