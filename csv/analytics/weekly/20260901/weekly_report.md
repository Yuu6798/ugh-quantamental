# FX Weekly Report v2 — 20260825 to 20260831

Generated: 2026-09-06T06:06:25Z
Report date (JST): 2026-09-01T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | - | 16.6 | 2.5 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 10.8 | 8.5 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 45.0 | 47.6 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 100.0% | 100.0% | 75.0% | 11.9 | 5.9 |
| ugh_v2_beta | 4 | 3 | 75.0% | 100.0% | 100.0% | 75.0% | 11.5 | 4.5 |
| ugh_v2_delta | 4 | 3 | 75.0% | 100.0% | 100.0% | 75.0% | 11.7 | 5.2 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 100.0% | 100.0% | 75.0% | 11.4 | 5.4 |

### Event-Tag Analysis (sources: auto_only: 7, none: 21)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | month_end | 1 | 0.0% | - | 60.8 |
| baseline_random_walk | month_end | 1 | 0.0% | - | 20.0 |
| baseline_simple_technical | month_end | 1 | 0.0% | - | 45.3 |
| ugh_v2_alpha | month_end | 1 | 0.0% | 100.0% | 32.3 |
| ugh_v2_beta | month_end | 1 | 0.0% | 100.0% | 34.8 |
| ugh_v2_delta | month_end | 1 | 0.0% | 100.0% | 33.6 |
| ugh_v2_gamma | month_end | 1 | 0.0% | 100.0% | 31.2 |

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
| baseline_prev_day_direction | low | 4 | 75.0% | - | 16.6 |
| baseline_random_walk | low | 4 | 0.0% | - | 10.8 |
| baseline_simple_technical | low | 4 | 25.0% | - | 45.0 |
| ugh_v2_alpha | low | 4 | 75.0% | 100.0% | 11.9 |
| ugh_v2_beta | low | 4 | 75.0% | 100.0% | 11.5 |
| ugh_v2_delta | low | 4 | 75.0% | 100.0% | 11.7 |
| ugh_v2_gamma | low | 4 | 75.0% | 100.0% | 11.4 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 16.6 |
| baseline_random_walk | trending | 4 | 0.0% | - | 10.8 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 45.0 |
| ugh_v2_alpha | trending | 4 | 75.0% | 100.0% | 11.9 |
| ugh_v2_beta | trending | 4 | 75.0% | 100.0% | 11.5 |
| ugh_v2_delta | trending | 4 | 75.0% | 100.0% | 11.7 |
| ugh_v2_gamma | trending | 4 | 75.0% | 100.0% | 11.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 100.0% | - | 2.5 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 30.7 |
| baseline_random_walk | low | 2 | 0.0% | - | 7.5 |
| baseline_random_walk | normal | 2 | 0.0% | - | 14.1 |
| baseline_simple_technical | low | 2 | 50.0% | - | 42.5 |
| baseline_simple_technical | normal | 2 | 0.0% | - | 47.6 |
| ugh_v2_alpha | low | 2 | 100.0% | 100.0% | 5.9 |
| ugh_v2_alpha | normal | 2 | 50.0% | 100.0% | 17.9 |
| ugh_v2_beta | low | 2 | 100.0% | 100.0% | 4.5 |
| ugh_v2_beta | normal | 2 | 50.0% | 100.0% | 18.4 |
| ugh_v2_delta | low | 2 | 100.0% | 100.0% | 5.2 |
| ugh_v2_delta | normal | 2 | 50.0% | 100.0% | 18.2 |
| ugh_v2_gamma | low | 2 | 100.0% | 100.0% | 5.4 |
| ugh_v2_gamma | normal | 2 | 50.0% | 100.0% | 17.4 |

## Provider Health Summary

- **Total runs**: 13
- **Success**: 4
- **Failed**: 0
- **Skipped**: 9
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (13)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
