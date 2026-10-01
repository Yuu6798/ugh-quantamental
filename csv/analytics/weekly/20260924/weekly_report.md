# FX Weekly Report v2 — 20260917 to 20260923

Generated: 2026-10-01T07:29:19Z
Report date (JST): 2026-09-24T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 54.0 | 49.6 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 37.9 | 42.1 |
| baseline_simple_technical | 5 | 2 | 40.0% | - | - | - | 58.9 | 59.3 |
| ugh_v2_alpha | 5 | 3 | 60.0% | 100.0% | 80.0% | 20.0% | 38.2 | 42.1 |
| ugh_v2_beta | 5 | 3 | 60.0% | 100.0% | 80.0% | 20.0% | 36.0 | 34.6 |
| ugh_v2_delta | 5 | 2 | 40.0% | 100.0% | 80.0% | 20.0% | 38.3 | 42.1 |
| ugh_v2_gamma | 5 | 3 | 60.0% | 100.0% | 80.0% | 20.0% | 38.2 | 42.1 |

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
| failure_reason | 9 | 0 | 0 | 0 | 9 | 26 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 47.6 |
| baseline_prev_day_direction | medium | 2 | 50.0% | - | 63.6 |
| baseline_random_walk | low | 3 | 0.0% | - | 23.2 |
| baseline_random_walk | medium | 2 | 0.0% | - | 60.0 |
| baseline_simple_technical | low | 3 | 33.3% | - | 59.5 |
| baseline_simple_technical | medium | 2 | 50.0% | - | 57.8 |
| ugh_v2_alpha | low | 3 | 66.7% | 100.0% | 19.7 |
| ugh_v2_alpha | medium | 2 | 50.0% | 100.0% | 66.0 |
| ugh_v2_beta | low | 3 | 66.7% | 100.0% | 17.7 |
| ugh_v2_beta | medium | 2 | 50.0% | 100.0% | 63.5 |
| ugh_v2_delta | low | 3 | 33.3% | 100.0% | 20.5 |
| ugh_v2_delta | medium | 2 | 50.0% | 100.0% | 65.0 |
| ugh_v2_gamma | low | 3 | 66.7% | 100.0% | 19.9 |
| ugh_v2_gamma | medium | 2 | 50.0% | 100.0% | 65.6 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 54.0 |
| baseline_random_walk | trending | 5 | 0.0% | - | 37.9 |
| baseline_simple_technical | trending | 5 | 40.0% | - | 58.9 |
| ugh_v2_alpha | trending | 5 | 60.0% | 100.0% | 38.2 |
| ugh_v2_beta | trending | 5 | 60.0% | 100.0% | 36.0 |
| ugh_v2_delta | trending | 5 | 40.0% | 100.0% | 38.3 |
| ugh_v2_gamma | trending | 5 | 60.0% | 100.0% | 38.2 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 77.6 |
| baseline_prev_day_direction | normal | 4 | 75.0% | - | 48.1 |
| baseline_random_walk | high | 1 | 0.0% | - | 60.3 |
| baseline_random_walk | normal | 4 | 0.0% | - | 32.3 |
| baseline_simple_technical | high | 1 | 0.0% | - | 105.2 |
| baseline_simple_technical | normal | 4 | 50.0% | - | 47.3 |
| ugh_v2_alpha | high | 1 | 0.0% | 100.0% | 80.8 |
| ugh_v2_alpha | normal | 4 | 75.0% | 100.0% | 27.6 |
| ugh_v2_beta | high | 1 | 0.0% | 100.0% | 76.4 |
| ugh_v2_beta | normal | 4 | 75.0% | 100.0% | 25.9 |
| ugh_v2_delta | high | 1 | 0.0% | 100.0% | 78.9 |
| ugh_v2_delta | normal | 4 | 50.0% | 100.0% | 28.2 |
| ugh_v2_gamma | high | 1 | 0.0% | 100.0% | 79.6 |
| ugh_v2_gamma | normal | 4 | 75.0% | 100.0% | 27.8 |

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
