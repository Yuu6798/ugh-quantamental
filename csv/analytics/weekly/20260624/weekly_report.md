# FX Weekly Report v2 — 20260617 to 20260623

Generated: 2026-07-01T06:01:16Z
Report date (JST): 2026-06-24T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 24.4 | 22.9 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 17.2 | 15.6 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | - | 13.9 | 12.2 |
| ugh_v2_alpha | 5 | 4 | 80.0% | 60.0% | 60.0% | - | 16.3 | 12.5 |
| ugh_v2_beta | 5 | 3 | 60.0% | 40.0% | 60.0% | - | 17.0 | 13.5 |
| ugh_v2_delta | 5 | 3 | 60.0% | 40.0% | 60.0% | - | 16.9 | 12.9 |
| ugh_v2_gamma | 5 | 4 | 80.0% | 80.0% | 60.0% | - | 16.3 | 12.3 |

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
| failure_reason | 6 | 0 | 0 | 0 | 6 | 29 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 60.0% | - | 24.4 |
| baseline_random_walk | low | 5 | 0.0% | - | 17.2 |
| baseline_simple_technical | low | 5 | 80.0% | - | 13.9 |
| ugh_v2_alpha | low | 5 | 80.0% | 60.0% | 16.3 |
| ugh_v2_beta | low | 5 | 60.0% | 40.0% | 17.0 |
| ugh_v2_delta | low | 5 | 60.0% | 40.0% | 16.9 |
| ugh_v2_gamma | low | 5 | 80.0% | 80.0% | 16.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 24.4 |
| baseline_random_walk | trending | 5 | 0.0% | - | 17.2 |
| baseline_simple_technical | trending | 5 | 80.0% | - | 13.9 |
| ugh_v2_alpha | trending | 5 | 80.0% | 60.0% | 16.3 |
| ugh_v2_beta | trending | 5 | 60.0% | 40.0% | 17.0 |
| ugh_v2_delta | trending | 5 | 60.0% | 40.0% | 16.9 |
| ugh_v2_gamma | trending | 5 | 80.0% | 80.0% | 16.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 28.6 |
| baseline_prev_day_direction | normal | 4 | 50.0% | - | 23.3 |
| baseline_random_walk | high | 1 | 0.0% | - | 44.2 |
| baseline_random_walk | normal | 4 | 0.0% | - | 10.4 |
| baseline_simple_technical | high | 1 | 100.0% | - | 31.2 |
| baseline_simple_technical | normal | 4 | 75.0% | - | 9.6 |
| ugh_v2_alpha | high | 1 | 100.0% | 0.0% | 39.4 |
| ugh_v2_alpha | normal | 4 | 75.0% | 75.0% | 10.5 |
| ugh_v2_beta | high | 1 | 100.0% | 0.0% | 38.0 |
| ugh_v2_beta | normal | 4 | 50.0% | 50.0% | 11.7 |
| ugh_v2_delta | high | 1 | 100.0% | 0.0% | 38.6 |
| ugh_v2_delta | normal | 4 | 50.0% | 50.0% | 11.5 |
| ugh_v2_gamma | high | 1 | 100.0% | 0.0% | 39.5 |
| ugh_v2_gamma | normal | 4 | 75.0% | 100.0% | 10.5 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 1
- **Lag occurrences**: 1
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
