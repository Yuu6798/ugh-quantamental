# FX Weekly Report v2 — 20260803 to 20260807

Generated: 2026-08-10T03:07:40Z
Report date (JST): 2026-08-10T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | - | 58.7 | 41.9 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 21.0 | 19.7 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | - | 52.1 | 50.8 |
| ugh_v2_alpha | 4 | 2 | 50.0% | 100.0% | 100.0% | 0.0% | 33.3 | 35.0 |
| ugh_v2_beta | 4 | 1 | 25.0% | 100.0% | 100.0% | 0.0% | 30.1 | 33.8 |
| ugh_v2_delta | 4 | 1 | 25.0% | 100.0% | 100.0% | 0.0% | 31.0 | 34.0 |
| ugh_v2_gamma | 4 | 2 | 50.0% | 100.0% | 100.0% | 0.0% | 33.3 | 35.0 |

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
| baseline_prev_day_direction | low | 4 | 25.0% | - | 58.7 |
| baseline_random_walk | low | 4 | 0.0% | - | 21.0 |
| baseline_simple_technical | low | 4 | 50.0% | - | 52.1 |
| ugh_v2_alpha | low | 4 | 50.0% | 100.0% | 33.3 |
| ugh_v2_beta | low | 4 | 25.0% | 100.0% | 30.1 |
| ugh_v2_delta | low | 4 | 25.0% | 100.0% | 31.0 |
| ugh_v2_gamma | low | 4 | 50.0% | 100.0% | 33.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 25.0% | - | 58.7 |
| baseline_random_walk | trending | 4 | 0.0% | - | 21.0 |
| baseline_simple_technical | trending | 4 | 50.0% | - | 52.1 |
| ugh_v2_alpha | trending | 4 | 50.0% | 100.0% | 33.3 |
| ugh_v2_beta | trending | 4 | 25.0% | 100.0% | 30.1 |
| ugh_v2_delta | trending | 4 | 25.0% | 100.0% | 31.0 |
| ugh_v2_gamma | trending | 4 | 50.0% | 100.0% | 33.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 0.0% | - | 40.0 |
| baseline_prev_day_direction | normal | 1 | 100.0% | - | 114.7 |
| baseline_random_walk | low | 3 | 0.0% | - | 26.5 |
| baseline_random_walk | normal | 1 | 0.0% | - | 4.5 |
| baseline_simple_technical | low | 3 | 33.3% | - | 59.3 |
| baseline_simple_technical | normal | 1 | 100.0% | - | 30.6 |
| ugh_v2_alpha | low | 3 | 33.3% | 100.0% | 38.4 |
| ugh_v2_alpha | normal | 1 | 100.0% | 100.0% | 18.1 |
| ugh_v2_beta | low | 3 | 0.0% | 100.0% | 33.0 |
| ugh_v2_beta | normal | 1 | 100.0% | 100.0% | 21.6 |
| ugh_v2_delta | low | 3 | 0.0% | 100.0% | 34.9 |
| ugh_v2_delta | normal | 1 | 100.0% | 100.0% | 19.4 |
| ugh_v2_gamma | low | 3 | 33.3% | 100.0% | 38.4 |
| ugh_v2_gamma | normal | 1 | 100.0% | 100.0% | 17.9 |

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
