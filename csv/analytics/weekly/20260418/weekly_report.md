# FX Weekly Report v2 — 20260413 to 20260417

Generated: 2026-04-17T11:41:06Z
Report date (JST): 2026-04-18T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: No

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | 29.2 | 31.7 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 16.0 | 10.7 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 34.5 | 42.0 |
| ugh | 4 | 1 | 25.0% | 75.0% | 100.0% | 16.1 | 10.8 |

## AI Annotation Layer

- **AI annotated**: 0
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 16
- **Slices interpretable**: No

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 0 | 0 | 0 | 0 | 16 |
| event_tags | 0 | 0 | 0 | 0 | 16 |
| volatility_label | 0 | 0 | 0 | 0 | 16 |
| intervention_risk | 0 | 0 | 0 | 0 | 16 |
| failure_reason | 0 | 0 | 0 | 0 | 16 |

## Annotation-Dependent Analysis

> No confirmed annotations available. Regime, volatility, and intervention-risk slices show aggregate metrics per strategy (label='all'). Add confirmed annotations for labeled breakdown.

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 50.0% | - | 29.2 |
| baseline_random_walk | all | 4 | 0.0% | - | 16.0 |
| baseline_simple_technical | all | 4 | 50.0% | - | 34.5 |
| ugh | all | 4 | 25.0% | 75.0% | 16.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 50.0% | - | 29.2 |
| baseline_random_walk | all | 4 | 0.0% | - | 16.0 |
| baseline_simple_technical | all | 4 | 50.0% | - | 34.5 |
| ugh | all | 4 | 25.0% | 75.0% | 16.1 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 50.0% | - | 29.2 |
| baseline_random_walk | all | 4 | 0.0% | - | 16.0 |
| baseline_simple_technical | all | 4 | 50.0% | - | 34.5 |
| ugh | all | 4 | 25.0% | 75.0% | 16.1 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 5
- **Failed**: 0
- **Skipped**: 9
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (14)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
