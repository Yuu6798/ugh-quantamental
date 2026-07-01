# FX Weekly Report v2 — 20260624 to 20260630

Generated: 2026-07-01T06:01:16Z
Report date (JST): 2026-07-01T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 13.3 | 15.8 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 9.1 | 8.7 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 8.6 | 8.4 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 75.0% | 50.0% | 0.0% | 9.5 | 9.2 |
| ugh_v2_beta | 4 | 3 | 75.0% | 50.0% | 50.0% | 0.0% | 10.1 | 10.3 |
| ugh_v2_delta | 4 | 3 | 75.0% | 75.0% | 50.0% | 0.0% | 9.8 | 9.7 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 75.0% | 50.0% | 0.0% | 9.5 | 9.2 |

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
| baseline_prev_day_direction | low | 4 | 50.0% | - | 13.3 |
| baseline_random_walk | low | 4 | 0.0% | - | 9.1 |
| baseline_simple_technical | low | 4 | 75.0% | - | 8.6 |
| ugh_v2_alpha | low | 4 | 75.0% | 75.0% | 9.5 |
| ugh_v2_beta | low | 4 | 75.0% | 50.0% | 10.1 |
| ugh_v2_delta | low | 4 | 75.0% | 75.0% | 9.8 |
| ugh_v2_gamma | low | 4 | 75.0% | 75.0% | 9.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 13.3 |
| baseline_random_walk | trending | 4 | 0.0% | - | 9.1 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 8.6 |
| ugh_v2_alpha | trending | 4 | 75.0% | 75.0% | 9.5 |
| ugh_v2_beta | trending | 4 | 75.0% | 50.0% | 10.1 |
| ugh_v2_delta | trending | 4 | 75.0% | 75.0% | 9.8 |
| ugh_v2_gamma | trending | 4 | 75.0% | 75.0% | 9.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 16.3 |
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 4.3 |
| baseline_random_walk | low | 3 | 0.0% | - | 11.1 |
| baseline_random_walk | normal | 1 | 0.0% | - | 3.1 |
| baseline_simple_technical | low | 3 | 100.0% | - | 5.8 |
| baseline_simple_technical | normal | 1 | 0.0% | - | 16.6 |
| ugh_v2_alpha | low | 3 | 100.0% | 66.7% | 9.7 |
| ugh_v2_alpha | normal | 1 | 0.0% | 100.0% | 9.1 |
| ugh_v2_beta | low | 3 | 100.0% | 33.3% | 10.9 |
| ugh_v2_beta | normal | 1 | 0.0% | 100.0% | 7.7 |
| ugh_v2_delta | low | 3 | 100.0% | 66.7% | 10.4 |
| ugh_v2_delta | normal | 1 | 0.0% | 100.0% | 8.3 |
| ugh_v2_gamma | low | 3 | 100.0% | 66.7% | 9.7 |
| ugh_v2_gamma | normal | 1 | 0.0% | 100.0% | 8.8 |

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
