# FX Weekly Report v2 — 20260610 to 20260616

Generated: 2026-07-01T06:01:16Z
Report date (JST): 2026-06-17T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 24.1 | 11.9 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 16.3 | 11.8 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | - | 13.5 | 4.1 |
| ugh_v2_alpha | 5 | 3 | 60.0% | 60.0% | 40.0% | - | 13.8 | 4.2 |
| ugh_v2_beta | 5 | 3 | 60.0% | 60.0% | 40.0% | - | 14.0 | 3.2 |
| ugh_v2_delta | 5 | 3 | 60.0% | 60.0% | 40.0% | - | 13.9 | 3.6 |
| ugh_v2_gamma | 5 | 3 | 60.0% | 60.0% | 40.0% | - | 13.9 | 4.6 |

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
| failure_reason | 8 | 0 | 0 | 0 | 8 | 27 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 60.0% | - | 24.1 |
| baseline_random_walk | low | 5 | 0.0% | - | 16.3 |
| baseline_simple_technical | low | 5 | 80.0% | - | 13.5 |
| ugh_v2_alpha | low | 5 | 60.0% | 60.0% | 13.8 |
| ugh_v2_beta | low | 5 | 60.0% | 60.0% | 14.0 |
| ugh_v2_delta | low | 5 | 60.0% | 60.0% | 13.9 |
| ugh_v2_gamma | low | 5 | 60.0% | 60.0% | 13.9 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 24.1 |
| baseline_random_walk | trending | 5 | 0.0% | - | 16.3 |
| baseline_simple_technical | trending | 5 | 80.0% | - | 13.5 |
| ugh_v2_alpha | trending | 5 | 60.0% | 60.0% | 13.8 |
| ugh_v2_beta | trending | 5 | 60.0% | 60.0% | 14.0 |
| ugh_v2_delta | trending | 5 | 60.0% | 60.0% | 13.9 |
| ugh_v2_gamma | trending | 5 | 60.0% | 60.0% | 13.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 48.0 |
| baseline_prev_day_direction | normal | 4 | 75.0% | - | 18.1 |
| baseline_random_walk | high | 1 | 0.0% | - | 36.1 |
| baseline_random_walk | normal | 4 | 0.0% | - | 11.4 |
| baseline_simple_technical | high | 1 | 0.0% | - | 50.0 |
| baseline_simple_technical | normal | 4 | 100.0% | - | 4.3 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 43.5 |
| ugh_v2_alpha | normal | 4 | 75.0% | 75.0% | 6.5 |
| ugh_v2_beta | high | 1 | 0.0% | 0.0% | 44.3 |
| ugh_v2_beta | normal | 4 | 75.0% | 75.0% | 6.5 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 43.9 |
| ugh_v2_delta | normal | 4 | 75.0% | 75.0% | 6.5 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 43.0 |
| ugh_v2_gamma | normal | 4 | 75.0% | 75.0% | 6.7 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 2
- **Lag occurrences**: 2
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
