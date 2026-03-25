# FX Monthly Review v1 — Specification

## Purpose

The monthly review layer aggregates one month of daily FX protocol results to provide:

- **Monthly strategy performance** across UGH and all baselines
- **Baseline comparison deltas** (UGH vs each baseline)
- **Annotation-aware analysis** by regime, volatility, intervention risk, and event tags
- **Provider health summary** over the monthly window
- **Rule-based review flags** identifying areas that may need attention
- **Recommendation summary** for logic review decisions

**This is a review and feedback layer only.** No forecast, outcome, or evaluation logic is changed. No new predictions are generated. The monthly review reads persisted CSV artifacts and produces aggregated analysis.

## Internal Logic Unchanged

The following are explicitly not modified:

- UGH formula / projection calculations
- State determination logic
- Baseline computation (random walk, previous day direction, simple technical)
- Forecast / outcome / evaluation judgment logic
- Request builder semantics
- Workflow engine internal processing
- Existing CSV / manifest / weekly report column definitions
- Database schema
- Batch ID / outcome ID generation rules

## Request Definition

```python
# Parameters for run_monthly_review()
pair: str = "USDJPY"                    # Currency pair
review_generated_at_jst: datetime       # Review generation timestamp (JST)
business_day_count: int = 20            # Business days in the monthly window
max_examples: int = 3                   # Max representative success/failure examples
include_annotations: bool = True        # Include annotation-aware metrics
```

## Result Definition

```python
{
    "review_version": "v1",
    "pair": str,
    "review_generated_at_jst": str,     # ISO format
    "requested_window_count": int,
    "included_window_count": int,
    "missing_window_count": int,
    "monthly_strategy_metrics": [...],
    "monthly_baseline_comparisons": [...],
    "monthly_state_metrics": [...],
    "monthly_regime_metrics": [...],
    "monthly_volatility_metrics": [...],
    "monthly_intervention_metrics": [...],
    "monthly_event_tag_metrics": [...],
    "provider_health_summary": {...},
    "annotation_coverage_summary": {...},
    "recommendation_summary": str,
    "review_flags": [...],
    "representative_successes": [...],
    "representative_failures": [...],
    "generated_artifact_paths": [...],
}
```

## Strategy Metrics

Per-strategy aggregation for each of the four strategies:

| Field | Description |
|---|---|
| `strategy_kind` | `ugh`, `baseline_random_walk`, `baseline_prev_day_direction`, `baseline_simple_technical` |
| `forecast_count` | Number of forecasts in the monthly window |
| `direction_hit_count` | Number of correct direction predictions |
| `direction_hit_rate` | `direction_hit_count / forecast_count` |
| `range_hit_count` | Number of range hits (UGH only) |
| `range_hit_rate` | `range_hit_count / range_evaluable_count` |
| `state_proxy_hit_count` | Number of state proxy hits (UGH only) |
| `state_proxy_hit_rate` | `state_proxy_hit_count / state_evaluable_count` |
| `mean_abs_close_error_bp` | Mean of `|close_error_bp|` |
| `median_abs_close_error_bp` | Median of `|close_error_bp|` |
| `mean_abs_magnitude_error_bp` | Mean of `|magnitude_error_bp|` |
| `median_abs_magnitude_error_bp` | Median of `|magnitude_error_bp|` |

## Baseline Comparisons

For each baseline strategy, compute deltas vs UGH:

| Field | Description |
|---|---|
| `baseline_strategy_kind` | The baseline being compared |
| `direction_accuracy_delta_vs_ugh` | `baseline_rate - ugh_rate` (negative = UGH better) |
| `mean_abs_close_error_bp_delta_vs_ugh` | `baseline_error - ugh_error` (positive = UGH better) |
| `mean_abs_magnitude_error_bp_delta_vs_ugh` | Same for magnitude error |
| `state_proxy_hit_rate_delta_vs_ugh` | Computed if both strategies have state proxy data |

## Annotation-Aware Analysis

Confirmed manual annotations are prioritized. Metrics are computed for UGH only, sliced by:

- **regime_label**: e.g., trending, choppy, ranging
- **volatility_label**: e.g., low, normal, high
- **intervention_risk**: e.g., low, medium, high
- **event_tag**: e.g., fomc, cpi_us, boj (expanded from pipe-delimited)

Each slice includes: `observation_count`, `direction_hit_rate`, `mean_abs_close_error_bp`.

### Annotation Coverage Summary

| Field | Description |
|---|---|
| `total_observations` | All observations in the window |
| `confirmed_count` | Observations with confirmed annotations |
| `pending_count` | Observations with pending annotations |
| `unlabeled_count` | Observations with no annotation |
| `annotation_coverage_rate` | `confirmed_count / total_observations` |

## Provider Health Summary

| Field | Description |
|---|---|
| `total_runs` | Total provider health records in the window |
| `providers` | Dict of provider name to usage count |
| `provider_usage_count` | Number of distinct providers used |
| `fallback_adjustment_count` | Number of runs using fallback adjustments |
| `lagged_snapshot_count` | Number of runs with lagged snapshots |
| `success_count` | Runs with status success/ok |
| `failed_count` | Runs with status failed/error |
| `skipped_count` | Runs with status skipped/idempotent_skip |
| `provider_mix_summary` | List of `{provider, count, share}` dicts |

## Review Flags

Rule-based flags are computed from monthly metrics. Each flag includes a `flag` identifier and a `reason` string explaining why it was raised.

### Flag Conditions

| Flag | Condition | Threshold Constant |
|---|---|---|
| `insufficient_data` | UGH forecast_count < minimum | `THRESHOLD_MINIMUM_OBSERVATIONS = 5` |
| `inspect_magnitude_mapping` | UGH mean close error worse than random walk by threshold | `THRESHOLD_CLOSE_ERROR_VS_RANDOM_WALK_BP = 5.0` bp |
| `inspect_direction_logic` | UGH direction accuracy below simple technical by threshold | `THRESHOLD_DIRECTION_DEFICIT_VS_TECHNICAL_PCT = 0.10` (10%) |
| `inspect_state_mapping` | State proxy hit rate high but magnitude error also high | `THRESHOLD_STATE_HIT_HIGH = 0.70`, `THRESHOLD_MAGNITUDE_ERROR_DESPITE_STATE_HIT_BP = 30.0` bp |
| `low_annotation_coverage` | Confirmed annotation coverage below threshold | `THRESHOLD_ANNOTATION_COVERAGE_LOW = 0.30` (30%) |
| `provider_quality_issue` | Provider lag or fallback rate exceeds threshold | `THRESHOLD_PROVIDER_LAG_RATE = 0.30`, `THRESHOLD_PROVIDER_FALLBACK_RATE = 0.30` |
| `missing_windows` | Missing window rate exceeds threshold | `THRESHOLD_MISSING_WINDOW_RATE = 0.25` (25%) |
| `keep_current_logic` | No other flags triggered | (no threshold) |

All thresholds are defined as module-level constants in `monthly_review.py` and can be modified for future tuning.

### Flag Behavior

- If `insufficient_data` is triggered, no other flags are computed (early return).
- If no flags are triggered, `keep_current_logic` is added automatically.
- Multiple `provider_quality_issue` flags may appear (one for lag, one for fallback).

## Recommendation Summary

A text summary derived from the review flags. Provides actionable guidance:

- **keep_current_logic**: "All monthly metrics are within acceptable thresholds."
- **insufficient_data**: "Insufficient observation data for reliable monthly assessment."
- **inspect_magnitude_mapping**: "Review magnitude/close-error mapping in UGH engine."
- **inspect_direction_logic**: "Review direction prediction logic — baseline outperforming."
- **inspect_state_mapping**: "Review state-to-magnitude mapping."
- **low_annotation_coverage**: "Increase annotation coverage."
- **provider_quality_issue**: "Investigate provider data quality."
- **missing_windows**: "Investigate missing protocol windows."

## Monthly Artifacts

### File Layout

```
{csv_output_dir}/analytics/monthly/{YYYYMM}/
├── monthly_review.json
├── monthly_review.md
├── monthly_strategy_metrics.csv
├── monthly_slice_metrics.csv
└── monthly_review_flags.csv

{csv_output_dir}/analytics/monthly/latest/
├── monthly_review.json
├── monthly_review.md
├── monthly_strategy_metrics.csv
├── monthly_slice_metrics.csv
└── monthly_review_flags.csv
```

The `latest/` directory is always mirrored from the most recent dated directory.

### monthly_review.md Sections

1. Monthly Summary (recommendation)
2. Review Flags
3. Strategy Performance (table)
4. Baseline Comparisons (delta table)
5. State Metrics (UGH by dominant_state)
6. Regime Analysis (confirmed annotations)
7. Volatility Analysis (confirmed annotations)
8. Intervention Risk Analysis (confirmed annotations)
9. Event Tag Analysis (confirmed annotations)
10. Provider Health Summary
11. Annotation Coverage
12. Representative Successes
13. Representative Failures
14. Recommendation Summary

## CLI

```bash
# scripts/run_fx_monthly_review.py
FX_CSV_OUTPUT_DIR=./data/csv \
FX_REVIEW_DATE=20260401 \
FX_MONTH_DAYS=20 \
FX_PAIR=USDJPY \
python scripts/run_fx_monthly_review.py
```

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `FX_CSV_OUTPUT_DIR` | `./data/csv` | Root CSV output directory |
| `FX_REVIEW_DATE` | today JST | Review date (YYYYMMDD) |
| `FX_MONTH_DAYS` | `20` | Business days to include |
| `FX_PAIR` | `USDJPY` | Currency pair |
| `FX_MAX_EXAMPLES` | `3` | Max representative examples |
| `FX_INCLUDE_ANNOTATIONS` | `true` | Include annotation-aware metrics |

## GitHub Actions Workflow

```yaml
# .github/workflows/fx-monthly-review.yml
# Runs on 1st of each month at 10:00 JST (01:00 UTC)
# Also supports manual dispatch (workflow_dispatch)
# Independent of daily and weekly workflows
```

## Re-generation

The monthly review can be regenerated at any time from persisted CSV artifacts:

```bash
FX_CSV_OUTPUT_DIR=./data/csv FX_REVIEW_DATE=20260401 python scripts/run_fx_monthly_review.py
```

No forecast engine is re-executed. All data comes from:
- `analytics/labeled_observations.csv` (rebuilt from history)
- `latest/provider_health.csv` or `history/*/provider_health.csv`

## Module Layout

| File | Purpose |
|---|---|
| `fx_protocol/monthly_review.py` | Pure functions: metrics, comparisons, flags, review |
| `fx_protocol/monthly_review_exports.py` | File I/O: JSON, MD, CSV export + orchestrator |
| `scripts/run_fx_monthly_review.py` | CLI entrypoint |
| `.github/workflows/fx-monthly-review.yml` | Monthly GitHub Actions workflow |
| `tests/fx_protocol/test_monthly_review.py` | Tests for pure functions |
| `tests/fx_protocol/test_monthly_review_exports.py` | Tests for export helpers |
