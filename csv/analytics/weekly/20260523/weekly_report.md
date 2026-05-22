# FX Weekly Report v2 — 20260518 to 20260522

Generated: 2026-05-22T13:26:57Z
Report date (JST): 2026-05-23T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: No

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
| baseline_prev_day_direction | all | 4 | 50.0% | - | 12.0 |
| baseline_random_walk | all | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | all | 4 | 50.0% | - | 41.5 |
| ugh_v2_alpha | all | 4 | 75.0% | 100.0% | 12.3 |
| ugh_v2_beta | all | 4 | 75.0% | 100.0% | 10.2 |
| ugh_v2_delta | all | 4 | 75.0% | 100.0% | 11.2 |
| ugh_v2_gamma | all | 4 | 75.0% | 100.0% | 12.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 50.0% | - | 12.0 |
| baseline_random_walk | all | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | all | 4 | 50.0% | - | 41.5 |
| ugh_v2_alpha | all | 4 | 75.0% | 100.0% | 12.3 |
| ugh_v2_beta | all | 4 | 75.0% | 100.0% | 10.2 |
| ugh_v2_delta | all | 4 | 75.0% | 100.0% | 11.2 |
| ugh_v2_gamma | all | 4 | 75.0% | 100.0% | 12.1 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 50.0% | - | 12.0 |
| baseline_random_walk | all | 4 | 0.0% | - | 12.4 |
| baseline_simple_technical | all | 4 | 50.0% | - | 41.5 |
| ugh_v2_alpha | all | 4 | 75.0% | 100.0% | 12.3 |
| ugh_v2_beta | all | 4 | 75.0% | 100.0% | 10.2 |
| ugh_v2_delta | all | 4 | 75.0% | 100.0% | 11.2 |
| ugh_v2_gamma | all | 4 | 75.0% | 100.0% | 12.1 |

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
