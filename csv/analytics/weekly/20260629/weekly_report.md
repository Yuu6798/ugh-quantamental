# FX Weekly Report v2 — 20260622 to 20260626

Generated: 2026-06-29T05:25:19Z
Report date (JST): 2026-06-29T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 17.2 | 15.8 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 9.9 | 10.2 |
| baseline_simple_technical | 4 | 4 | 100.0% | - | - | - | 8.0 | 8.0 |
| ugh_v2_alpha | 4 | 4 | 100.0% | 75.0% | 0.0% | - | 9.8 | 9.9 |
| ugh_v2_beta | 4 | 3 | 75.0% | 50.0% | 0.0% | - | 11.4 | 10.8 |
| ugh_v2_delta | 4 | 3 | 75.0% | 50.0% | 0.0% | - | 11.0 | 10.4 |
| ugh_v2_gamma | 4 | 4 | 100.0% | 75.0% | 0.0% | - | 9.7 | 9.8 |

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
| failure_reason | 2 | 0 | 0 | 0 | 2 | 26 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 17.2 |
| baseline_random_walk | low | 4 | 0.0% | - | 9.9 |
| baseline_simple_technical | low | 4 | 100.0% | - | 8.0 |
| ugh_v2_alpha | low | 4 | 100.0% | 75.0% | 9.8 |
| ugh_v2_beta | low | 4 | 75.0% | 50.0% | 11.4 |
| ugh_v2_delta | low | 4 | 75.0% | 50.0% | 11.0 |
| ugh_v2_gamma | low | 4 | 100.0% | 75.0% | 9.7 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 17.2 |
| baseline_random_walk | trending | 4 | 0.0% | - | 9.9 |
| baseline_simple_technical | trending | 4 | 100.0% | - | 8.0 |
| ugh_v2_alpha | trending | 4 | 100.0% | 75.0% | 9.8 |
| ugh_v2_beta | trending | 4 | 75.0% | 50.0% | 11.4 |
| ugh_v2_delta | trending | 4 | 75.0% | 50.0% | 11.0 |
| ugh_v2_gamma | trending | 4 | 100.0% | 75.0% | 9.7 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 100.0% | - | 15.8 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 18.6 |
| baseline_random_walk | low | 2 | 0.0% | - | 9.6 |
| baseline_random_walk | normal | 2 | 0.0% | - | 10.2 |
| baseline_simple_technical | low | 2 | 100.0% | - | 8.4 |
| baseline_simple_technical | normal | 2 | 100.0% | - | 7.5 |
| ugh_v2_alpha | low | 2 | 100.0% | 50.0% | 9.9 |
| ugh_v2_alpha | normal | 2 | 100.0% | 100.0% | 9.7 |
| ugh_v2_beta | low | 2 | 100.0% | 50.0% | 10.8 |
| ugh_v2_beta | normal | 2 | 50.0% | 50.0% | 11.9 |
| ugh_v2_delta | low | 2 | 100.0% | 50.0% | 10.4 |
| ugh_v2_delta | normal | 2 | 50.0% | 50.0% | 11.7 |
| ugh_v2_gamma | low | 2 | 100.0% | 50.0% | 9.8 |
| ugh_v2_gamma | normal | 2 | 100.0% | 100.0% | 9.6 |

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
