# FX Weekly Report v2 — 20260706 to 20260710

Generated: 2026-07-13T04:26:45Z
Report date (JST): 2026-07-13T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 36.3 | 36.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 22.2 | 21.6 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 22.7 | 23.4 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 0.0% | 50.0% | 0.0% | 25.6 | 23.6 |
| ugh_v2_beta | 4 | 2 | 50.0% | 0.0% | 75.0% | 25.0% | 27.5 | 27.3 |
| ugh_v2_delta | 4 | 3 | 75.0% | 0.0% | 75.0% | 25.0% | 26.1 | 24.9 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 0.0% | 50.0% | 0.0% | 25.5 | 23.6 |

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
| failure_reason | 5 | 0 | 0 | 0 | 5 | 23 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 36.3 |
| baseline_random_walk | low | 4 | 0.0% | - | 22.2 |
| baseline_simple_technical | low | 4 | 75.0% | - | 22.7 |
| ugh_v2_alpha | low | 4 | 75.0% | 0.0% | 25.6 |
| ugh_v2_beta | low | 4 | 50.0% | 0.0% | 27.5 |
| ugh_v2_delta | low | 4 | 75.0% | 0.0% | 26.1 |
| ugh_v2_gamma | low | 4 | 75.0% | 0.0% | 25.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 36.3 |
| baseline_random_walk | trending | 4 | 0.0% | - | 22.2 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 22.7 |
| ugh_v2_alpha | trending | 4 | 75.0% | 0.0% | 25.6 |
| ugh_v2_beta | trending | 4 | 50.0% | 0.0% | 27.5 |
| ugh_v2_delta | trending | 4 | 75.0% | 0.0% | 26.1 |
| ugh_v2_gamma | trending | 4 | 75.0% | 0.0% | 25.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 50.0% | - | 43.9 |
| baseline_prev_day_direction | normal | 2 | 100.0% | - | 28.7 |
| baseline_random_walk | low | 2 | 0.0% | - | 6.8 |
| baseline_random_walk | normal | 2 | 0.0% | - | 37.7 |
| baseline_simple_technical | low | 2 | 50.0% | - | 27.0 |
| baseline_simple_technical | normal | 2 | 100.0% | - | 18.4 |
| ugh_v2_alpha | low | 2 | 50.0% | 0.0% | 19.5 |
| ugh_v2_alpha | normal | 2 | 100.0% | 0.0% | 31.6 |
| ugh_v2_beta | low | 2 | 50.0% | 0.0% | 23.1 |
| ugh_v2_beta | normal | 2 | 50.0% | 0.0% | 31.8 |
| ugh_v2_delta | low | 2 | 50.0% | 0.0% | 21.4 |
| ugh_v2_delta | normal | 2 | 100.0% | 0.0% | 30.7 |
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
