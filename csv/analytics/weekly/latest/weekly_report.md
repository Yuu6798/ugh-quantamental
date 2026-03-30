# FX Weekly Report v2 — 20260323 to 20260327

Generated: 2026-03-30T02:56:31Z
Report date (JST): 2026-03-30T08:00:00+09:00
Business days: 5
Total observations: 20
Core analysis ready: Yes
Annotated analysis ready: No

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | 58.4 | 31.5 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | 35.3 | 40.7 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | 28.9 | 19.3 |
| ugh | 5 | 4 | 80.0% | 60.0% | 100.0% | 35.2 | 40.5 |

## Annotation Coverage

- **Total observations**: 20
- **Confirmed**: 0
- **Pending**: 0
- **Unlabeled**: 20
- **Coverage rate**: 0.0%

### Field-Level Coverage

| Field | Populated | Rate | Confirmed | Pending | Unlabeled |
|---|---|---|---|---|---|
| regime_label | 0 | 0.0% | 0 | 0 | 20 |
| event_tags | 0 | 0.0% | 0 | 0 | 20 |
| volatility_label | 0 | 0.0% | 0 | 0 | 20 |
| intervention_risk | 0 | 0.0% | 0 | 0 | 20 |

## Annotation-Dependent Analysis

> No confirmed annotations available. Regime, volatility, and intervention-risk slices show aggregate metrics per strategy (label='all'). Add confirmed annotations for labeled breakdown.

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 5 | 60.0% | - | 58.4 |
| baseline_random_walk | all | 5 | 0.0% | - | 35.3 |
| baseline_simple_technical | all | 5 | 80.0% | - | 28.9 |
| ugh | all | 5 | 80.0% | 60.0% | 35.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 5 | 60.0% | - | 58.4 |
| baseline_random_walk | all | 5 | 0.0% | - | 35.3 |
| baseline_simple_technical | all | 5 | 80.0% | - | 28.9 |
| ugh | all | 5 | 80.0% | 60.0% | 35.2 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | all | 5 | 60.0% | - | 58.4 |
| baseline_random_walk | all | 5 | 0.0% | - | 35.3 |
| baseline_simple_technical | all | 5 | 80.0% | - | 28.9 |
| ugh | all | 5 | 80.0% | 60.0% | 35.2 |

## Provider Health Summary

- **Total runs**: 7
- **Success**: 2
- **Failed**: 0
- **Skipped**: 5
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (7)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- Event-tag slices use effective_event_tags (auto-derived + manual when available).
- Regime/volatility/intervention slices require confirmed annotations.
