# FX Weekly Report v2 — 20260727 to 20260731

Generated: 2026-08-01T04:49:32Z
Report date (JST): 2026-08-03T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 63.6 | 21.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 68.8 | 18.0 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | - | 85.8 | 34.8 |
| ugh_v2_alpha | 4 | 2 | 50.0% | 50.0% | 75.0% | 0.0% | 72.3 | 22.5 |
| ugh_v2_beta | 4 | 2 | 50.0% | 50.0% | 75.0% | 0.0% | 70.0 | 21.0 |
| ugh_v2_delta | 4 | 2 | 50.0% | 50.0% | 75.0% | 0.0% | 70.1 | 21.7 |
| ugh_v2_gamma | 4 | 2 | 50.0% | 50.0% | 75.0% | 0.0% | 71.8 | 21.8 |

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
| event_tags | 0 | 0 | 0 | 0 | 0 | 28 |
| volatility_label | 28 | 0 | 0 | 0 | 28 | 0 |
| intervention_risk | 28 | 0 | 0 | 0 | 28 | 0 |
| failure_reason | 8 | 0 | 0 | 0 | 8 | 20 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 210.0 |
| baseline_prev_day_direction | low | 3 | 66.7% | - | 14.9 |
| baseline_random_walk | high | 1 | 0.0% | - | 236.9 |
| baseline_random_walk | low | 3 | 0.0% | - | 12.8 |
| baseline_simple_technical | high | 1 | 0.0% | - | 259.7 |
| baseline_simple_technical | low | 3 | 66.7% | - | 27.8 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 243.3 |
| ugh_v2_alpha | low | 3 | 66.7% | 66.7% | 15.3 |
| ugh_v2_beta | high | 1 | 0.0% | 0.0% | 236.9 |
| ugh_v2_beta | low | 3 | 66.7% | 66.7% | 14.4 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 236.9 |
| ugh_v2_delta | low | 3 | 66.7% | 66.7% | 14.5 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 243.0 |
| ugh_v2_gamma | low | 3 | 66.7% | 66.7% | 14.7 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 63.6 |
| baseline_random_walk | trending | 4 | 0.0% | - | 68.8 |
| baseline_simple_technical | trending | 4 | 50.0% | - | 85.8 |
| ugh_v2_alpha | trending | 4 | 50.0% | 50.0% | 72.3 |
| ugh_v2_beta | trending | 4 | 50.0% | 50.0% | 70.0 |
| ugh_v2_delta | trending | 4 | 50.0% | 50.0% | 70.1 |
| ugh_v2_gamma | trending | 4 | 50.0% | 50.0% | 71.8 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 210.0 |
| baseline_prev_day_direction | low | 1 | 100.0% | - | 6.7 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 18.9 |
| baseline_random_walk | high | 1 | 0.0% | - | 236.9 |
| baseline_random_walk | low | 1 | 0.0% | - | 9.2 |
| baseline_random_walk | normal | 2 | 0.0% | - | 14.7 |
| baseline_simple_technical | high | 1 | 0.0% | - | 259.7 |
| baseline_simple_technical | low | 1 | 100.0% | - | 13.8 |
| baseline_simple_technical | normal | 2 | 50.0% | - | 34.8 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 243.3 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 1.0 |
| ugh_v2_alpha | normal | 2 | 50.0% | 50.0% | 22.5 |
| ugh_v2_beta | high | 1 | 0.0% | 0.0% | 236.9 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 1.1 |
| ugh_v2_beta | normal | 2 | 50.0% | 50.0% | 21.0 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 236.9 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 0.1 |
| ugh_v2_delta | normal | 2 | 50.0% | 50.0% | 21.7 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 243.0 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 0.5 |
| ugh_v2_gamma | normal | 2 | 50.0% | 50.0% | 21.8 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
