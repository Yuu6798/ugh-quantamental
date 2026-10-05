# FX Weekly Report v2 — 20260928 to 20261002

Generated: 2026-10-05T06:27:14Z
Report date (JST): 2026-10-05T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | - | 39.9 | 25.1 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 13.9 | 6.0 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 30.5 | 29.6 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 100.0% | 25.0% | 50.0% | 14.7 | 14.2 |
| ugh_v2_beta | 4 | 3 | 75.0% | 100.0% | 25.0% | 50.0% | 11.6 | 7.1 |
| ugh_v2_delta | 4 | 3 | 75.0% | 100.0% | 25.0% | 50.0% | 13.1 | 10.1 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 100.0% | 25.0% | 50.0% | 14.5 | 13.3 |

### Event-Tag Analysis (sources: auto_only: 7, none: 21)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | month_end | 1 | 0.0% | - | 12.1 |
| baseline_prev_day_direction | quarter_end | 1 | 0.0% | - | 12.1 |
| baseline_random_walk | month_end | 1 | 0.0% | - | 4.5 |
| baseline_random_walk | quarter_end | 1 | 0.0% | - | 4.5 |
| baseline_simple_technical | month_end | 1 | 100.0% | - | 50.3 |
| baseline_simple_technical | quarter_end | 1 | 100.0% | - | 50.3 |
| ugh_v2_alpha | month_end | 1 | 100.0% | 100.0% | 12.4 |
| ugh_v2_alpha | quarter_end | 1 | 100.0% | 100.0% | 12.4 |
| ugh_v2_beta | month_end | 1 | 100.0% | 100.0% | 6.6 |
| ugh_v2_beta | quarter_end | 1 | 100.0% | 100.0% | 6.6 |
| ugh_v2_delta | month_end | 1 | 100.0% | 100.0% | 10.2 |
| ugh_v2_delta | quarter_end | 1 | 100.0% | 100.0% | 10.2 |
| ugh_v2_gamma | month_end | 1 | 100.0% | 100.0% | 11.4 |
| ugh_v2_gamma | quarter_end | 1 | 100.0% | 100.0% | 11.4 |

## AI Annotation Layer

- **AI annotated**: 28
- **Auto annotated**: 0
- **Manual compat**: 0
- **OHLC fallback**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Fallback | Effective | Missing |
|---|---|---|---|---|---|---|
| regime_label | 28 | 0 | 0 | 0 | 28 | 0 |
| event_tags | 0 | 7 | 0 | 0 | 7 | 21 |
| volatility_label | 28 | 0 | 0 | 0 | 28 | 0 |
| intervention_risk | 28 | 0 | 0 | 0 | 28 | 0 |
| failure_reason | 4 | 0 | 0 | 0 | 4 | 24 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 25.0% | - | 39.9 |
| baseline_random_walk | low | 4 | 0.0% | - | 13.9 |
| baseline_simple_technical | low | 4 | 75.0% | - | 30.5 |
| ugh_v2_alpha | low | 4 | 75.0% | 100.0% | 14.7 |
| ugh_v2_beta | low | 4 | 75.0% | 100.0% | 11.6 |
| ugh_v2_delta | low | 4 | 75.0% | 100.0% | 13.1 |
| ugh_v2_gamma | low | 4 | 75.0% | 100.0% | 14.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 25.0% | - | 39.9 |
| baseline_random_walk | trending | 4 | 0.0% | - | 13.9 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 30.5 |
| ugh_v2_alpha | trending | 4 | 75.0% | 100.0% | 14.7 |
| ugh_v2_beta | trending | 4 | 75.0% | 100.0% | 11.6 |
| ugh_v2_delta | trending | 4 | 75.0% | 100.0% | 13.1 |
| ugh_v2_gamma | trending | 4 | 75.0% | 100.0% | 14.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 0.0% | - | 8.8 |
| baseline_prev_day_direction | normal | 3 | 33.3% | - | 50.3 |
| baseline_random_walk | low | 1 | 0.0% | - | 7.6 |
| baseline_random_walk | normal | 3 | 0.0% | - | 16.1 |
| baseline_simple_technical | low | 1 | 0.0% | - | 8.8 |
| baseline_simple_technical | normal | 3 | 100.0% | - | 37.8 |
| ugh_v2_alpha | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_alpha | normal | 3 | 100.0% | 100.0% | 17.1 |
| ugh_v2_beta | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_beta | normal | 3 | 100.0% | 100.0% | 13.0 |
| ugh_v2_delta | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_delta | normal | 3 | 100.0% | 100.0% | 14.9 |
| ugh_v2_gamma | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_gamma | normal | 3 | 100.0% | 100.0% | 16.8 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (14), yahoo_finance (1)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
