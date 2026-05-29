# FX Weekly Report v2 — 20260525 to 20260529

Generated: 2026-05-29T13:54:45Z
Report date (JST): 2026-05-30T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: No

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | 21.1 | 20.8 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 14.4 | 16.0 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 32.8 | 31.8 |
| ugh_v2_alpha | 4 | 2 | 50.0% | 100.0% | 25.0% | 18.9 | 15.7 |
| ugh_v2_beta | 4 | 2 | 50.0% | 100.0% | 50.0% | 19.2 | 16.6 |
| ugh_v2_delta | 4 | 2 | 50.0% | 100.0% | 50.0% | 19.1 | 16.1 |
| ugh_v2_gamma | 4 | 2 | 50.0% | 100.0% | 50.0% | 17.8 | 15.4 |

## AI Annotation Layer

- **AI annotated**: 0
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 28
- **Slices interpretable**: No

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 0 | 0 | 0 | 0 | 28 |
| event_tags | 0 | 0 | 0 | 0 | 28 |
| volatility_label | 0 | 0 | 0 | 0 | 28 |
| intervention_risk | 0 | 0 | 0 | 0 | 28 |
| failure_reason | 0 | 0 | 0 | 0 | 28 |

## Annotation-Dependent Analysis

> No confirmed annotations available. Regime, volatility, and intervention-risk slices show aggregate metrics per strategy (label='all'). Add confirmed annotations for labeled breakdown.

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 25.0% | - | 21.1 |
| baseline_random_walk | all | 4 | 0.0% | - | 14.4 |
| baseline_simple_technical | all | 4 | 50.0% | - | 32.8 |
| ugh_v2_alpha | all | 4 | 50.0% | 100.0% | 18.9 |
| ugh_v2_beta | all | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_delta | all | 4 | 50.0% | 100.0% | 19.1 |
| ugh_v2_gamma | all | 4 | 50.0% | 100.0% | 17.8 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 25.0% | - | 21.1 |
| baseline_random_walk | all | 4 | 0.0% | - | 14.4 |
| baseline_simple_technical | all | 4 | 50.0% | - | 32.8 |
| ugh_v2_alpha | all | 4 | 50.0% | 100.0% | 18.9 |
| ugh_v2_beta | all | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_delta | all | 4 | 50.0% | 100.0% | 19.1 |
| ugh_v2_gamma | all | 4 | 50.0% | 100.0% | 17.8 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 25.0% | - | 21.1 |
| baseline_random_walk | all | 4 | 0.0% | - | 14.4 |
| baseline_simple_technical | all | 4 | 50.0% | - | 32.8 |
| ugh_v2_alpha | all | 4 | 50.0% | 100.0% | 18.9 |
| ugh_v2_beta | all | 4 | 50.0% | 100.0% | 19.2 |
| ugh_v2_delta | all | 4 | 50.0% | 100.0% | 19.1 |
| ugh_v2_gamma | all | 4 | 50.0% | 100.0% | 17.8 |

## Provider Health Summary

- **Total runs**: 13
- **Success**: 5
- **Failed**: 0
- **Skipped**: 8
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (13)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
