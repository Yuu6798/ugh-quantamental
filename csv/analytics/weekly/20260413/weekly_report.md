# FX Weekly Report v2 — 20260406 to 20260410

Generated: 2026-04-13T03:45:41Z
Report date (JST): 2026-04-13T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | 42.5 | 35.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 24.8 | 18.3 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 44.7 | 34.5 |
| ugh | 4 | 2 | 50.0% | 75.0% | 100.0% | 24.8 | 18.3 |

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
| failure_reason | 2 | 0 | 0 | 2 | 14 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 0.0% | - | 38.3 |
| baseline_prev_day_direction | medium | 1 | 100.0% | - | 55.2 |
| baseline_random_walk | low | 3 | 0.0% | - | 13.4 |
| baseline_random_walk | medium | 1 | 0.0% | - | 58.9 |
| baseline_simple_technical | low | 3 | 66.7% | - | 27.4 |
| baseline_simple_technical | medium | 1 | 0.0% | - | 96.6 |
| ugh | low | 3 | 33.3% | 100.0% | 13.4 |
| ugh | medium | 1 | 100.0% | 0.0% | 58.9 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 3 | 0.0% | - | 38.3 |
| baseline_prev_day_direction | trending | 1 | 100.0% | - | 55.2 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 24.8 |
| baseline_simple_technical | choppy | 2 | 0.0% | - | 69.5 |
| baseline_simple_technical | trending | 2 | 100.0% | - | 19.9 |
| ugh | choppy | 2 | 0.0% | 100.0% | 18.3 |
| ugh | trending | 2 | 100.0% | 50.0% | 31.3 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 69.3 |
| baseline_prev_day_direction | low | 2 | 0.0% | - | 15.7 |
| baseline_random_walk | high | 1 | 0.0% | - | 58.9 |
| baseline_random_walk | low | 2 | 0.0% | - | 7.8 |
| baseline_random_walk | normal | 1 | 0.0% | - | 24.6 |
| baseline_simple_technical | high | 1 | 0.0% | - | 96.6 |
| baseline_simple_technical | low | 1 | 100.0% | - | 13.1 |
| baseline_simple_technical | normal | 2 | 50.0% | - | 34.5 |
| ugh | high | 1 | 100.0% | 0.0% | 58.9 |
| ugh | low | 2 | 50.0% | 100.0% | 7.8 |
| ugh | normal | 1 | 0.0% | 100.0% | 24.6 |

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
