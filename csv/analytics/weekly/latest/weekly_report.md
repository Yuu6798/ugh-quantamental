# FX Weekly Report v2 — 20261019 to 20261023

Generated: 2026-10-26T12:44:06Z
Report date (JST): 2026-10-24T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 46.8 | 41.8 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 34.9 | 25.9 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 46.1 | 34.3 |
| ugh_v2_alpha | 4 | 1 | 25.0% | 75.0% | 100.0% | 75.0% | 36.0 | 26.4 |
| ugh_v2_beta | 4 | 1 | 25.0% | 75.0% | 100.0% | 75.0% | 36.0 | 28.0 |
| ugh_v2_delta | 4 | 1 | 25.0% | 75.0% | 100.0% | 75.0% | 36.4 | 27.2 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 75.0% | 100.0% | 75.0% | 35.9 | 26.3 |

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
| failure_reason | 12 | 0 | 0 | 0 | 12 | 16 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 33.9 |
| baseline_prev_day_direction | medium | 1 | 100.0% | - | 85.4 |
| baseline_random_walk | low | 3 | 0.0% | - | 17.7 |
| baseline_random_walk | medium | 1 | 0.0% | - | 86.6 |
| baseline_simple_technical | low | 3 | 33.3% | - | 25.6 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 107.8 |
| ugh_v2_alpha | low | 3 | 33.3% | 100.0% | 18.0 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 90.0 |
| ugh_v2_beta | low | 3 | 33.3% | 100.0% | 19.1 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 86.6 |
| ugh_v2_delta | low | 3 | 33.3% | 100.0% | 18.6 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 89.7 |
| ugh_v2_gamma | low | 3 | 33.3% | 100.0% | 17.9 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 89.9 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 46.8 |
| baseline_random_walk | trending | 4 | 0.0% | - | 34.9 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 46.1 |
| ugh_v2_alpha | trending | 4 | 25.0% | 75.0% | 36.0 |
| ugh_v2_beta | trending | 4 | 25.0% | 75.0% | 36.0 |
| ugh_v2_delta | trending | 4 | 25.0% | 75.0% | 36.4 |
| ugh_v2_gamma | trending | 4 | 25.0% | 75.0% | 35.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 85.4 |
| baseline_prev_day_direction | normal | 3 | 66.7% | - | 33.9 |
| baseline_random_walk | high | 1 | 0.0% | - | 86.6 |
| baseline_random_walk | normal | 3 | 0.0% | - | 17.7 |
| baseline_simple_technical | high | 1 | 0.0% | - | 107.8 |
| baseline_simple_technical | normal | 3 | 33.3% | - | 25.6 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 90.0 |
| ugh_v2_alpha | normal | 3 | 33.3% | 100.0% | 18.0 |
| ugh_v2_beta | high | 1 | 0.0% | 0.0% | 86.6 |
| ugh_v2_beta | normal | 3 | 33.3% | 100.0% | 19.1 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 89.7 |
| ugh_v2_delta | normal | 3 | 33.3% | 100.0% | 18.6 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 89.9 |
| ugh_v2_gamma | normal | 3 | 33.3% | 100.0% | 17.9 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 4
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 2
- **Lag occurrences**: 2
- **Providers used**: alpha_vantage (14)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
