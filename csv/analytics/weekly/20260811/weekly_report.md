# FX Weekly Report v2 — 20260804 to 20260810

Generated: 2026-09-01T06:30:34Z
Report date (JST): 2026-08-11T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 0 | 0.0% | - | - | - | 68.3 | 44.4 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 43.6 | 39.8 |
| baseline_simple_technical | 5 | 2 | 40.0% | - | - | - | 63.3 | 68.0 |
| ugh_v2_alpha | 5 | 2 | 40.0% | 80.0% | 100.0% | 20.0% | 57.1 | 52.0 |
| ugh_v2_beta | 5 | 0 | 0.0% | 80.0% | 100.0% | 20.0% | 55.7 | 46.0 |
| ugh_v2_delta | 5 | 0 | 0.0% | 80.0% | 100.0% | 20.0% | 57.0 | 48.7 |
| ugh_v2_gamma | 5 | 2 | 40.0% | 80.0% | 100.0% | 20.0% | 56.7 | 52.0 |

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
| failure_reason | 16 | 0 | 0 | 0 | 16 | 19 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 0.0% | - | 50.7 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 138.7 |
| baseline_random_walk | low | 4 | 0.0% | - | 29.8 |
| baseline_random_walk | medium | 1 | 0.0% | - | 98.9 |
| baseline_simple_technical | low | 4 | 50.0% | - | 45.7 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 133.6 |
| ugh_v2_alpha | low | 4 | 50.0% | 100.0% | 36.9 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 137.9 |
| ugh_v2_beta | low | 4 | 0.0% | 100.0% | 34.7 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 139.8 |
| ugh_v2_delta | low | 4 | 0.0% | 100.0% | 36.1 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 140.5 |
| ugh_v2_gamma | low | 4 | 50.0% | 100.0% | 36.9 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 136.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 0.0% | - | 68.3 |
| baseline_random_walk | trending | 5 | 0.0% | - | 43.6 |
| baseline_simple_technical | trending | 5 | 40.0% | - | 63.3 |
| ugh_v2_alpha | trending | 5 | 40.0% | 80.0% | 57.1 |
| ugh_v2_beta | trending | 5 | 0.0% | 80.0% | 55.7 |
| ugh_v2_delta | trending | 5 | 0.0% | 80.0% | 57.0 |
| ugh_v2_gamma | trending | 5 | 40.0% | 80.0% | 56.7 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 0.0% | - | 40.0 |
| baseline_prev_day_direction | normal | 2 | 0.0% | - | 110.8 |
| baseline_random_walk | low | 3 | 0.0% | - | 26.5 |
| baseline_random_walk | normal | 2 | 0.0% | - | 69.3 |
| baseline_simple_technical | low | 3 | 33.3% | - | 59.3 |
| baseline_simple_technical | normal | 2 | 50.0% | - | 69.3 |
| ugh_v2_alpha | low | 3 | 33.3% | 100.0% | 38.4 |
| ugh_v2_alpha | normal | 2 | 50.0% | 50.0% | 85.0 |
| ugh_v2_beta | low | 3 | 0.0% | 100.0% | 33.0 |
| ugh_v2_beta | normal | 2 | 0.0% | 50.0% | 89.8 |
| ugh_v2_delta | low | 3 | 0.0% | 100.0% | 34.9 |
| ugh_v2_delta | normal | 2 | 0.0% | 50.0% | 90.2 |
| ugh_v2_gamma | low | 3 | 33.3% | 100.0% | 38.4 |
| ugh_v2_gamma | normal | 2 | 50.0% | 50.0% | 84.1 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (14), yahoo_finance (1)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
