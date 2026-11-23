# FX Weekly Report v2 — 20261116 to 20261120

Generated: 2026-11-23T08:28:06Z
Report date (JST): 2026-11-23T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 9.6 | 6.0 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 10.5 | 9.4 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 28.0 | 31.4 |
| ugh_v2_alpha | 4 | 1 | 25.0% | 100.0% | 100.0% | 100.0% | 13.4 | 11.7 |
| ugh_v2_beta | 4 | 1 | 25.0% | 100.0% | 100.0% | 100.0% | 11.4 | 11.1 |
| ugh_v2_delta | 4 | 1 | 25.0% | 100.0% | 100.0% | 100.0% | 12.5 | 11.4 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 100.0% | 100.0% | 100.0% | 13.3 | 11.8 |

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
| failure_reason | 12 | 0 | 0 | 0 | 12 | 16 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 9.6 |
| baseline_random_walk | low | 4 | 0.0% | - | 10.5 |
| baseline_simple_technical | low | 4 | 25.0% | - | 28.0 |
| ugh_v2_alpha | low | 4 | 25.0% | 100.0% | 13.4 |
| ugh_v2_beta | low | 4 | 25.0% | 100.0% | 11.4 |
| ugh_v2_delta | low | 4 | 25.0% | 100.0% | 12.5 |
| ugh_v2_gamma | low | 4 | 25.0% | 100.0% | 13.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 9.6 |
| baseline_random_walk | trending | 4 | 0.0% | - | 10.5 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 28.0 |
| ugh_v2_alpha | trending | 4 | 25.0% | 100.0% | 13.4 |
| ugh_v2_beta | trending | 4 | 25.0% | 100.0% | 11.4 |
| ugh_v2_delta | trending | 4 | 25.0% | 100.0% | 12.5 |
| ugh_v2_gamma | trending | 4 | 25.0% | 100.0% | 13.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 4 | 75.0% | - | 9.6 |
| baseline_random_walk | normal | 4 | 0.0% | - | 10.5 |
| baseline_simple_technical | normal | 4 | 25.0% | - | 28.0 |
| ugh_v2_alpha | normal | 4 | 25.0% | 100.0% | 13.4 |
| ugh_v2_beta | normal | 4 | 25.0% | 100.0% | 11.4 |
| ugh_v2_delta | normal | 4 | 25.0% | 100.0% | 12.5 |
| ugh_v2_gamma | normal | 4 | 25.0% | 100.0% | 13.3 |

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
