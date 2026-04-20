# FX Weekly Report v2 — 20260413 to 20260417

Generated: 2026-04-20T02:49:32Z
Report date (JST): 2026-04-20T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | 29.2 | 31.7 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 16.0 | 10.7 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 34.5 | 42.0 |
| ugh | 4 | 1 | 25.0% | 75.0% | 100.0% | 16.1 | 10.8 |

## AI Annotation Layer

- **AI annotated**: 16
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 16 | 0 | 0 | 16 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 16 |
| volatility_label | 16 | 0 | 0 | 16 | 0 |
| intervention_risk | 16 | 0 | 0 | 16 | 0 |
| failure_reason | 3 | 0 | 0 | 3 | 13 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 50.0% | - | 29.2 |
| baseline_random_walk | low | 4 | 0.0% | - | 16.0 |
| baseline_simple_technical | low | 4 | 50.0% | - | 34.5 |
| ugh | low | 4 | 25.0% | 75.0% | 16.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 2 | 0.0% | - | 47.4 |
| baseline_prev_day_direction | trending | 2 | 100.0% | - | 11.0 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 16.0 |
| baseline_simple_technical | choppy | 2 | 0.0% | - | 47.4 |
| baseline_simple_technical | trending | 2 | 100.0% | - | 21.5 |
| ugh | choppy | 3 | 0.0% | 100.0% | 7.5 |
| ugh | trending | 1 | 100.0% | 0.0% | 41.8 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 52.1 |
| baseline_prev_day_direction | low | 1 | 100.0% | - | 1.2 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 31.7 |
| baseline_random_walk | low | 3 | 0.0% | - | 7.3 |
| baseline_random_walk | normal | 1 | 0.0% | - | 42.0 |
| baseline_simple_technical | low | 1 | 100.0% | - | 6.0 |
| baseline_simple_technical | normal | 3 | 33.3% | - | 44.0 |
| ugh | low | 3 | 0.0% | 100.0% | 7.5 |
| ugh | normal | 1 | 100.0% | 0.0% | 41.8 |

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
