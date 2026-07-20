# FX Weekly Report v2 — 20260713 to 20260717

Generated: 2026-07-20T04:31:33Z
Report date (JST): 2026-07-20T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | - | 46.0 | 38.9 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 19.6 | 12.0 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | - | 25.0 | 27.2 |
| ugh_v2_alpha | 4 | 1 | 25.0% | 50.0% | 100.0% | 75.0% | 21.2 | 15.1 |
| ugh_v2_beta | 4 | 1 | 25.0% | 50.0% | 75.0% | 75.0% | 22.2 | 17.2 |
| ugh_v2_delta | 4 | 1 | 25.0% | 50.0% | 100.0% | 75.0% | 21.8 | 16.3 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 50.0% | 100.0% | 75.0% | 21.1 | 14.9 |

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
| baseline_prev_day_direction | low | 3 | 33.3% | - | 29.6 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 95.1 |
| baseline_random_walk | low | 3 | 0.0% | - | 8.4 |
| baseline_random_walk | medium | 1 | 0.0% | - | 53.2 |
| baseline_simple_technical | low | 3 | 66.7% | - | 22.5 |
| baseline_simple_technical | medium | 1 | 100.0% | - | 32.3 |
| ugh_v2_alpha | low | 3 | 33.3% | 66.7% | 10.5 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 53.2 |
| ugh_v2_beta | low | 3 | 33.3% | 66.7% | 11.9 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 53.2 |
| ugh_v2_delta | low | 3 | 33.3% | 66.7% | 11.3 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 53.2 |
| ugh_v2_gamma | low | 3 | 33.3% | 66.7% | 10.3 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 53.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 25.0% | - | 46.0 |
| baseline_random_walk | trending | 4 | 0.0% | - | 19.6 |
| baseline_simple_technical | trending | 4 | 75.0% | - | 25.0 |
| ugh_v2_alpha | trending | 4 | 25.0% | 50.0% | 21.2 |
| ugh_v2_beta | trending | 4 | 25.0% | 50.0% | 22.2 |
| ugh_v2_delta | trending | 4 | 25.0% | 50.0% | 21.8 |
| ugh_v2_gamma | trending | 4 | 25.0% | 50.0% | 21.1 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 4 | 25.0% | - | 46.0 |
| baseline_random_walk | normal | 4 | 0.0% | - | 19.6 |
| baseline_simple_technical | normal | 4 | 75.0% | - | 25.0 |
| ugh_v2_alpha | normal | 4 | 25.0% | 50.0% | 21.2 |
| ugh_v2_beta | normal | 4 | 25.0% | 50.0% | 22.2 |
| ugh_v2_delta | normal | 4 | 25.0% | 50.0% | 21.8 |
| ugh_v2_gamma | normal | 4 | 25.0% | 50.0% | 21.1 |

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
