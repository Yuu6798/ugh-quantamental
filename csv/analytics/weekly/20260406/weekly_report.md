# FX Weekly Report v2 — 20260330 to 20260403

Generated: 2026-04-06T03:54:53Z
Report date (JST): 2026-04-06T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | 54.9 | 52.3 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 32.6 | 30.8 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 50.2 | 43.6 |
| ugh | 4 | 2 | 50.0% | 25.0% | 100.0% | 32.7 | 30.9 |

### Event-Tag Analysis (sources: auto_only: 4, none: 12)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | month_end | 1 | 100.0% | - | 53.2 |
| baseline_prev_day_direction | quarter_end | 1 | 100.0% | - | 53.2 |
| baseline_random_walk | month_end | 1 | 0.0% | - | 63.9 |
| baseline_random_walk | quarter_end | 1 | 0.0% | - | 63.9 |
| baseline_simple_technical | month_end | 1 | 0.0% | - | 101.1 |
| baseline_simple_technical | quarter_end | 1 | 0.0% | - | 101.1 |
| ugh | month_end | 1 | 0.0% | 0.0% | 64.3 |
| ugh | quarter_end | 1 | 0.0% | 0.0% | 64.3 |

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
| event_tags | 0 | 4 | 0 | 4 | 12 |
| volatility_label | 16 | 0 | 0 | 16 | 0 |
| intervention_risk | 16 | 0 | 0 | 16 | 0 |
| failure_reason | 2 | 0 | 0 | 2 | 14 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 0.0% | - | 60.1 |
| baseline_prev_day_direction | medium | 2 | 100.0% | - | 49.6 |
| baseline_random_walk | low | 2 | 0.0% | - | 7.8 |
| baseline_random_walk | medium | 2 | 0.0% | - | 57.4 |
| baseline_simple_technical | low | 2 | 50.0% | - | 43.6 |
| baseline_simple_technical | medium | 2 | 50.0% | - | 56.9 |
| ugh | low | 2 | 50.0% | 50.0% | 7.8 |
| ugh | medium | 2 | 50.0% | 0.0% | 57.6 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 2 | 0.0% | - | 60.1 |
| baseline_prev_day_direction | trending | 2 | 100.0% | - | 49.6 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 32.6 |
| baseline_simple_technical | choppy | 2 | 0.0% | - | 77.0 |
| baseline_simple_technical | trending | 2 | 100.0% | - | 23.6 |
| ugh | choppy | 2 | 0.0% | 0.0% | 37.6 |
| ugh | trending | 2 | 100.0% | 50.0% | 27.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 3 | 33.3% | - | 57.8 |
| baseline_prev_day_direction | normal | 1 | 100.0% | - | 46.0 |
| baseline_random_walk | high | 2 | 0.0% | - | 57.4 |
| baseline_random_walk | low | 2 | 0.0% | - | 7.8 |
| baseline_simple_technical | high | 2 | 0.0% | - | 77.0 |
| baseline_simple_technical | low | 1 | 100.0% | - | 12.7 |
| baseline_simple_technical | normal | 1 | 100.0% | - | 34.4 |
| ugh | high | 2 | 50.0% | 0.0% | 57.6 |
| ugh | low | 2 | 50.0% | 50.0% | 7.8 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 1
- **Lag occurrences**: 1
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
