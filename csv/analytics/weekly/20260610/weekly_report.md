# FX Weekly Report v2 — 20260603 to 20260609

Generated: 2026-07-01T06:01:16Z
Report date (JST): 2026-06-10T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 12.8 | 13.1 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 8.9 | 8.8 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | - | 10.0 | 14.2 |
| ugh_v2_alpha | 5 | 4 | 80.0% | 80.0% | 40.0% | - | 8.6 | 8.5 |
| ugh_v2_beta | 5 | 4 | 80.0% | 60.0% | 40.0% | - | 9.3 | 9.8 |
| ugh_v2_delta | 5 | 4 | 80.0% | 80.0% | 40.0% | - | 9.0 | 9.2 |
| ugh_v2_gamma | 5 | 4 | 80.0% | 80.0% | 40.0% | - | 8.3 | 8.8 |

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
| failure_reason | 4 | 0 | 0 | 0 | 4 | 31 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 60.0% | - | 12.8 |
| baseline_random_walk | low | 5 | 0.0% | - | 8.9 |
| baseline_simple_technical | low | 5 | 80.0% | - | 10.0 |
| ugh_v2_alpha | low | 5 | 80.0% | 80.0% | 8.6 |
| ugh_v2_beta | low | 5 | 80.0% | 60.0% | 9.3 |
| ugh_v2_delta | low | 5 | 80.0% | 80.0% | 9.0 |
| ugh_v2_gamma | low | 5 | 80.0% | 80.0% | 8.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 12.8 |
| baseline_random_walk | trending | 5 | 0.0% | - | 8.9 |
| baseline_simple_technical | trending | 5 | 80.0% | - | 10.0 |
| ugh_v2_alpha | trending | 5 | 80.0% | 80.0% | 8.6 |
| ugh_v2_beta | trending | 5 | 80.0% | 60.0% | 9.3 |
| ugh_v2_delta | trending | 5 | 80.0% | 80.0% | 9.0 |
| ugh_v2_gamma | trending | 5 | 80.0% | 80.0% | 8.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 6.3 |
| baseline_prev_day_direction | normal | 4 | 50.0% | - | 14.4 |
| baseline_random_walk | high | 1 | 0.0% | - | 8.8 |
| baseline_random_walk | normal | 4 | 0.0% | - | 8.9 |
| baseline_simple_technical | high | 1 | 100.0% | - | 14.2 |
| baseline_simple_technical | normal | 4 | 75.0% | - | 9.0 |
| ugh_v2_alpha | high | 1 | 100.0% | 100.0% | 4.7 |
| ugh_v2_alpha | normal | 4 | 75.0% | 75.0% | 9.6 |
| ugh_v2_beta | high | 1 | 100.0% | 100.0% | 4.7 |
| ugh_v2_beta | normal | 4 | 75.0% | 50.0% | 10.5 |
| ugh_v2_delta | high | 1 | 100.0% | 100.0% | 4.7 |
| ugh_v2_delta | normal | 4 | 75.0% | 75.0% | 10.1 |
| ugh_v2_gamma | high | 1 | 100.0% | 100.0% | 3.5 |
| ugh_v2_gamma | normal | 4 | 75.0% | 75.0% | 9.5 |

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
