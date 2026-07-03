# FX Weekly Report v2 — 20260629 to 20260703

Generated: 2026-07-03T12:52:39Z
Report date (JST): 2026-07-04T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 42.8 | 29.3 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 36.8 | 25.9 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 36.0 | 18.2 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 50.0% | 25.0% | 0.0% | 36.0 | 18.2 |
| ugh_v2_beta | 4 | 3 | 75.0% | 0.0% | 25.0% | 0.0% | 36.1 | 18.5 |
| ugh_v2_delta | 4 | 3 | 75.0% | 25.0% | 25.0% | 0.0% | 36.1 | 18.4 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 50.0% | 50.0% | 0.0% | 36.0 | 18.8 |

### Event-Tag Analysis (sources: auto_only: 7, none: 21)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | month_end | 1 | 100.0% | - | 23.4 |
| baseline_prev_day_direction | quarter_end | 1 | 100.0% | - | 23.4 |
| baseline_random_walk | month_end | 1 | 0.0% | - | 37.7 |
| baseline_random_walk | quarter_end | 1 | 0.0% | - | 37.7 |
| baseline_simple_technical | month_end | 1 | 100.0% | - | 24.5 |
| baseline_simple_technical | quarter_end | 1 | 100.0% | - | 24.5 |
| ugh_v2_alpha | month_end | 1 | 100.0% | 0.0% | 27.2 |
| ugh_v2_alpha | quarter_end | 1 | 100.0% | 0.0% | 27.2 |
| ugh_v2_beta | month_end | 1 | 100.0% | 0.0% | 25.9 |
| ugh_v2_beta | quarter_end | 1 | 100.0% | 0.0% | 25.9 |
| ugh_v2_delta | month_end | 1 | 100.0% | 0.0% | 26.5 |
| ugh_v2_delta | quarter_end | 1 | 100.0% | 0.0% | 26.5 |
| ugh_v2_gamma | month_end | 1 | 100.0% | 0.0% | 28.0 |
| ugh_v2_gamma | quarter_end | 1 | 100.0% | 0.0% | 28.0 |

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
| event_tags | 0 | 7 | 0 | 0 | 7 | 21 |
| volatility_label | 28 | 0 | 0 | 0 | 28 | 0 |
| intervention_risk | 28 | 0 | 0 | 0 | 28 | 0 |
| failure_reason | 4 | 0 | 0 | 0 | 4 | 24 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 25.3 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 95.3 |
| baseline_random_walk | low | 3 | 0.0% | - | 18.1 |
| baseline_random_walk | medium | 1 | 0.0% | - | 92.9 |
| baseline_simple_technical | low | 3 | 100.0% | - | 12.3 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 106.9 |
| ugh_v2_alpha | low | 3 | 100.0% | 66.7% | 15.1 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 98.8 |
| ugh_v2_beta | low | 3 | 100.0% | 0.0% | 15.6 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 97.7 |
| ugh_v2_delta | low | 3 | 100.0% | 33.3% | 15.4 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 98.2 |
| ugh_v2_gamma | low | 3 | 100.0% | 66.7% | 15.2 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 98.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 42.8 |
| baseline_random_walk | trending | 4 | 0.0% | - | 36.8 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 36.0 |
| ugh_v2_alpha | trending | 4 | 75.0% | 50.0% | 36.0 |
| ugh_v2_beta | trending | 4 | 75.0% | 0.0% | 36.1 |
| ugh_v2_delta | trending | 4 | 75.0% | 25.0% | 36.1 |
| ugh_v2_gamma | trending | 4 | 75.0% | 50.0% | 36.0 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 59.4 |
| baseline_prev_day_direction | low | 1 | 0.0% | - | 17.3 |
| baseline_prev_day_direction | normal | 1 | 100.0% | - | 35.2 |
| baseline_random_walk | high | 2 | 0.0% | - | 65.3 |
| baseline_random_walk | low | 1 | 0.0% | - | 14.2 |
| baseline_random_walk | normal | 1 | 0.0% | - | 2.5 |
| baseline_simple_technical | high | 2 | 50.0% | - | 65.7 |
| baseline_simple_technical | low | 1 | 100.0% | - | 0.7 |
| baseline_simple_technical | normal | 1 | 100.0% | - | 11.8 |
| ugh_v2_alpha | high | 2 | 50.0% | 0.0% | 63.0 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 9.3 |
| ugh_v2_alpha | normal | 1 | 100.0% | 100.0% | 8.8 |
| ugh_v2_beta | high | 2 | 50.0% | 0.0% | 61.8 |
| ugh_v2_beta | low | 1 | 100.0% | 0.0% | 11.1 |
| ugh_v2_beta | normal | 1 | 100.0% | 0.0% | 9.8 |
| ugh_v2_delta | high | 2 | 50.0% | 0.0% | 62.4 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 10.3 |
| ugh_v2_delta | normal | 1 | 100.0% | 0.0% | 9.3 |
| ugh_v2_gamma | high | 2 | 50.0% | 0.0% | 63.3 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 9.6 |
| ugh_v2_gamma | normal | 1 | 100.0% | 100.0% | 7.9 |

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
