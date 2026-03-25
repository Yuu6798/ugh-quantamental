# FX Observability Artifacts v1 — Specification

**Status**: Implemented
**Depends on**: M13–M17 (FX Daily Protocol core)
**Scope**: Additive observability/reproducibility layer — no changes to existing logic

---

## 1. Motivation

The FX Daily Protocol (M13–M17) produces forecasts, outcomes, evaluations, and CSV exports. However, it lacks structured artifacts for:

- Capturing the exact market data inputs used per run (reproducibility)
- Summarizing run metadata in a machine-readable format (observability)
- Providing a human-readable daily digest (readability)
- Tracking cumulative strategy performance (scoreboard)
- Monitoring data provider health over time (operational health)

This specification adds five **derived artifacts** that are reconstructed entirely from existing records. No prediction logic is introduced or modified.

---

## 2. Change Boundary

### NOT changed
- UGH formulas, state judgment, baseline calculation
- Forecast/outcome/evaluation judgment logic
- Request builder semantics
- Workflow engine internals
- Existing CSV/manifest field definitions
- DB schema
- Batch ID / outcome ID generation rules

### Added
- `observability.py` — pure functions for artifact generation
- Five new artifacts in `latest/` and `history/` layout
- New fields on `FxDailyAutomationResult`
- Step 7 in `run_fx_daily_protocol_once`

---

## 3. Artifact Definitions

### 3.1 input_snapshot.json

Captures the market data state used as input for a forecast run.

**Location**:
- `latest/input_snapshot.json`
- `history/{YYYYMMDD}/{forecast_batch_id}/input_snapshot.json`

**Fields**:

| Field | Type | Description |
|---|---|---|
| as_of_jst | string (ISO 8601) | Canonical protocol timestamp |
| pair | string | Currency pair (e.g. "USDJPY") |
| current_spot | float | Current spot price from provider |
| provider_name | string | Market data vendor name |
| market_data_provenance | object | Full provenance record |
| completed_windows | array | All OHLC windows used |
| completed_window_count | int | Number of completed windows |
| newest_completed_window_end_jst | string (ISO 8601) | End time of newest window |
| generated_at_utc | string (ISO 8601) | Artifact generation timestamp |

### 3.2 run_summary.json

Machine-readable summary of one automation run.

**Location**:
- `latest/run_summary.json`
- `history/{YYYYMMDD}/{forecast_batch_id}/run_summary.json`

**Fields**:

| Field | Type | Description |
|---|---|---|
| as_of_jst | string (ISO 8601) | Canonical protocol timestamp |
| provider_name | string | Market data vendor name |
| versions | object | theory/engine/schema/protocol versions |
| forecast_batch_id | string or null | Batch ID if forecast generated |
| outcome_id | string or null | Outcome ID if recorded |
| forecast_created | bool | Whether a new forecast was created |
| outcome_recorded | bool | Whether an outcome was recorded |
| evaluation_count | int | Number of evaluations generated |
| csv_paths | object | Paths to generated CSV files |
| manifest_path | string or null | Path to manifest.json |
| snapshot_lag_business_days | int | Provider data lag in business days |
| used_fallback_adjustment | bool | Whether 1-day fallback was used |
| run_status | string | "ok" or "idempotent_skip" |
| generated_at_utc | string (ISO 8601) | Artifact generation timestamp |

### 3.3 daily_report.md

Human-readable daily digest reconstructed from existing records.

**Location**:
- `latest/daily_report.md`
- `history/{YYYYMMDD}/{forecast_batch_id}/daily_report.md`

**Sections**:

1. **Run Summary** — as_of_jst, batch ID, counts
2. **Today's Forecasts** — table of strategy/direction/change/state
3. **Previous Window Outcome** — realized OHLC, direction, events
4. **Evaluation Comparison** — table of hit rates and errors per strategy
5. **Observation Notes** — mechanical notes (UGH hits, baseline comparison)

No new prediction logic is introduced. All content derives from `ForecastRecord`, `OutcomeRecord`, `EvaluationRecord`, and manifest data.

### 3.4 scoreboard.csv

Cumulative strategy performance metrics aggregated from all historical evaluations.

**Location**:
- `latest/scoreboard.csv`
- `history/{YYYYMMDD}/{forecast_batch_id}/scoreboard.csv`

**Columns**:

| Column | Type | Description |
|---|---|---|
| strategy_kind | string | Strategy identifier |
| observation_count | int | Total evaluations for this strategy |
| direction_hit_count | int | Correct direction predictions |
| direction_hit_rate | float | Hit count / observation count |
| range_hit_count | int or blank | Range hits (UGH only) |
| range_hit_rate | float or blank | Range hit rate (UGH only) |
| state_proxy_hit_count | int or blank | State proxy hits (UGH only) |
| state_proxy_hit_rate | float or blank | State proxy hit rate (UGH only) |
| mean_close_error_bp | float | Mean close error in basis points |
| median_close_error_bp | float | Median close error in basis points |
| mean_magnitude_error_bp | float | Mean magnitude error in basis points |
| last_updated_utc | string (ISO 8601) | When scoreboard was generated |

Data source: all `evaluation.csv` files found in `history/` directories.

### 3.5 provider_health.csv

Append-only log of provider health per run.

**Location**:
- `provider_health.csv` (root of csv_output_dir, append-only)
- `latest/provider_health.csv` (latest copy)
- `history/{YYYYMMDD}/{forecast_batch_id}/provider_health.csv` (snapshot)

**Columns**:

| Column | Type | Description |
|---|---|---|
| as_of_jst | string (ISO 8601) | Canonical protocol timestamp |
| generated_at_utc | string (ISO 8601) | Row generation timestamp |
| provider_name | string | Market data vendor name |
| newest_completed_window_end_jst | string (ISO 8601) | Newest window end |
| snapshot_lag_business_days | int | Data lag in business days |
| used_fallback_adjustment | bool | Whether fallback was applied |
| run_status | string | "ok" or "idempotent_skip" |
| notes | string | Optional notes |

---

## 4. Layout

All artifacts follow the existing `latest/` + `history/` layout convention:

```
{csv_output_dir}/
├── latest/
│   ├── forecast.csv          (existing)
│   ├── outcome.csv           (existing)
│   ├── evaluation.csv        (existing)
│   ├── manifest.json         (existing)
│   ├── input_snapshot.json   (NEW)
│   ├── run_summary.json      (NEW)
│   ├── daily_report.md       (NEW)
│   ├── scoreboard.csv        (NEW)
│   └── provider_health.csv   (NEW)
├── history/{YYYYMMDD}/{forecast_batch_id}/
│   ├── forecast.csv          (existing)
│   ├── outcome.csv           (existing)
│   ├── evaluation.csv        (existing)
│   ├── input_snapshot.json   (NEW)
│   ├── run_summary.json      (NEW)
│   ├── daily_report.md       (NEW)
│   ├── scoreboard.csv        (NEW)
│   └── provider_health.csv   (NEW)
├── observability/            (NEW — staging area for artifacts)
│   ├── {YYYYMMDD}_input_snapshot.json
│   ├── {YYYYMMDD}_run_summary.json
│   ├── {YYYYMMDD}_daily_report.md
│   └── {YYYYMMDD}_scoreboard.csv
└── provider_health.csv       (NEW — append-only master log)
```

---

## 5. Stale File Policy

When an artifact is not generated (e.g., scoreboard when no evaluations exist), the corresponding `latest/` file is **deleted** to prevent serving stale data. This matches the existing policy for `latest/outcome.csv` and `latest/evaluation.csv`.

---

## 6. Integration Point

Observability artifacts are generated in **Step 7** of `run_fx_daily_protocol_once`, after Step 6 (manifest). They are only generated when `config.write_csv_exports` is `True` and a `forecast_batch_id` exists.

The `FxDailyAutomationResult` model includes five new optional path fields:
- `input_snapshot_path`
- `run_summary_path`
- `daily_report_path`
- `scoreboard_path`
- `provider_health_path`

---

## 7. Invariants

1. Existing forecast/outcome/evaluation/manifest outputs are **byte-identical** with and without observability artifacts.
2. All artifact content derives from already-persisted records — no new computation.
3. Idempotent: re-running the same window overwrites artifacts deterministically.
4. No DB schema changes required.
5. `observability.py` is importable without SQLAlchemy.
