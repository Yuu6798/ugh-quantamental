# FX Daily Forecast Workflow v1 (Phase 2 Milestone 14)

## Why this workflow exists

Milestone 13 froze the FX Daily Protocol contracts (forecast/outcome/evaluation records, calendar rules, and deterministic IDs). Milestone 14 adds the **daily workflow** that actually generates and persists one deterministic forecast batch per business day.

This milestone is intentionally narrow:
- generate one daily batch for one pair/as-of,
- include UGH + baseline strategies,
- persist records with deterministic IDs,
- enforce idempotent rerun behavior.

## Execution inputs

`DailyForecastWorkflowRequest` carries:
- `pair`, `as_of_jst`, `market_data_provenance`, `input_snapshot_ref`
- `ugh_request: FullWorkflowRequest` (projection + state workflow request)
- `baseline_context` (spot/rolling stats/SMAs/warmup)
- version fields (`theory_version`, `engine_version`, `schema_version`, `protocol_version`)
- optional `locked_at_utc`

Validation rules:
- `as_of_jst` must be a protocol business day (Mon–Fri in JST)
- `as_of_jst` must be exactly 08:00 JST
- `baseline_context.warmup_window_count >= 20`

## Batch composition

For each request, the workflow computes:
- `forecast_batch_id = make_forecast_batch_id(pair, as_of_jst, protocol_version)`
- `window_end_jst = next_as_of_jst(as_of_jst)`

Then generates exactly four forecasts:
1. `strategy_kind="ugh"`
2. `strategy_kind="baseline_random_walk"`
3. `strategy_kind="baseline_prev_day_direction"`
4. `strategy_kind="baseline_simple_technical"`

All four share:
- `forecast_batch_id`
- `pair`
- `as_of_jst`
- `window_end_jst`
- version metadata fields

## Baseline rules

### A) Random walk baseline
- `forecast_direction = flat`
- `expected_close_change_bp = 0`
- band half-width = `trailing_mean_range_price / 2`
- expected range centered at `current_spot`

### B) Previous-day-direction baseline
- requires `previous_close_change_bp` (fail fast if missing)
- direction = sign(`previous_close_change_bp`)
- `expected_close_change_bp = previous_close_change_bp`
- expected range uses same width/centering rule as random walk

### C) Simple technical baseline
- requires both `sma5` and `sma20` (fail fast if either missing)
- direction:
  - `up` if `sma5 > sma20`
  - `down` if `sma5 < sma20`
  - `flat` otherwise
- `expected_close_change_bp = sign(sma5 - sma20) * trailing_mean_abs_close_change_bp`
- expected range uses same width/centering rule as random walk

## UGH forecast mapping

The workflow executes the existing deterministic UGH full workflow via:
- `run_full_workflow(session, request.ugh_request)`

Then maps outputs to a `ForecastRecord` with `strategy_kind="ugh"` and protocol fields including:
- `primary_question`
- `dominant_state`, `state_probabilities`
- `q_dir`, `q_strength`, `s_q`, `temporal_score`
- `grv_raw`, `grv_lock`
- `alignment`, `e_star`, `mismatch_px`, `mismatch_sem`, `conviction`, `urgency`
- `forecast_direction`, `expected_close_change_bp`, `expected_range`

## Persistence design

Adds one minimal table:
- `fx_forecast_records`
  - `forecast_id` (PK)
  - `forecast_batch_id` (indexed)
  - `pair`
  - `strategy_kind`
  - `as_of_jst`
  - `window_end_jst`
  - `protocol_version`
  - `payload_json` (full `ForecastRecord` JSON)

Repository helpers:
- `save_fx_forecast_batch(...)`
- `load_fx_forecast_batch(...)`

## Idempotency policy

- Batch identity is deterministic (`pair + as_of_jst + protocol_version`)
- If full batch already exists (4 records), return it without inserting duplicates
- If partial batch exists (<4 records), fail fast with a clear error

## Intentionally deferred (not in Milestone 14)

- outcome ingestion / persistence
- evaluation generation / persistence
- weekly/monthly reporting
- scheduling / automation
- external connectors and API/CLI surfaces
