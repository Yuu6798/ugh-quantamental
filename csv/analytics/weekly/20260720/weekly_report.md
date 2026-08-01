# FX Weekly Report v2 — 20260713 to 20260717

Generated: 2026-08-01T04:49:32Z
Report date (JST): 2026-07-20T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 2 | 40.0% | - | - | - | 39.2 | 12.9 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 15.8 | 11.7 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | - | 24.1 | 22.2 |
| ugh_v2_alpha | 5 | 2 | 40.0% | 60.0% | 100.0% | 60.0% | 17.9 | 8.1 |
| ugh_v2_beta | 5 | 2 | 40.0% | 60.0% | 80.0% | 60.0% | 19.1 | 8.6 |
| ugh_v2_delta | 5 | 2 | 40.0% | 60.0% | 100.0% | 60.0% | 18.5 | 8.3 |
| ugh_v2_gamma | 5 | 2 | 40.0% | 60.0% | 100.0% | 60.0% | 17.7 | 8.3 |

## AI Annotation Layer

- **AI annotated**: 35
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
| regime_label | 35 | 0 | 0 | 0 | 35 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 35 |
| volatility_label | 35 | 0 | 0 | 0 | 35 | 0 |
| intervention_risk | 35 | 0 | 0 | 0 | 35 | 0 |
| failure_reason | 12 | 0 | 0 | 0 | 12 | 23 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 50.0% | - | 25.2 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 95.1 |
| baseline_random_walk | low | 4 | 0.0% | - | 6.5 |
| baseline_random_walk | medium | 1 | 0.0% | - | 53.2 |
| baseline_simple_technical | low | 4 | 75.0% | - | 22.0 |
| baseline_simple_technical | medium | 1 | 100.0% | - | 32.3 |
| ugh_v2_alpha | low | 4 | 50.0% | 75.0% | 9.0 |
| ugh_v2_alpha | medium | 1 | 0.0% | 0.0% | 53.2 |
| ugh_v2_beta | low | 4 | 50.0% | 75.0% | 10.5 |
| ugh_v2_beta | medium | 1 | 0.0% | 0.0% | 53.2 |
| ugh_v2_delta | low | 4 | 50.0% | 75.0% | 9.9 |
| ugh_v2_delta | medium | 1 | 0.0% | 0.0% | 53.2 |
| ugh_v2_gamma | low | 4 | 50.0% | 75.0% | 8.8 |
| ugh_v2_gamma | medium | 1 | 0.0% | 0.0% | 53.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 40.0% | - | 39.2 |
| baseline_random_walk | trending | 5 | 0.0% | - | 15.8 |
| baseline_simple_technical | trending | 5 | 80.0% | - | 24.1 |
| ugh_v2_alpha | trending | 5 | 40.0% | 60.0% | 17.9 |
| ugh_v2_beta | trending | 5 | 40.0% | 60.0% | 19.1 |
| ugh_v2_delta | trending | 5 | 40.0% | 60.0% | 18.5 |
| ugh_v2_gamma | trending | 5 | 40.0% | 60.0% | 17.7 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 11.7 |
| baseline_prev_day_direction | normal | 4 | 25.0% | - | 46.0 |
| baseline_random_walk | low | 1 | 0.0% | - | 0.6 |
| baseline_random_walk | normal | 4 | 0.0% | - | 19.6 |
| baseline_simple_technical | low | 1 | 100.0% | - | 20.5 |
| baseline_simple_technical | normal | 4 | 75.0% | - | 25.0 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 4.7 |
| ugh_v2_alpha | normal | 4 | 25.0% | 50.0% | 21.2 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 6.5 |
| ugh_v2_beta | normal | 4 | 25.0% | 50.0% | 22.2 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 5.7 |
| ugh_v2_delta | normal | 4 | 25.0% | 50.0% | 21.8 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 4.3 |
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
