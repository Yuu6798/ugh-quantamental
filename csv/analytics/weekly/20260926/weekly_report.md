# FX Weekly Report v2 — 20260921 to 20260925

Generated: 2026-09-25T15:51:20Z
Report date (JST): 2026-09-26T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 4 | 100.0% | - | - | - | 31.2 | 28.5 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 36.7 | 38.4 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | - | 44.2 | 38.2 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 100.0% | 75.0% | 50.0% | 27.2 | 25.8 |
| ugh_v2_beta | 4 | 4 | 100.0% | 100.0% | 75.0% | 50.0% | 22.7 | 19.4 |
| ugh_v2_delta | 4 | 3 | 75.0% | 100.0% | 75.0% | 50.0% | 25.6 | 24.5 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 100.0% | 75.0% | 50.0% | 27.8 | 26.7 |

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
| failure_reason | 3 | 0 | 0 | 0 | 3 | 25 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 100.0% | - | 25.0 |
| baseline_prev_day_direction | medium | 1 | 100.0% | - | 49.6 |
| baseline_random_walk | low | 3 | 0.0% | - | 29.0 |
| baseline_random_walk | medium | 1 | 0.0% | - | 59.7 |
| baseline_simple_technical | low | 3 | 33.3% | - | 55.4 |
| baseline_simple_technical | medium | 1 | 100.0% | - | 10.5 |
| ugh_v2_alpha | low | 3 | 66.7% | 100.0% | 19.2 |
| ugh_v2_alpha | medium | 1 | 100.0% | 100.0% | 51.1 |
| ugh_v2_beta | low | 3 | 100.0% | 100.0% | 13.3 |
| ugh_v2_beta | medium | 1 | 100.0% | 100.0% | 50.6 |
| ugh_v2_delta | low | 3 | 66.7% | 100.0% | 17.1 |
| ugh_v2_delta | medium | 1 | 100.0% | 100.0% | 51.0 |
| ugh_v2_gamma | low | 3 | 66.7% | 100.0% | 19.8 |
| ugh_v2_gamma | medium | 1 | 100.0% | 100.0% | 51.7 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 100.0% | - | 31.2 |
| baseline_random_walk | trending | 4 | 0.0% | - | 36.7 |
| baseline_simple_technical | trending | 4 | 50.0% | - | 44.2 |
| ugh_v2_alpha | trending | 4 | 75.0% | 100.0% | 27.2 |
| ugh_v2_beta | trending | 4 | 100.0% | 100.0% | 22.7 |
| ugh_v2_delta | trending | 4 | 75.0% | 100.0% | 25.6 |
| ugh_v2_gamma | trending | 4 | 75.0% | 100.0% | 27.8 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 4 | 100.0% | - | 31.2 |
| baseline_random_walk | normal | 4 | 0.0% | - | 36.7 |
| baseline_simple_technical | normal | 4 | 50.0% | - | 44.2 |
| ugh_v2_alpha | normal | 4 | 75.0% | 100.0% | 27.2 |
| ugh_v2_beta | normal | 4 | 100.0% | 100.0% | 22.7 |
| ugh_v2_delta | normal | 4 | 75.0% | 100.0% | 25.6 |
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
