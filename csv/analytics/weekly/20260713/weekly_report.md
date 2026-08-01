# FX Weekly Report v2 — 20260706 to 20260710

Generated: 2026-08-01T04:49:32Z
Report date (JST): 2026-07-13T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 4 | 80.0% | - | - | - | 34.8 | 29.6 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 26.2 | 30.2 |
| baseline_simple_technical | 5 | 3 | 60.0% | - | - | - | 30.5 | 26.7 |
| ugh_v2_alpha | 5 | 3 | 60.0% | 0.0% | 60.0% | 20.0% | 28.8 | 26.6 |
| ugh_v2_beta | 5 | 2 | 40.0% | 0.0% | 80.0% | 40.0% | 30.4 | 30.2 |
| ugh_v2_delta | 5 | 3 | 60.0% | 0.0% | 80.0% | 40.0% | 29.2 | 27.1 |
| ugh_v2_gamma | 5 | 3 | 60.0% | 0.0% | 60.0% | 20.0% | 28.8 | 26.7 |

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
| failure_reason | 9 | 0 | 0 | 0 | 9 | 26 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 80.0% | - | 34.8 |
| baseline_random_walk | low | 5 | 0.0% | - | 26.2 |
| baseline_simple_technical | low | 5 | 60.0% | - | 30.5 |
| ugh_v2_alpha | low | 5 | 60.0% | 0.0% | 28.8 |
| ugh_v2_beta | low | 5 | 40.0% | 0.0% | 30.4 |
| ugh_v2_delta | low | 5 | 60.0% | 0.0% | 29.2 |
| ugh_v2_gamma | low | 5 | 60.0% | 0.0% | 28.8 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 80.0% | - | 34.8 |
| baseline_random_walk | trending | 5 | 0.0% | - | 26.2 |
| baseline_simple_technical | trending | 5 | 60.0% | - | 30.5 |
| ugh_v2_alpha | trending | 5 | 60.0% | 0.0% | 28.8 |
| ugh_v2_beta | trending | 5 | 40.0% | 0.0% | 30.4 |
| ugh_v2_delta | trending | 5 | 60.0% | 0.0% | 29.2 |
| ugh_v2_gamma | trending | 5 | 60.0% | 0.0% | 28.8 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 29.0 |
| baseline_prev_day_direction | low | 2 | 50.0% | - | 43.9 |
| baseline_prev_day_direction | normal | 2 | 100.0% | - | 28.7 |
| baseline_random_walk | high | 1 | 0.0% | - | 41.9 |
| baseline_random_walk | low | 2 | 0.0% | - | 6.8 |
| baseline_random_walk | normal | 2 | 0.0% | - | 37.7 |
| baseline_simple_technical | high | 1 | 0.0% | - | 61.6 |
| baseline_simple_technical | low | 2 | 50.0% | - | 27.0 |
| baseline_simple_technical | normal | 2 | 100.0% | - | 18.4 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 41.9 |
| ugh_v2_alpha | low | 2 | 50.0% | 0.0% | 19.5 |
| ugh_v2_alpha | normal | 2 | 100.0% | 0.0% | 31.6 |
| ugh_v2_beta | high | 1 | 0.0% | 0.0% | 41.9 |
| ugh_v2_beta | low | 2 | 50.0% | 0.0% | 23.1 |
| ugh_v2_beta | normal | 2 | 50.0% | 0.0% | 31.8 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 41.9 |
| ugh_v2_delta | low | 2 | 50.0% | 0.0% | 21.4 |
| ugh_v2_delta | normal | 2 | 100.0% | 0.0% | 30.7 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 41.9 |
| ugh_v2_gamma | low | 2 | 50.0% | 0.0% | 19.3 |
| ugh_v2_gamma | normal | 2 | 100.0% | 0.0% | 31.7 |

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
