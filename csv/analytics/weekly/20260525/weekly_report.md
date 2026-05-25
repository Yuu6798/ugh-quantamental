# FX Weekly Report v2 — 20260518 to 20260522

Generated: 2026-05-25T05:15:49Z
Report date (JST): 2026-05-25T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | 12.0 | 9.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 12.4 | 12.3 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 41.5 | 40.9 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 100.0% | 100.0% | 12.3 | 10.3 |
| ugh_v2_beta | 4 | 3 | 75.0% | 100.0% | 100.0% | 10.2 | 7.2 |
| ugh_v2_delta | 4 | 3 | 75.0% | 100.0% | 100.0% | 11.2 | 8.6 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 100.0% | 100.0% | 12.1 | 10.5 |

## AI Annotation Layer

- **AI annotated**: 28
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 28 | 0 | 0 | 28 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 28 |
| volatility_label | 28 | 0 | 0 | 28 | 0 |
| intervention_risk | 28 | 0 | 0 | 28 | 0 |
| failure_reason | 4 | 0 | 0 | 4 | 24 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 50.0% | - | 12.0 |
| baseline_random_walk | low | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | low | 4 | 50.0% | - | 41.5 |
| ugh_v2_alpha | low | 4 | 75.0% | 100.0% | 12.3 |
| ugh_v2_beta | low | 4 | 75.0% | 100.0% | 10.2 |
| ugh_v2_delta | low | 4 | 75.0% | 100.0% | 11.2 |
| ugh_v2_gamma | low | 4 | 75.0% | 100.0% | 12.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 2 | 0.0% | - | 19.2 |
| baseline_prev_day_direction | trending | 2 | 100.0% | - | 4.8 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | choppy | 2 | 0.0% | - | 53.9 |
| baseline_simple_technical | trending | 2 | 100.0% | - | 29.2 |
| ugh_v2_alpha | choppy | 1 | 0.0% | 100.0% | 22.7 |
| ugh_v2_alpha | trending | 3 | 100.0% | 100.0% | 8.9 |
| ugh_v2_beta | choppy | 1 | 0.0% | 100.0% | 23.4 |
| ugh_v2_beta | trending | 3 | 100.0% | 100.0% | 5.8 |
| ugh_v2_delta | choppy | 1 | 0.0% | 100.0% | 23.0 |
| ugh_v2_delta | trending | 3 | 100.0% | 100.0% | 7.2 |
| ugh_v2_gamma | choppy | 1 | 0.0% | 100.0% | 21.6 |
| ugh_v2_gamma | trending | 3 | 100.0% | 100.0% | 8.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 7.8 |
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 24.6 |
| baseline_random_walk | low | 3 | 0.0% | - | 9.9 |
| baseline_random_walk | normal | 1 | 0.0% | - | 20.2 |
| baseline_simple_technical | high | 1 | 0.0% | - | 59.9 |
| baseline_simple_technical | normal | 3 | 66.7% | - | 35.4 |
| ugh_v2_alpha | low | 3 | 100.0% | 100.0% | 8.9 |
| ugh_v2_alpha | normal | 1 | 0.0% | 100.0% | 22.7 |
| ugh_v2_beta | low | 3 | 100.0% | 100.0% | 5.8 |
| ugh_v2_beta | normal | 1 | 0.0% | 100.0% | 23.4 |
| ugh_v2_delta | low | 3 | 100.0% | 100.0% | 7.2 |
| ugh_v2_delta | normal | 1 | 0.0% | 100.0% | 23.0 |
| ugh_v2_gamma | low | 3 | 100.0% | 100.0% | 8.9 |
| ugh_v2_gamma | normal | 1 | 0.0% | 100.0% | 21.6 |

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
