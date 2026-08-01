# FX Weekly Report v2 — 20260720 to 20260724

Generated: 2026-08-01T04:49:32Z
Report date (JST): 2026-07-27T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 35.1 | 43.5 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 19.4 | 8.0 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | - | 21.0 | 22.6 |
| ugh_v2_alpha | 5 | 4 | 80.0% | 60.0% | 100.0% | 0.0% | 20.4 | 12.2 |
| ugh_v2_beta | 5 | 4 | 80.0% | 60.0% | 100.0% | 0.0% | 21.6 | 14.6 |
| ugh_v2_delta | 5 | 4 | 80.0% | 60.0% | 100.0% | 0.0% | 21.0 | 13.5 |
| ugh_v2_gamma | 5 | 4 | 80.0% | 60.0% | 100.0% | 0.0% | 20.2 | 11.3 |

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
| baseline_prev_day_direction | low | 5 | 60.0% | - | 35.1 |
| baseline_random_walk | low | 5 | 0.0% | - | 19.4 |
| baseline_simple_technical | low | 5 | 80.0% | - | 21.0 |
| ugh_v2_alpha | low | 5 | 80.0% | 60.0% | 20.4 |
| ugh_v2_beta | low | 5 | 80.0% | 60.0% | 21.6 |
| ugh_v2_delta | low | 5 | 80.0% | 60.0% | 21.0 |
| ugh_v2_gamma | low | 5 | 80.0% | 60.0% | 20.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 35.1 |
| baseline_random_walk | trending | 5 | 0.0% | - | 19.4 |
| baseline_simple_technical | trending | 5 | 80.0% | - | 21.0 |
| ugh_v2_alpha | trending | 5 | 80.0% | 60.0% | 20.4 |
| ugh_v2_beta | trending | 5 | 80.0% | 60.0% | 21.6 |
| ugh_v2_delta | trending | 5 | 80.0% | 60.0% | 21.0 |
| ugh_v2_gamma | trending | 5 | 80.0% | 60.0% | 20.2 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 40.2 |
| baseline_prev_day_direction | low | 2 | 100.0% | - | 25.5 |
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 44.3 |
| baseline_random_walk | high | 2 | 0.0% | - | 43.3 |
| baseline_random_walk | low | 2 | 0.0% | - | 4.3 |
| baseline_random_walk | normal | 1 | 0.0% | - | 1.8 |
| baseline_simple_technical | high | 2 | 100.0% | - | 22.3 |
| baseline_simple_technical | low | 2 | 100.0% | - | 18.0 |
| baseline_simple_technical | normal | 1 | 0.0% | - | 24.2 |
| ugh_v2_alpha | high | 2 | 100.0% | 0.0% | 37.6 |
| ugh_v2_alpha | low | 2 | 100.0% | 100.0% | 7.7 |
| ugh_v2_alpha | normal | 1 | 0.0% | 100.0% | 11.3 |
| ugh_v2_beta | high | 2 | 100.0% | 0.0% | 37.9 |
| ugh_v2_beta | low | 2 | 100.0% | 100.0% | 9.2 |
| ugh_v2_beta | normal | 1 | 0.0% | 100.0% | 13.8 |
| ugh_v2_delta | high | 2 | 100.0% | 0.0% | 37.7 |
| ugh_v2_delta | low | 2 | 100.0% | 100.0% | 8.5 |
| ugh_v2_delta | normal | 1 | 0.0% | 100.0% | 12.6 |
| ugh_v2_gamma | high | 2 | 100.0% | 0.0% | 38.0 |
| ugh_v2_gamma | low | 2 | 100.0% | 100.0% | 7.3 |
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
