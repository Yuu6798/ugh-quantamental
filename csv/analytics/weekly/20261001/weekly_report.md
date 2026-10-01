# FX Weekly Report v2 — 20260924 to 20260930

Generated: 2026-10-01T07:29:19Z
Report date (JST): 2026-10-01T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | - | 67.2 | 62.8 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 35.8 | 21.2 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | - | 58.4 | 36.0 |
| ugh_v2_alpha | 4 | 2 | 50.0% | 100.0% | 25.0% | 25.0% | 44.8 | 12.8 |
| ugh_v2_beta | 4 | 2 | 50.0% | 100.0% | 25.0% | 25.0% | 39.8 | 6.2 |
| ugh_v2_delta | 4 | 2 | 50.0% | 100.0% | 25.0% | 25.0% | 42.0 | 8.8 |
| ugh_v2_gamma | 4 | 2 | 50.0% | 100.0% | 25.0% | 25.0% | 44.4 | 13.3 |

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
| failure_reason | 8 | 0 | 0 | 0 | 8 | 20 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 33.3% | - | 44.8 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 134.2 |
| baseline_random_walk | low | 3 | 0.0% | - | 14.5 |
| baseline_random_walk | medium | 1 | 0.0% | - | 99.5 |
| baseline_simple_technical | low | 3 | 66.7% | - | 27.0 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 152.7 |
| ugh_v2_alpha | low | 3 | 66.7% | 100.0% | 11.1 |
| ugh_v2_alpha | medium | 1 | 0.0% | 100.0% | 145.9 |
| ugh_v2_beta | low | 3 | 66.7% | 100.0% | 5.5 |
| ugh_v2_beta | medium | 1 | 0.0% | 100.0% | 142.5 |
| ugh_v2_delta | low | 3 | 66.7% | 100.0% | 8.2 |
| ugh_v2_delta | medium | 1 | 0.0% | 100.0% | 143.4 |
| ugh_v2_gamma | low | 3 | 66.7% | 100.0% | 11.4 |
| ugh_v2_gamma | medium | 1 | 0.0% | 100.0% | 143.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 25.0% | - | 67.2 |
| baseline_random_walk | trending | 4 | 0.0% | - | 35.8 |
| baseline_simple_technical | trending | 4 | 50.0% | - | 58.4 |
| ugh_v2_alpha | trending | 4 | 50.0% | 100.0% | 44.8 |
| ugh_v2_beta | trending | 4 | 50.0% | 100.0% | 39.8 |
| ugh_v2_delta | trending | 4 | 50.0% | 100.0% | 42.0 |
| ugh_v2_gamma | trending | 4 | 50.0% | 100.0% | 44.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 134.2 |
| baseline_prev_day_direction | low | 1 | 0.0% | - | 8.8 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 62.8 |
| baseline_random_walk | high | 1 | 0.0% | - | 99.5 |
| baseline_random_walk | low | 1 | 0.0% | - | 7.6 |
| baseline_random_walk | normal | 2 | 0.0% | - | 17.9 |
| baseline_simple_technical | high | 1 | 0.0% | - | 152.7 |
| baseline_simple_technical | low | 1 | 0.0% | - | 8.8 |
| baseline_simple_technical | normal | 2 | 100.0% | - | 36.0 |
| ugh_v2_alpha | high | 1 | 0.0% | 100.0% | 145.9 |
| ugh_v2_alpha | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_alpha | normal | 2 | 100.0% | 100.0% | 12.8 |
| ugh_v2_beta | high | 1 | 0.0% | 100.0% | 142.5 |
| ugh_v2_beta | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_beta | normal | 2 | 100.0% | 100.0% | 4.5 |
| ugh_v2_delta | high | 1 | 0.0% | 100.0% | 143.4 |
| ugh_v2_delta | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_delta | normal | 2 | 100.0% | 100.0% | 8.4 |
| ugh_v2_gamma | high | 1 | 0.0% | 100.0% | 143.5 |
| ugh_v2_gamma | low | 1 | 0.0% | 100.0% | 7.6 |
| ugh_v2_gamma | normal | 2 | 100.0% | 100.0% | 13.3 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 5
- **Lag occurrences**: 5
- **Providers used**: alpha_vantage (14), yahoo_finance (1)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
