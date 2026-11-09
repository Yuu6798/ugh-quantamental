# FX Weekly Report v2 — 20261102 to 20261106

Generated: 2026-11-09T07:30:05Z
Report date (JST): 2026-11-09T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 36.7 | 35.2 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 34.6 | 38.6 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 47.9 | 58.3 |
| ugh_v2_alpha | 4 | 0 | 0.0% | 100.0% | 50.0% | 0.0% | 34.6 | 38.6 |
| ugh_v2_beta | 4 | 1 | 25.0% | 100.0% | 50.0% | 0.0% | 34.6 | 36.1 |
| ugh_v2_delta | 4 | 1 | 25.0% | 100.0% | 50.0% | 0.0% | 34.6 | 36.7 |
| ugh_v2_gamma | 4 | 0 | 0.0% | 100.0% | 50.0% | 0.0% | 34.6 | 38.6 |

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
| failure_reason | 14 | 0 | 0 | 0 | 14 | 14 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 50.0% | - | 36.7 |
| baseline_random_walk | low | 4 | 0.0% | - | 34.6 |
| baseline_simple_technical | low | 4 | 25.0% | - | 47.9 |
| ugh_v2_alpha | low | 4 | 0.0% | 100.0% | 34.6 |
| ugh_v2_beta | low | 4 | 25.0% | 100.0% | 34.6 |
| ugh_v2_delta | low | 4 | 25.0% | 100.0% | 34.6 |
| ugh_v2_gamma | low | 4 | 0.0% | 100.0% | 34.6 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 36.7 |
| baseline_random_walk | trending | 4 | 0.0% | - | 34.6 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 47.9 |
| ugh_v2_alpha | trending | 4 | 0.0% | 100.0% | 34.6 |
| ugh_v2_beta | trending | 4 | 25.0% | 100.0% | 34.6 |
| ugh_v2_delta | trending | 4 | 25.0% | 100.0% | 34.6 |
| ugh_v2_gamma | trending | 4 | 0.0% | 100.0% | 34.6 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 38.2 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 35.2 |
| baseline_random_walk | high | 2 | 0.0% | - | 30.7 |
| baseline_random_walk | normal | 2 | 0.0% | - | 38.6 |
| baseline_simple_technical | high | 2 | 50.0% | - | 36.2 |
| baseline_simple_technical | normal | 2 | 0.0% | - | 59.5 |
| ugh_v2_alpha | high | 2 | 0.0% | 100.0% | 30.7 |
| ugh_v2_alpha | normal | 2 | 0.0% | 100.0% | 38.6 |
| ugh_v2_beta | high | 2 | 50.0% | 100.0% | 30.5 |
| ugh_v2_beta | normal | 2 | 0.0% | 100.0% | 38.6 |
| ugh_v2_delta | high | 2 | 50.0% | 100.0% | 30.6 |
| ugh_v2_delta | normal | 2 | 0.0% | 100.0% | 38.6 |
| ugh_v2_gamma | high | 2 | 0.0% | 100.0% | 30.7 |
| ugh_v2_gamma | normal | 2 | 0.0% | 100.0% | 38.6 |

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
