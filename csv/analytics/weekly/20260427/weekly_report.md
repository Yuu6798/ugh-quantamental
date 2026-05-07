# FX Weekly Report v2 — 20260420 to 20260424

Generated: 2026-05-07T02:05:06Z
Report date (JST): 2026-04-27T08:00:00+09:00
Business days: 5
Total observations: 20
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | 27.2 | 28.2 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | 17.4 | 13.8 |
| baseline_simple_technical | 5 | 1 | 20.0% | - | - | 36.2 | 37.3 |
| ugh | 5 | 1 | 20.0% | 80.0% | 100.0% | 17.4 | 13.9 |

## AI Annotation Layer

- **AI annotated**: 20
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 20 | 0 | 0 | 20 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 20 |
| volatility_label | 20 | 0 | 0 | 20 | 0 |
| intervention_risk | 20 | 0 | 0 | 20 | 0 |
| failure_reason | 4 | 0 | 0 | 4 | 16 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 60.0% | - | 27.2 |
| baseline_random_walk | low | 5 | 0.0% | - | 17.4 |
| baseline_simple_technical | low | 5 | 20.0% | - | 36.2 |
| ugh | low | 5 | 20.0% | 80.0% | 17.4 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 2 | 0.0% | - | 36.4 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 21.0 |
| baseline_random_walk | choppy | 5 | 0.0% | - | 17.4 |
| baseline_simple_technical | choppy | 4 | 0.0% | - | 43.1 |
| baseline_simple_technical | trending | 1 | 100.0% | - | 8.8 |
| ugh | choppy | 4 | 0.0% | 75.0% | 18.2 |
| ugh | trending | 1 | 100.0% | 100.0% | 14.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 6.3 |
| baseline_prev_day_direction | normal | 4 | 50.0% | - | 32.4 |
| baseline_random_walk | low | 4 | 0.0% | - | 12.1 |
| baseline_random_walk | normal | 1 | 0.0% | - | 38.4 |
| baseline_simple_technical | high | 1 | 0.0% | - | 63.0 |
| baseline_simple_technical | low | 1 | 100.0% | - | 8.8 |
| baseline_simple_technical | normal | 3 | 0.0% | - | 36.5 |
| ugh | low | 4 | 25.0% | 100.0% | 12.2 |
| ugh | normal | 1 | 0.0% | 0.0% | 38.6 |

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
