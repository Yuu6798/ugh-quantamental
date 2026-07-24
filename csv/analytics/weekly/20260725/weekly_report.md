# FX Weekly Report v2 — 20260720 to 20260724

Generated: 2026-07-24T12:15:13Z
Report date (JST): 2026-07-25T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 33.0 | 39.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 24.1 | 25.2 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 20.4 | 22.3 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 50.0% | 100.0% | 0.0% | 22.4 | 23.9 |
| ugh_v2_beta | 4 | 3 | 75.0% | 50.0% | 100.0% | 0.0% | 23.3 | 24.8 |
| ugh_v2_delta | 4 | 3 | 75.0% | 50.0% | 100.0% | 0.0% | 22.9 | 24.3 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 50.0% | 100.0% | 0.0% | 22.4 | 23.7 |

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
| failure_reason | 4 | 0 | 0 | 0 | 4 | 24 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 50.0% | - | 33.0 |
| baseline_random_walk | low | 4 | 0.0% | - | 24.1 |
| baseline_simple_technical | low | 4 | 75.0% | - | 20.4 |
| ugh_v2_alpha | low | 4 | 75.0% | 50.0% | 22.4 |
| ugh_v2_beta | low | 4 | 75.0% | 50.0% | 23.3 |
| ugh_v2_delta | low | 4 | 75.0% | 50.0% | 22.9 |
| ugh_v2_gamma | low | 4 | 75.0% | 50.0% | 22.4 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 33.0 |
| baseline_random_walk | trending | 4 | 0.0% | - | 24.1 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 20.4 |
| ugh_v2_alpha | trending | 4 | 75.0% | 50.0% | 22.4 |
| ugh_v2_beta | trending | 4 | 75.0% | 50.0% | 23.3 |
| ugh_v2_delta | trending | 4 | 75.0% | 50.0% | 22.9 |
| ugh_v2_gamma | trending | 4 | 75.0% | 50.0% | 22.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 40.2 |
| baseline_prev_day_direction | low | 1 | 100.0% | - | 7.4 |
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 44.3 |
| baseline_random_walk | high | 2 | 0.0% | - | 43.3 |
| baseline_random_walk | low | 1 | 0.0% | - | 8.0 |
| baseline_random_walk | normal | 1 | 0.0% | - | 1.8 |
| baseline_simple_technical | high | 2 | 100.0% | - | 22.3 |
| baseline_simple_technical | low | 1 | 100.0% | - | 12.9 |
| baseline_simple_technical | normal | 1 | 0.0% | - | 24.2 |
| ugh_v2_alpha | high | 2 | 100.0% | 0.0% | 37.6 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 3.1 |
| ugh_v2_alpha | normal | 1 | 0.0% | 100.0% | 11.3 |
| ugh_v2_beta | high | 2 | 100.0% | 0.0% | 37.9 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 3.8 |
| ugh_v2_beta | normal | 1 | 0.0% | 100.0% | 13.8 |
| ugh_v2_delta | high | 2 | 100.0% | 0.0% | 37.7 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 3.5 |
| ugh_v2_delta | normal | 1 | 0.0% | 100.0% | 12.6 |
| ugh_v2_gamma | high | 2 | 100.0% | 0.0% | 38.0 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 3.3 |
| ugh_v2_gamma | normal | 1 | 0.0% | 100.0% | 10.5 |

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
