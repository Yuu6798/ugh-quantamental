# FX Weekly Report v2 — 20260420 to 20260424

Generated: 2026-04-27T04:26:59Z
Report date (JST): 2026-04-27T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | 26.9 | 28.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 18.1 | 13.2 |
| baseline_simple_technical | 4 | 0 | 0.0% | - | - | 43.1 | 38.2 |
| ugh | 4 | 0 | 0.0% | 75.0% | 100.0% | 18.2 | 13.4 |

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
| failure_reason | 4 | 0 | 0 | 4 | 12 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 26.9 |
| baseline_random_walk | low | 4 | 0.0% | - | 18.1 |
| baseline_simple_technical | low | 4 | 0.0% | - | 43.1 |
| ugh | low | 4 | 0.0% | 75.0% | 18.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 44.7 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 21.0 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 18.1 |
| baseline_simple_technical | choppy | 4 | 0.0% | - | 43.1 |
| ugh | choppy | 4 | 0.0% | 75.0% | 18.2 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 6.3 |
| baseline_prev_day_direction | normal | 3 | 66.7% | - | 33.8 |
| baseline_random_walk | low | 3 | 0.0% | - | 11.3 |
| baseline_random_walk | normal | 1 | 0.0% | - | 38.4 |
| baseline_simple_technical | high | 1 | 0.0% | - | 63.0 |
| baseline_simple_technical | normal | 3 | 0.0% | - | 36.5 |
| ugh | low | 3 | 0.0% | 100.0% | 11.4 |
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
