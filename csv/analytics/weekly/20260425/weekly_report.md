# FX Weekly Report v2 — 20260420 to 20260424

Generated: 2026-04-24T11:49:57Z
Report date (JST): 2026-04-25T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: No

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | 26.9 | 28.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 18.1 | 13.2 |
| baseline_simple_technical | 4 | 0 | 0.0% | - | - | 43.1 | 38.2 |
| ugh | 4 | 0 | 0.0% | 75.0% | 100.0% | 18.2 | 13.4 |

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
| baseline_prev_day_direction | all | 4 | 75.0% | - | 26.9 |
| baseline_random_walk | all | 4 | 0.0% | - | 18.1 |
| baseline_simple_technical | all | 4 | 0.0% | - | 43.1 |
| ugh | all | 4 | 0.0% | 75.0% | 18.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 75.0% | - | 26.9 |
| baseline_random_walk | all | 4 | 0.0% | - | 18.1 |
| baseline_simple_technical | all | 4 | 0.0% | - | 43.1 |
| ugh | all | 4 | 0.0% | 75.0% | 18.2 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 4 | 75.0% | - | 26.9 |
| baseline_random_walk | all | 4 | 0.0% | - | 18.1 |
| baseline_simple_technical | all | 4 | 0.0% | - | 43.1 |
| ugh | all | 4 | 0.0% | 75.0% | 18.2 |

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
