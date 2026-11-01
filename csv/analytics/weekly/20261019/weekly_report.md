# FX Weekly Report v2 — 20261012 to 20261016

Generated: 2026-11-01T07:49:47Z
Report date (JST): 2026-10-19T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | - | 22.0 | 18.3 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 14.9 | 19.6 |
| baseline_simple_technical | 5 | 2 | 40.0% | - | - | - | 32.3 | 33.1 |
| ugh_v2_alpha | 5 | 1 | 20.0% | 100.0% | 100.0% | 80.0% | 16.3 | 15.8 |
| ugh_v2_beta | 5 | 1 | 20.0% | 100.0% | 100.0% | 80.0% | 15.3 | 13.3 |
| ugh_v2_delta | 5 | 1 | 20.0% | 100.0% | 100.0% | 80.0% | 15.4 | 14.2 |
| ugh_v2_gamma | 5 | 1 | 20.0% | 100.0% | 100.0% | 80.0% | 16.3 | 17.1 |

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
| failure_reason | 16 | 0 | 0 | 0 | 16 | 19 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 60.0% | - | 22.0 |
| baseline_random_walk | low | 5 | 0.0% | - | 14.9 |
| baseline_simple_technical | low | 5 | 40.0% | - | 32.3 |
| ugh_v2_alpha | low | 5 | 20.0% | 100.0% | 16.3 |
| ugh_v2_beta | low | 5 | 20.0% | 100.0% | 15.3 |
| ugh_v2_delta | low | 5 | 20.0% | 100.0% | 15.4 |
| ugh_v2_gamma | low | 5 | 20.0% | 100.0% | 16.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 60.0% | - | 22.0 |
| baseline_random_walk | trending | 5 | 0.0% | - | 14.9 |
| baseline_simple_technical | trending | 5 | 40.0% | - | 32.3 |
| ugh_v2_alpha | trending | 5 | 20.0% | 100.0% | 16.3 |
| ugh_v2_beta | trending | 5 | 20.0% | 100.0% | 15.3 |
| ugh_v2_delta | trending | 5 | 20.0% | 100.0% | 15.4 |
| ugh_v2_gamma | trending | 5 | 20.0% | 100.0% | 16.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 5 | 60.0% | - | 22.0 |
| baseline_random_walk | normal | 5 | 0.0% | - | 14.9 |
| baseline_simple_technical | normal | 5 | 40.0% | - | 32.3 |
| ugh_v2_alpha | normal | 5 | 20.0% | 100.0% | 16.3 |
| ugh_v2_beta | normal | 5 | 20.0% | 100.0% | 15.3 |
| ugh_v2_delta | normal | 5 | 20.0% | 100.0% | 15.4 |
| ugh_v2_gamma | normal | 5 | 20.0% | 100.0% | 16.3 |

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
