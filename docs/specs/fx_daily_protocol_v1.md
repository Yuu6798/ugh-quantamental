# FX Daily Protocol v1 — Phase 2 Protocol Freeze

**Milestone:** 13
**Status:** Frozen
**Date:** 2026-03-12

---

## 1. Purpose

This document freezes the operational protocol for the daily FX prediction, outcome recording,
and evaluation cycle. It defines the typed record contracts, business-day rules, canonical time
references, forecast window, ID policy, versioning policy, and fail-fast requirements that all
downstream Phase 2 components must follow.

Phase 2 is not about adding new theory or changing core engine math. Milestone 13 is purely a
protocol freeze: schema-first, deterministic, and connector-free.

---

## 2. Scope

**In scope:**

- Typed Pydantic v2 record contracts: `ForecastRecord`, `OutcomeRecord`, `EvaluationRecord`
- Supporting models: `MarketDataProvenance`, `ExpectedRange`, `DisconfirmerRule`
- Enumerations: `CurrencyPair`, `StrategyKind`, `ForecastDirection`, `EventTag`
- Deterministic protocol calendar helpers
- Deterministic ID generation helpers
- Formal definitions of the forecast/outcome/evaluation layers

**Out of scope (deferred to later milestones):**

- Daily forecasting workflow execution
- Outcome ingestion automation and connectors
- Weekly / monthly performance reporting
- Persistence schema changes for protocol records
- CLI, notebooks, async execution, scheduling
- API or gRPC layer
- Batch orchestration framework
- Intra-day or high-frequency signal handling
- ML fitting, calibration, or learned weight matrices

---

## 3. Business-Day Rules

### 3.1 Phase 2 v1 definition

A **protocol business day** is any calendar day that falls on **Monday through Friday** (ISO
weekday 1–5) in Japan Standard Time (JST, `Asia/Tokyo`, UTC+9).

### 3.2 Holiday exclusion policy

**Holidays are NOT excluded in v1.** The calendar is weekday-only. Japanese public holidays,
US holidays, and other market-closure days are tracked via `EventTag` metadata but do not alter
the business-day calendar in this version.

### 3.3 Saturday and Sunday

Saturday (ISO weekday 6) and Sunday (ISO weekday 7) are always non-business days.

---

## 4. As-Of Time

The **canonical as-of time** for every forecast is **08:00 JST** on the forecast business day.

- `as_of_jst` is always `YYYY-MM-DD 08:00:00+09:00`
- Forecasts that are logically associated with the same date share the same `as_of_jst`
- A forecast batch for a given date must be locked (`locked_at_utc`) before market open

---

## 5. Horizon and Canonical Forecast Window

The **canonical forecast window** for a single forecast cycle is:

```
[as_of_t, as_of_t+1 business day)
```

That is:
- `window_start_jst = as_of_jst` (08:00 JST on day T)
- `window_end_jst = as_of_jst on the next protocol business day` (08:00 JST on day T+1)

The window is a half-open interval: the start is inclusive, the end is exclusive.

The outcome observation covers the **realized OHLC** of the pair over this window. In Phase 2 v1,
"close" refers to the price at `window_end_jst`.

---

## 6. Forecast Layer (`ForecastRecord`)

### 6.1 Definition

A `ForecastRecord` is an **immutable, locked prediction** produced at `as_of_jst`. Once created
and locked, it must not be modified. It captures:

- The predicted direction (`forecast_direction`) over the canonical window
- The expected price range (`expected_range`) and expected close change in basis points
- All UGH engine inputs and outputs (for `strategy_kind="ugh"`)
- Baseline strategy outputs (for non-UGH `strategy_kind`)
- Provenance metadata (`market_data_provenance`, version fields)

### 6.2 Strategy kinds

| `strategy_kind`                   | UGH engine fields | Notes                        |
|-----------------------------------|-------------------|------------------------------|
| `ugh`                             | Required          | Full UGH engine output       |
| `baseline_random_walk`            | None              | Random-walk forecast         |
| `baseline_prev_day_direction`     | None              | Previous-day repeat          |
| `baseline_simple_technical`       | None              | Simple moving-average signal |

For `strategy_kind="ugh"`, all UGH engine fields are required and must be non-null.
For baseline strategies, UGH fields may be `None`. Baselines still require `forecast_direction`
and `expected_close_change_bp`. Disconfirmers may be empty for baselines.

### 6.3 UGH engine fields carried in ForecastRecord

The following fields are produced by the UGH projection and state engines:

| Field                | Source                   |
|----------------------|--------------------------|
| `dominant_state`     | State engine             |
| `state_probabilities`| State engine             |
| `q_dir`              | Question direction input |
| `q_strength`         | Question features        |
| `s_q`                | Question features        |
| `temporal_score`     | Question features        |
| `grv_raw`            | Gravity bias (raw)       |
| `grv_lock`           | Signal features          |
| `alignment`          | Projection engine        |
| `e_star`             | Projection engine        |
| `mismatch_px`        | Projection engine        |
| `mismatch_sem`       | Projection engine        |
| `conviction`         | Projection engine        |
| `urgency`            | Projection engine        |
| `input_snapshot_ref` | SSV snapshot reference   |
| `primary_question`   | Question text            |
| `expected_range`     | Derived from projection  |

### 6.4 Baselines at forecast time

Baselines are **saved at forecast time**, not recomputed later. The baseline forecast for a given
window is fixed at lock time. This ensures evaluation is always comparing against the originally
produced forecast, regardless of later data revisions.

---

## 7. Outcome Layer (`OutcomeRecord`)

### 7.1 Definition

An `OutcomeRecord` is a **canonical market-fact record**. It records what actually happened in
the market during the forecast window:

- Realized OHLC prices (`realized_open`, `realized_high`, `realized_low`, `realized_close`)
- Realized direction (`realized_direction`) computed from the price change
- Realized close change in basis points (`realized_close_change_bp`)
- Realized price range (`realized_range_price` = `realized_high - realized_low`)
- Whether a scheduled event occurred (`event_happened`) and which tags apply (`event_tags`)
- Market data provenance (`market_data_provenance`)

### 7.2 State-proxy exclusion policy

**`OutcomeRecord` does NOT contain state-proxy fields.**

Specifically, `realized_state_proxy` and `actual_state_change` are intentionally absent from
`OutcomeRecord`. These are **evaluation-layer metadata**, not market-fact observations.

**Rationale:** Outcome records are canonical facts about what the market did. State-proxy
assessments require interpretation against the UGH framework and are computed in the evaluation
layer, not observed in the market. Mixing interpretation into the fact record would:

1. Violate the separation of observation from interpretation
2. Make `OutcomeRecord` framework-dependent (it must remain framework-agnostic)
3. Complicate downstream use by non-UGH consumers

### 7.3 Outcome immutability

Outcome records should be treated as append-only. Once an outcome is recorded for a given
`(pair, window_start_jst, window_end_jst)`, it must not be overwritten.

---

## 8. Evaluation Layer (`EvaluationRecord`)

### 8.1 Definition

An `EvaluationRecord` joins a `ForecastRecord` with its corresponding `OutcomeRecord` and
computes atomic diagnostic metrics. It answers: did the forecast match the outcome?

### 8.2 Metrics carried in EvaluationRecord

| Field                  | Type           | Description                                   |
|------------------------|----------------|-----------------------------------------------|
| `direction_hit`        | `bool`         | Forecast direction matches realized direction |
| `range_hit`            | `bool \| None` | Realized close falls within `expected_range`  |
| `close_error_bp`       | `float \| None`| Absolute error of close prediction in bps    |
| `magnitude_error_bp`   | `float \| None`| Error of magnitude prediction in bps         |
| `state_proxy_hit`      | `bool \| None` | State-proxy match (UGH only)                 |
| `mismatch_change_bp`   | `float \| None`| Change in mismatch metric (UGH only)         |
| `realized_state_proxy` | `str \| None`  | Evaluated state proxy string (UGH only)      |
| `actual_state_change`  | `bool \| None` | Whether lifecycle state changed (UGH only)   |
| `disconfirmers_hit`    | `tuple[str]`   | IDs of disconfirmer rules that fired         |
| `disconfirmer_explained`| `bool \| None`| Miss explained by a fired disconfirmer       |

### 8.3 Scope constraint: no aggregated metrics

`EvaluationRecord` stores **atomic diagnostics only**. The following aggregate metrics are
**intentionally deferred** to the reporting layer and must NOT appear in `EvaluationRecord`:

- MAE (mean absolute error)
- RMSE (root mean squared error)
- MASE (mean absolute scaled error)
- sMAPE (symmetric mean absolute percentage error)
- Rolling accuracy windows

### 8.4 Direction accuracy metric

`direction_hit` is an **evaluable-subset metric**: it is computable for all strategy kinds,
but meaningful only where a directional forecast is provided. Direction accuracy over a window
of N evaluations is computed by the reporting layer, not stored here.

### 8.5 Range hit metric

`range_hit` is the **strict canonical envelope-hit metric**: it is `True` iff the realized
close price falls within the half-open interval `[expected_range.low_price, expected_range.high_price]`.
It is `None` when `expected_range` was not provided (baseline strategies).

---

## 9. Event Tag Taxonomy

Event tags use a **fixed minimal taxonomy** in v1:

| Tag                | Description                             |
|--------------------|-----------------------------------------|
| `fomc`             | Federal Reserve FOMC meeting/decision   |
| `boj`              | Bank of Japan policy decision           |
| `cpi_us`           | US CPI release                          |
| `nfp_us`           | US non-farm payrolls release            |
| `jp_holiday`       | Japanese public holiday                 |
| `us_holiday`       | US public holiday                       |
| `month_end`        | Month-end rebalancing window            |
| `quarter_end`      | Quarter-end rebalancing window          |
| `other_macro`      | Other scheduled macro event             |
| `unscheduled_event`| Unscheduled geopolitical/risk event     |

Adding new tags requires a protocol version bump. Event tags are metadata only and do not
affect the business-day calendar in v1.

---

## 10. ID and Uniqueness Rules

All IDs are **deterministic and content-addressed**: given the same inputs, the same ID is
always produced. This enables idempotent replay and deduplication without a central registry.

### 10.1 ID formats

| ID                   | Format                                                                 |
|----------------------|------------------------------------------------------------------------|
| `forecast_batch_id`  | `fb_{pair}_{as_of_yyyymmddTHHMMSS}_{protocol_version}_{hash16}`       |
| `forecast_id`        | `fc_{pair}_{as_of_yyyymmddTHHMMSS}_{protocol_version}_{strategy}_{hash16}` |
| `outcome_id`         | `oc_{pair}_{start_yyyymmddTHHMMSS}_{end_yyyymmddTHHMMSS}_{schema_version}_{hash16}` |
| `evaluation_id`      | `ev_{forecast_id}_{schema_version}_{hash16}`                          |

Where `hash16` is the first 16 characters of the SHA-256 digest of the pipe-separated
(`|`) concatenation of the ID's input fields.

### 10.2 Uniqueness constraint

- One `ForecastRecord` per `(pair, as_of_jst, strategy_kind)`
- One `OutcomeRecord` per `(pair, window_start_jst, window_end_jst)`
- One `EvaluationRecord` per `(forecast_id, outcome_id)`
- One `ForecastBatch` per `(pair, as_of_jst, protocol_version)`

---

## 11. Version Rules

Every protocol record carries four version fields:

| Field              | Meaning                                           |
|--------------------|---------------------------------------------------|
| `theory_version`   | Version of the UGH theoretical framework used    |
| `engine_version`   | Version of the engine implementation             |
| `schema_version`   | Version of this protocol record schema           |
| `protocol_version` | Version of the operational protocol              |

Version strings are opaque to the protocol; their format is defined by the versioning policy.
Comparing records across version boundaries is supported only at the reporting layer.

---

## 12. Warm-Up Policy

**The protocol starts only after a warm-up history of at least 20 completed windows exists.**

This means:
- At minimum 20 `OutcomeRecord` entries must exist for the pair before evaluation begins
- Direction accuracy and other running metrics are not reported until 20+ evaluations are available
- This prevents early-window noise from dominating reported performance

---

## 13. Fail-Fast Policy

The protocol enforces fail-fast validation at three checkpoints:

### 13.1 Ingestion / normalization

- Market data must be finite (no `NaN`, `Inf`, `-Inf`)
- `realized_open`, `realized_high`, `realized_low`, `realized_close` must all be positive finite
- `realized_high >= realized_low` must hold; violation raises `ValueError`
- `price_type` must be `"mid"` (no other price types in v1)

### 13.2 Schema validation

- Pydantic v2 `extra="forbid"` rejects unknown fields at construction time
- `ExpectedRange` validator enforces `low_price <= high_price` at construction time
- `ForecastRecord` model validator enforces that all UGH fields are non-null for
  `strategy_kind="ugh"` at construction time
- Invalid enum values raise `ValidationError` immediately

### 13.3 Evaluation computation

- `evaluation_id` must not already exist in the evaluation store (deduplication check)
- `forecast_id` and `outcome_id` must resolve to existing records before evaluation proceeds
- `direction_hit` computation must not silently absorb `ValueError`; computation errors propagate

---

## 14. Out-of-Scope Section

The following are explicitly out of scope for this milestone and must not be implemented:

1. **Workflow execution**: `run_forecast_workflow`, `run_outcome_workflow`, `run_evaluation_workflow`
2. **Persistence schema**: No new ORM models or Alembic migrations
3. **Outcome ingestion automation**: No file readers, API clients, or data connectors
4. **Reporting**: No MAE, RMSE, MASE, or sMAPE computation; no rolling windows
5. **Weekly / monthly aggregation**: Deferred to reporting milestones
6. **Holiday calendar**: External holiday lists are out of scope for v1
7. **Multi-pair generalization**: The protocol supports `USDJPY` as the primary pair; extension
   to other pairs does not require protocol changes but is not validated in v1
8. **Async execution, scheduling, CLI, notebooks**: All deferred
9. **API or gRPC layer**: Not part of this library

---

## 15. References

- `src/ugh_quantamental/fx_protocol/models.py` — frozen Pydantic v2 record contracts
- `src/ugh_quantamental/fx_protocol/calendar.py` — deterministic calendar helpers
- `src/ugh_quantamental/fx_protocol/ids.py` — deterministic ID generation
- `docs/specs/ugh_projection_engine_v1.md` — projection engine math
- `docs/specs/ugh_state_engine_v1.md` — state engine math
- `docs/specs/ugh_baseline_v1.md` — baseline/golden snapshot policy
