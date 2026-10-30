# FX Weekly Report v2 — 20261026 to 20261030

Generated: 2026-10-30T17:03:32Z
Report date (JST): 2026-10-31T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 22.1 | 24.9 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 21.0 | 17.1 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | - | 35.5 | 32.0 |
| ugh_v2_alpha | 4 | 1 | 25.0% | 100.0% | 100.0% | 50.0% | 20.1 | 16.5 |
| ugh_v2_beta | 4 | 2 | 50.0% | 100.0% | 100.0% | 50.0% | 19.9 | 16.0 |
| ugh_v2_delta | 4 | 2 | 50.0% | 100.0% | 100.0% | 50.0% | 19.2 | 14.8 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 100.0% | 100.0% | 50.0% | 20.2 | 16.5 |

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
| failure_reason | 10 | 0 | 0 | 0 | 10 | 18 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 22.1 |
| baseline_random_walk | low | 4 | 0.0% | - | 21.0 |
| baseline_simple_technical | low | 4 | 50.0% | - | 35.5 |
| ugh_v2_alpha | low | 4 | 25.0% | 100.0% | 20.1 |
| ugh_v2_beta | low | 4 | 50.0% | 100.0% | 19.9 |
| ugh_v2_delta | low | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_gamma | low | 4 | 25.0% | 100.0% | 20.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 22.1 |
| baseline_random_walk | trending | 4 | 0.0% | - | 21.0 |
| baseline_simple_technical | trending | 4 | 50.0% | - | 35.5 |
| ugh_v2_alpha | trending | 4 | 25.0% | 100.0% | 20.1 |
| ugh_v2_beta | trending | 4 | 50.0% | 100.0% | 19.9 |
| ugh_v2_delta | trending | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_gamma | trending | 4 | 25.0% | 100.0% | 20.2 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 16.7 |
| baseline_prev_day_direction | normal | 3 | 66.7% | - | 24.0 |
| baseline_random_walk | low | 1 | 0.0% | - | 27.3 |
| baseline_random_walk | normal | 3 | 0.0% | - | 18.9 |
| baseline_simple_technical | low | 1 | 0.0% | - | 48.0 |
| baseline_simple_technical | normal | 3 | 66.7% | - | 31.3 |
| ugh_v2_alpha | low | 1 | 0.0% | 100.0% | 27.3 |
| ugh_v2_alpha | normal | 3 | 33.3% | 100.0% | 17.8 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 22.3 |
| ugh_v2_beta | normal | 3 | 33.3% | 100.0% | 19.1 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 23.9 |
| ugh_v2_delta | normal | 3 | 33.3% | 100.0% | 17.7 |
| ugh_v2_gamma | low | 1 | 0.0% | 100.0% | 27.3 |
| ugh_v2_gamma | normal | 3 | 33.3% | 100.0% | 17.8 |

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
