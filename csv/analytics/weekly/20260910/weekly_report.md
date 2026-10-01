# FX Weekly Report v2 — 20260903 to 20260909

Generated: 2026-10-01T07:29:19Z
Report date (JST): 2026-09-10T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 101.5 | 91.0 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 72.8 | 29.2 |
| baseline_simple_technical | 5 | 3 | 60.0% | - | - | - | 72.1 | 63.4 |
| ugh_v2_alpha | 5 | 2 | 40.0% | 60.0% | 80.0% | 0.0% | 72.0 | 34.0 |
| ugh_v2_beta | 5 | 3 | 60.0% | 60.0% | 60.0% | 0.0% | 71.0 | 39.0 |
| ugh_v2_delta | 5 | 2 | 40.0% | 60.0% | 80.0% | 0.0% | 72.0 | 36.4 |
| ugh_v2_gamma | 5 | 2 | 40.0% | 60.0% | 80.0% | 0.0% | 71.9 | 33.6 |

## AI Annotation Layer

- **AI annotated**: 35
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
| regime_label | 35 | 0 | 0 | 0 | 35 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 35 |
| volatility_label | 35 | 0 | 0 | 0 | 35 | 0 |
| intervention_risk | 35 | 0 | 0 | 0 | 35 | 0 |
| failure_reason | 11 | 0 | 0 | 0 | 11 | 24 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 109.6 |
| baseline_prev_day_direction | low | 3 | 66.7% | - | 96.2 |
| baseline_random_walk | high | 2 | 0.0% | - | 141.7 |
| baseline_random_walk | low | 3 | 0.0% | - | 26.9 |
| baseline_simple_technical | high | 2 | 50.0% | - | 138.6 |
| baseline_simple_technical | low | 3 | 66.7% | - | 27.8 |
| ugh_v2_alpha | high | 2 | 0.0% | 0.0% | 141.7 |
| ugh_v2_alpha | low | 3 | 66.7% | 100.0% | 25.5 |
| ugh_v2_beta | high | 2 | 50.0% | 0.0% | 139.1 |
| ugh_v2_beta | low | 3 | 66.7% | 100.0% | 25.7 |
| ugh_v2_delta | high | 2 | 0.0% | 0.0% | 141.7 |
| ugh_v2_delta | low | 3 | 66.7% | 100.0% | 25.5 |
| ugh_v2_gamma | high | 2 | 0.0% | 0.0% | 141.7 |
| ugh_v2_gamma | low | 3 | 66.7% | 100.0% | 25.4 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 101.5 |
| baseline_random_walk | trending | 5 | 0.0% | - | 72.8 |
| baseline_simple_technical | trending | 5 | 60.0% | - | 72.1 |
| ugh_v2_alpha | trending | 5 | 40.0% | 60.0% | 72.0 |
| ugh_v2_beta | trending | 5 | 60.0% | 60.0% | 71.0 |
| ugh_v2_delta | trending | 5 | 40.0% | 60.0% | 72.0 |
| ugh_v2_gamma | trending | 5 | 40.0% | 60.0% | 71.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 91.0 |
| baseline_prev_day_direction | low | 1 | 100.0% | - | 4.0 |
| baseline_prev_day_direction | normal | 3 | 33.3% | - | 137.6 |
| baseline_random_walk | high | 1 | 0.0% | - | 181.5 |
| baseline_random_walk | low | 1 | 0.0% | - | 29.2 |
| baseline_random_walk | normal | 3 | 0.0% | - | 51.2 |
| baseline_simple_technical | high | 1 | 0.0% | - | 211.7 |
| baseline_simple_technical | low | 1 | 100.0% | - | 8.5 |
| baseline_simple_technical | normal | 3 | 66.7% | - | 46.8 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 181.5 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 10.6 |
| ugh_v2_alpha | normal | 3 | 33.3% | 66.7% | 56.0 |
| ugh_v2_beta | high | 1 | 100.0% | 0.0% | 176.1 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 6.2 |
| ugh_v2_beta | normal | 3 | 33.3% | 66.7% | 57.6 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 181.5 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 8.3 |
| ugh_v2_delta | normal | 3 | 33.3% | 66.7% | 56.7 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 181.5 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 10.6 |
| ugh_v2_gamma | normal | 3 | 33.3% | 66.7% | 55.8 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
