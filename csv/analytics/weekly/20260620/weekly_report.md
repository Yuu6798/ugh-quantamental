# FX Weekly Report v2 — 20260615 to 20260619

Generated: 2026-06-19T13:58:50Z
Report date (JST): 2026-06-20T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: No

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 4 | 100.0% | - | - | 12.5 | 9.1 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 18.8 | 12.5 |
| baseline_simple_technical | 4 | 4 | 100.0% | - | - | 11.3 | 5.5 |
| ugh_v2_alpha | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.3 | 6.9 |
| ugh_v2_beta | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.0 | 6.3 |
| ugh_v2_delta | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.2 | 6.6 |
| ugh_v2_gamma | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.5 | 7.1 |

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
| baseline_prev_day_direction | all | 4 | 100.0% | - | 12.5 |
| baseline_random_walk | all | 4 | 0.0% | - | 18.8 |
| baseline_simple_technical | all | 4 | 100.0% | - | 11.3 |
| ugh_v2_alpha | all | 4 | 100.0% | 75.0% | 13.3 |
| ugh_v2_beta | all | 4 | 100.0% | 75.0% | 13.0 |
| ugh_v2_delta | all | 4 | 100.0% | 75.0% | 13.2 |
| ugh_v2_gamma | all | 4 | 100.0% | 75.0% | 13.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 100.0% | - | 12.5 |
| baseline_random_walk | all | 4 | 0.0% | - | 18.8 |
| baseline_simple_technical | all | 4 | 100.0% | - | 11.3 |
| ugh_v2_alpha | all | 4 | 100.0% | 75.0% | 13.3 |
| ugh_v2_beta | all | 4 | 100.0% | 75.0% | 13.0 |
| ugh_v2_delta | all | 4 | 100.0% | 75.0% | 13.2 |
| ugh_v2_gamma | all | 4 | 100.0% | 75.0% | 13.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 100.0% | - | 12.5 |
| baseline_random_walk | all | 4 | 0.0% | - | 18.8 |
| baseline_simple_technical | all | 4 | 100.0% | - | 11.3 |
| ugh_v2_alpha | all | 4 | 100.0% | 75.0% | 13.3 |
| ugh_v2_beta | all | 4 | 100.0% | 75.0% | 13.0 |
| ugh_v2_delta | all | 4 | 100.0% | 75.0% | 13.2 |
| ugh_v2_gamma | all | 4 | 100.0% | 75.0% | 13.5 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 2
- **Lag occurrences**: 2
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
