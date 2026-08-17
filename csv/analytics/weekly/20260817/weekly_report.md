# FX Weekly Report v2 — 20260810 to 20260814

Generated: 2026-08-17T02:15:21Z
Report date (JST): 2026-08-17T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 62.1 | 52.0 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 29.0 | 7.2 |
| baseline_simple_technical | 4 | 0 | 0.0% | - | - | - | 65.3 | 44.0 |
| ugh_v2_alpha | 4 | 0 | 0.0% | 75.0% | 100.0% | 25.0% | 43.3 | 16.3 |
| ugh_v2_beta | 4 | 1 | 25.0% | 75.0% | 75.0% | 50.0% | 40.3 | 9.6 |
| ugh_v2_delta | 4 | 0 | 0.0% | 75.0% | 75.0% | 50.0% | 42.5 | 13.5 |
| ugh_v2_gamma | 4 | 0 | 0.0% | 75.0% | 100.0% | 25.0% | 42.4 | 15.5 |

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
| failure_reason | 15 | 0 | 0 | 0 | 15 | 13 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 100.0% | - | 36.5 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 138.7 |
| baseline_random_walk | low | 3 | 0.0% | - | 5.7 |
| baseline_random_walk | medium | 1 | 0.0% | - | 98.9 |
| baseline_simple_technical | low | 3 | 0.0% | - | 42.5 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 133.6 |
| ugh_v2_alpha | low | 3 | 0.0% | 100.0% | 11.7 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 137.9 |
| ugh_v2_beta | low | 3 | 33.3% | 100.0% | 7.1 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 139.8 |
| ugh_v2_delta | low | 3 | 0.0% | 100.0% | 9.8 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 140.5 |
| ugh_v2_gamma | low | 3 | 0.0% | 100.0% | 11.2 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 136.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 62.1 |
| baseline_random_walk | trending | 4 | 0.0% | - | 29.0 |
| baseline_simple_technical | trending | 4 | 0.0% | - | 65.3 |
| ugh_v2_alpha | trending | 4 | 0.0% | 75.0% | 43.3 |
| ugh_v2_beta | trending | 4 | 25.0% | 75.0% | 40.3 |
| ugh_v2_delta | trending | 4 | 0.0% | 75.0% | 42.5 |
| ugh_v2_gamma | trending | 4 | 0.0% | 75.0% | 42.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 100.0% | - | 51.0 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 73.1 |
| baseline_random_walk | low | 2 | 0.0% | - | 3.5 |
| baseline_random_walk | normal | 2 | 0.0% | - | 54.5 |
| baseline_simple_technical | low | 2 | 0.0% | - | 40.4 |
| baseline_simple_technical | normal | 2 | 0.0% | - | 90.1 |
| ugh_v2_alpha | low | 2 | 0.0% | 100.0% | 7.5 |
| ugh_v2_alpha | normal | 2 | 0.0% | 50.0% | 79.0 |
| ugh_v2_beta | low | 2 | 50.0% | 100.0% | 3.2 |
| ugh_v2_beta | normal | 2 | 0.0% | 50.0% | 77.3 |
| ugh_v2_delta | low | 2 | 0.0% | 100.0% | 6.0 |
| ugh_v2_delta | normal | 2 | 0.0% | 50.0% | 79.0 |
| ugh_v2_gamma | low | 2 | 0.0% | 100.0% | 7.2 |
| ugh_v2_gamma | normal | 2 | 0.0% | 50.0% | 77.6 |

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
