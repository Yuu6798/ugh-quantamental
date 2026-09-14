# FX Weekly Report v2 — 20260907 to 20260911

Generated: 2026-09-14T05:36:16Z
Report date (JST): 2026-09-14T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 73.5 | 81.0 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 53.1 | 42.6 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 45.0 | 38.4 |
| ugh_v2_alpha | 4 | 2 | 50.0% | 75.0% | 75.0% | 25.0% | 61.4 | 66.6 |
| ugh_v2_beta | 4 | 2 | 50.0% | 75.0% | 75.0% | 25.0% | 59.3 | 64.6 |
| ugh_v2_delta | 4 | 2 | 50.0% | 75.0% | 75.0% | 25.0% | 60.3 | 65.5 |
| ugh_v2_gamma | 4 | 2 | 50.0% | 75.0% | 75.0% | 25.0% | 61.4 | 66.6 |

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
| baseline_prev_day_direction | high | 1 | 0.0% | - | 128.3 |
| baseline_prev_day_direction | low | 2 | 100.0% | - | 40.3 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 85.2 |
| baseline_random_walk | high | 1 | 0.0% | - | 102.0 |
| baseline_random_walk | low | 2 | 0.0% | - | 27.2 |
| baseline_random_walk | medium | 1 | 0.0% | - | 56.0 |
| baseline_simple_technical | high | 1 | 100.0% | - | 65.5 |
| baseline_simple_technical | low | 2 | 100.0% | - | 9.9 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 94.7 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 102.0 |
| ugh_v2_alpha | low | 2 | 100.0% | 100.0% | 21.2 |
| ugh_v2_alpha | medium | 1 | 0.0% | 100.0% | 101.3 |
| ugh_v2_beta | high | 1 | 0.0% | 0.0% | 102.0 |
| ugh_v2_beta | low | 2 | 100.0% | 100.0% | 19.0 |
| ugh_v2_beta | medium | 1 | 0.0% | 100.0% | 97.3 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 102.0 |
| ugh_v2_delta | low | 2 | 100.0% | 100.0% | 20.1 |
| ugh_v2_delta | medium | 1 | 0.0% | 100.0% | 99.2 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 102.0 |
| ugh_v2_gamma | low | 2 | 100.0% | 100.0% | 21.2 |
| ugh_v2_gamma | medium | 1 | 0.0% | 100.0% | 101.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 73.5 |
| baseline_random_walk | trending | 4 | 0.0% | - | 53.1 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 45.0 |
| ugh_v2_alpha | trending | 4 | 50.0% | 75.0% | 61.4 |
| ugh_v2_beta | trending | 4 | 50.0% | 75.0% | 59.3 |
| ugh_v2_delta | trending | 4 | 50.0% | 75.0% | 60.3 |
| ugh_v2_gamma | trending | 4 | 50.0% | 75.0% | 61.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 4.0 |
| baseline_prev_day_direction | normal | 3 | 33.3% | - | 96.7 |
| baseline_random_walk | low | 1 | 0.0% | - | 29.2 |
| baseline_random_walk | normal | 3 | 0.0% | - | 61.1 |
| baseline_simple_technical | low | 1 | 100.0% | - | 8.5 |
| baseline_simple_technical | normal | 3 | 66.7% | - | 57.2 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 10.6 |
| ugh_v2_alpha | normal | 3 | 33.3% | 66.7% | 78.4 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 6.2 |
| ugh_v2_beta | normal | 3 | 33.3% | 66.7% | 77.0 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 8.3 |
| ugh_v2_delta | normal | 3 | 33.3% | 66.7% | 77.7 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 10.6 |
| ugh_v2_gamma | normal | 3 | 33.3% | 66.7% | 78.4 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 5
- **Failed**: 0
- **Skipped**: 9
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (14)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
