# FX Weekly Report v2 — 20260910 to 20260916

Generated: 2026-10-01T07:29:19Z
Report date (JST): 2026-09-17T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 2 | 40.0% | - | - | - | 71.7 | 85.2 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 59.4 | 56.0 |
| baseline_simple_technical | 5 | 1 | 20.0% | - | - | - | 86.3 | 94.7 |
| ugh_v2_alpha | 5 | 1 | 20.0% | 100.0% | 100.0% | 60.0% | 80.9 | 82.3 |
| ugh_v2_beta | 5 | 2 | 40.0% | 100.0% | 100.0% | 60.0% | 76.8 | 70.1 |
| ugh_v2_delta | 5 | 0 | 0.0% | 100.0% | 100.0% | 60.0% | 79.3 | 75.4 |
| ugh_v2_gamma | 5 | 1 | 20.0% | 100.0% | 100.0% | 60.0% | 80.4 | 81.7 |

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
| failure_reason | 16 | 0 | 0 | 0 | 16 | 19 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 16.6 |
| baseline_prev_day_direction | medium | 4 | 25.0% | - | 85.5 |
| baseline_random_walk | low | 1 | 0.0% | - | 47.3 |
| baseline_random_walk | medium | 4 | 0.0% | - | 62.4 |
| baseline_simple_technical | low | 1 | 0.0% | - | 93.2 |
| baseline_simple_technical | medium | 4 | 25.0% | - | 84.5 |
| ugh_v2_alpha | low | 1 | 0.0% | 100.0% | 54.5 |
| ugh_v2_alpha | medium | 4 | 25.0% | 100.0% | 87.5 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 42.2 |
| ugh_v2_beta | medium | 4 | 25.0% | 100.0% | 85.5 |
| ugh_v2_delta | low | 1 | 0.0% | 100.0% | 47.3 |
| ugh_v2_delta | medium | 4 | 0.0% | 100.0% | 87.3 |
| ugh_v2_gamma | low | 1 | 0.0% | 100.0% | 54.0 |
| ugh_v2_gamma | medium | 4 | 25.0% | 100.0% | 87.0 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 40.0% | - | 71.7 |
| baseline_random_walk | trending | 5 | 0.0% | - | 59.4 |
| baseline_simple_technical | trending | 5 | 20.0% | - | 86.3 |
| ugh_v2_alpha | trending | 5 | 20.0% | 100.0% | 80.9 |
| ugh_v2_beta | trending | 5 | 40.0% | 100.0% | 76.8 |
| ugh_v2_delta | trending | 5 | 0.0% | 100.0% | 79.3 |
| ugh_v2_gamma | trending | 5 | 20.0% | 100.0% | 80.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 5 | 40.0% | - | 71.7 |
| baseline_random_walk | normal | 5 | 0.0% | - | 59.4 |
| baseline_simple_technical | normal | 5 | 20.0% | - | 86.3 |
| ugh_v2_alpha | normal | 5 | 20.0% | 100.0% | 80.9 |
| ugh_v2_beta | normal | 5 | 40.0% | 100.0% | 76.8 |
| ugh_v2_delta | normal | 5 | 0.0% | 100.0% | 79.3 |
| ugh_v2_gamma | normal | 5 | 20.0% | 100.0% | 80.4 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 5
- **Failed**: 0
- **Skipped**: 9
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (14)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
