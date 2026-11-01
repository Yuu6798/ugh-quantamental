# FX Weekly Report v2 — 20261005 to 20261009

Generated: 2026-11-01T07:49:47Z
Report date (JST): 2026-10-12T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 2 | 40.0% | - | - | - | 24.5 | 17.8 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 15.6 | 10.8 |
| baseline_simple_technical | 5 | 3 | 60.0% | - | - | - | 28.1 | 29.9 |
| ugh_v2_alpha | 5 | 3 | 60.0% | 100.0% | 100.0% | 80.0% | 19.2 | 18.6 |
| ugh_v2_beta | 5 | 3 | 60.0% | 100.0% | 100.0% | 80.0% | 19.6 | 20.5 |
| ugh_v2_delta | 5 | 3 | 60.0% | 100.0% | 100.0% | 80.0% | 19.4 | 20.0 |
| ugh_v2_gamma | 5 | 3 | 60.0% | 100.0% | 100.0% | 80.0% | 18.7 | 19.2 |

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
| baseline_prev_day_direction | low | 5 | 40.0% | - | 24.5 |
| baseline_random_walk | low | 5 | 0.0% | - | 15.6 |
| baseline_simple_technical | low | 5 | 60.0% | - | 28.1 |
| ugh_v2_alpha | low | 5 | 60.0% | 100.0% | 19.2 |
| ugh_v2_beta | low | 5 | 60.0% | 100.0% | 19.6 |
| ugh_v2_delta | low | 5 | 60.0% | 100.0% | 19.4 |
| ugh_v2_gamma | low | 5 | 60.0% | 100.0% | 18.7 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 40.0% | - | 24.5 |
| baseline_random_walk | trending | 5 | 0.0% | - | 15.6 |
| baseline_simple_technical | trending | 5 | 60.0% | - | 28.1 |
| ugh_v2_alpha | trending | 5 | 60.0% | 100.0% | 19.2 |
| ugh_v2_beta | trending | 5 | 60.0% | 100.0% | 19.6 |
| ugh_v2_delta | trending | 5 | 60.0% | 100.0% | 19.4 |
| ugh_v2_gamma | trending | 5 | 60.0% | 100.0% | 18.7 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 17.8 |
| baseline_prev_day_direction | normal | 4 | 25.0% | - | 26.1 |
| baseline_random_walk | low | 1 | 0.0% | - | 9.5 |
| baseline_random_walk | normal | 4 | 0.0% | - | 17.1 |
| baseline_simple_technical | low | 1 | 100.0% | - | 29.9 |
| baseline_simple_technical | normal | 4 | 50.0% | - | 27.7 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 15.7 |
| ugh_v2_alpha | normal | 4 | 50.0% | 100.0% | 20.1 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 15.2 |
| ugh_v2_beta | normal | 4 | 50.0% | 100.0% | 20.7 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 15.9 |
| ugh_v2_delta | normal | 4 | 50.0% | 100.0% | 20.4 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 13.8 |
| ugh_v2_gamma | normal | 4 | 50.0% | 100.0% | 19.9 |

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
