# FX Weekly Report v2 — 20260831 to 20260904

Generated: 2026-09-07T05:31:25Z
Report date (JST): 2026-09-07T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | - | 79.3 | 75.9 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 79.9 | 59.0 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 93.7 | 80.8 |
| ugh_v2_alpha | 4 | 1 | 25.0% | 50.0% | 100.0% | 25.0% | 85.2 | 68.2 |
| ugh_v2_beta | 4 | 1 | 25.0% | 50.0% | 75.0% | 25.0% | 86.4 | 71.0 |
| ugh_v2_delta | 4 | 0 | 0.0% | 50.0% | 100.0% | 25.0% | 87.1 | 69.6 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 50.0% | 100.0% | 25.0% | 84.7 | 67.1 |

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
| failure_reason | 13 | 0 | 0 | 0 | 13 | 15 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 100.0% | - | 91.0 |
| baseline_prev_day_direction | low | 2 | 0.0% | - | 54.2 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 118.1 |
| baseline_random_walk | high | 1 | 0.0% | - | 181.5 |
| baseline_random_walk | low | 2 | 0.0% | - | 23.8 |
| baseline_random_walk | medium | 1 | 0.0% | - | 90.5 |
| baseline_simple_technical | high | 1 | 0.0% | - | 211.7 |
| baseline_simple_technical | low | 2 | 50.0% | - | 23.4 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 116.3 |
| ugh_v2_alpha | high | 1 | 0.0% | 0.0% | 181.5 |
| ugh_v2_alpha | low | 2 | 50.0% | 100.0% | 27.5 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 104.1 |
| ugh_v2_beta | high | 1 | 100.0% | 0.0% | 176.1 |
| ugh_v2_beta | low | 2 | 0.0% | 100.0% | 31.2 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 107.1 |
| ugh_v2_delta | high | 1 | 0.0% | 0.0% | 181.5 |
| ugh_v2_delta | low | 2 | 0.0% | 100.0% | 30.6 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 105.7 |
| ugh_v2_gamma | high | 1 | 0.0% | 0.0% | 181.5 |
| ugh_v2_gamma | low | 2 | 50.0% | 100.0% | 27.1 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 103.0 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 25.0% | - | 79.3 |
| baseline_random_walk | trending | 4 | 0.0% | - | 79.9 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 93.7 |
| ugh_v2_alpha | trending | 4 | 25.0% | 50.0% | 85.2 |
| ugh_v2_beta | trending | 4 | 25.0% | 50.0% | 86.4 |
| ugh_v2_delta | trending | 4 | 0.0% | 50.0% | 87.1 |
| ugh_v2_gamma | trending | 4 | 25.0% | 50.0% | 84.7 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 104.5 |
| baseline_prev_day_direction | normal | 2 | 0.0% | - | 54.2 |
| baseline_random_walk | high | 2 | 0.0% | - | 136.0 |
| baseline_random_walk | normal | 2 | 0.0% | - | 23.8 |
| baseline_simple_technical | high | 2 | 0.0% | - | 164.0 |
| baseline_simple_technical | normal | 2 | 50.0% | - | 23.4 |
| ugh_v2_alpha | high | 2 | 0.0% | 0.0% | 142.8 |
| ugh_v2_alpha | normal | 2 | 50.0% | 100.0% | 27.5 |
| ugh_v2_beta | high | 2 | 50.0% | 0.0% | 141.6 |
| ugh_v2_beta | normal | 2 | 0.0% | 100.0% | 31.2 |
| ugh_v2_delta | high | 2 | 0.0% | 0.0% | 143.6 |
| ugh_v2_delta | normal | 2 | 0.0% | 100.0% | 30.6 |
| ugh_v2_gamma | high | 2 | 0.0% | 0.0% | 142.3 |
| ugh_v2_gamma | normal | 2 | 50.0% | 100.0% | 27.1 |

## Provider Health Summary

- **Total runs**: 17
- **Success**: 5
- **Failed**: 0
- **Skipped**: 12
- **Fallback adjustments**: 3
- **Lag occurrences**: 3
- **Providers used**: alpha_vantage (17)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
