# FX Weekly Report v2 — 20260325 to 20260331

Generated: 2026-04-01T04:28:10Z
Report date (JST): 2026-04-01T08:00:00+09:00
Business days: 5
Total observations: 16
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | 32.7 | 29.6 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 30.1 | 30.7 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | 20.5 | 14.4 |
| ugh | 4 | 3 | 75.0% | 50.0% | 100.0% | 30.0 | 30.5 |

### Event-Tag Analysis (sources: manual_compat: 12, none: 4)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | boj_pm_rift | 1 | 100.0% | - | 27.8 |
| baseline_prev_day_direction | hawkish_fed | 1 | 100.0% | - | 31.5 |
| baseline_prev_day_direction | intervention_warning | 2 | 100.0% | - | 23.9 |
| baseline_prev_day_direction | ppi_us | 1 | 100.0% | - | 31.5 |
| baseline_prev_day_direction | us_iran | 2 | 100.0% | - | 25.8 |
| baseline_random_walk | boj_pm_rift | 1 | 0.0% | - | 20.7 |
| baseline_random_walk | hawkish_fed | 1 | 0.0% | - | 48.5 |
| baseline_random_walk | intervention_warning | 2 | 0.0% | - | 30.7 |
| baseline_random_walk | ppi_us | 1 | 0.0% | - | 48.5 |
| baseline_random_walk | us_iran | 2 | 0.0% | - | 44.6 |
| baseline_simple_technical | boj_pm_rift | 1 | 100.0% | - | 19.3 |
| baseline_simple_technical | hawkish_fed | 1 | 100.0% | - | 9.5 |
| baseline_simple_technical | intervention_warning | 2 | 100.0% | - | 9.8 |
| baseline_simple_technical | ppi_us | 1 | 100.0% | - | 9.5 |
| baseline_simple_technical | us_iran | 2 | 100.0% | - | 5.0 |
| ugh | boj_pm_rift | 1 | 100.0% | 100.0% | 20.5 |
| ugh | hawkish_fed | 1 | 100.0% | 0.0% | 48.3 |
| ugh | intervention_warning | 2 | 100.0% | 100.0% | 30.5 |
| ugh | ppi_us | 1 | 100.0% | 0.0% | 48.3 |
| ugh | us_iran | 2 | 100.0% | 50.0% | 44.4 |

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
| event_tags | 0 | 0 | 12 | 12 | 4 |
| volatility_label | 16 | 0 | 0 | 16 | 0 |
| intervention_risk | 16 | 0 | 0 | 16 | 0 |
| failure_reason | 1 | 0 | 0 | 1 | 15 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 32.7 |
| baseline_random_walk | low | 4 | 0.0% | - | 30.1 |
| baseline_simple_technical | low | 4 | 75.0% | - | 20.5 |
| ugh | low | 4 | 75.0% | 50.0% | 30.0 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 51.3 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 26.4 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 30.1 |
| baseline_simple_technical | choppy | 1 | 0.0% | - | 52.8 |
| baseline_simple_technical | trending | 3 | 100.0% | - | 9.7 |
| ugh | choppy | 1 | 0.0% | 0.0% | 10.9 |
| ugh | trending | 3 | 100.0% | 66.7% | 36.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 51.3 |
| baseline_prev_day_direction | normal | 3 | 100.0% | - | 26.4 |
| baseline_random_walk | low | 1 | 0.0% | - | 10.6 |
| baseline_random_walk | normal | 3 | 0.0% | - | 36.6 |
| baseline_simple_technical | high | 1 | 0.0% | - | 52.8 |
| baseline_simple_technical | low | 3 | 100.0% | - | 9.7 |
| ugh | low | 1 | 0.0% | 0.0% | 10.9 |
| ugh | normal | 3 | 100.0% | 66.7% | 36.4 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 4
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 1
- **Lag occurrences**: 1
- **Providers used**: alpha_vantage (14)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
