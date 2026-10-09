# FX Weekly Report v2 — 20261005 to 20261009

Generated: 2026-10-09T17:28:46Z
Report date (JST): 2026-10-10T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 20.8 | 14.6 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 12.4 | 10.1 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | - | 33.5 | 35.2 |
| ugh_v2_alpha | 4 | 2 | 50.0% | 100.0% | 100.0% | 100.0% | 19.3 | 18.8 |
| ugh_v2_beta | 4 | 2 | 50.0% | 100.0% | 100.0% | 100.0% | 18.8 | 19.5 |
| ugh_v2_delta | 4 | 2 | 50.0% | 100.0% | 100.0% | 100.0% | 19.2 | 18.8 |
| ugh_v2_gamma | 4 | 2 | 50.0% | 100.0% | 100.0% | 100.0% | 18.5 | 18.1 |

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
| baseline_prev_day_direction | low | 4 | 50.0% | - | 20.8 |
| baseline_random_walk | low | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | low | 4 | 50.0% | - | 33.5 |
| ugh_v2_alpha | low | 4 | 50.0% | 100.0% | 19.3 |
| ugh_v2_beta | low | 4 | 50.0% | 100.0% | 18.8 |
| ugh_v2_delta | low | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_gamma | low | 4 | 50.0% | 100.0% | 18.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 20.8 |
| baseline_random_walk | trending | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | trending | 4 | 50.0% | - | 33.5 |
| ugh_v2_alpha | trending | 4 | 50.0% | 100.0% | 19.3 |
| ugh_v2_beta | trending | 4 | 50.0% | 100.0% | 18.8 |
| ugh_v2_delta | trending | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_gamma | trending | 4 | 50.0% | 100.0% | 18.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 17.8 |
| baseline_prev_day_direction | normal | 3 | 33.3% | - | 21.8 |
| baseline_random_walk | low | 1 | 0.0% | - | 9.5 |
| baseline_random_walk | normal | 3 | 0.0% | - | 13.3 |
| baseline_simple_technical | low | 1 | 100.0% | - | 29.9 |
| baseline_simple_technical | normal | 3 | 33.3% | - | 34.7 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 15.7 |
| ugh_v2_alpha | normal | 3 | 33.3% | 100.0% | 20.6 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 15.2 |
| ugh_v2_beta | normal | 3 | 33.3% | 100.0% | 20.0 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 15.9 |
| ugh_v2_delta | normal | 3 | 33.3% | 100.0% | 20.3 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 13.8 |
| ugh_v2_gamma | normal | 3 | 33.3% | 100.0% | 20.1 |

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
