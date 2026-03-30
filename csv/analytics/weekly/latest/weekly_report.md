# FX Weekly Report v2 — 20260323 to 20260327

Generated: 2026-03-30T03:42:56Z
Report date (JST): 2026-03-30T08:00:00+09:00
Business days: 5
Total observations: 20
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | 58.4 | 31.5 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | 35.3 | 40.7 |
| baseline_simple_technical | 5 | 4 | 80.0% | - | - | 28.9 | 19.3 |
| ugh | 5 | 4 | 80.0% | 60.0% | 100.0% | 35.2 | 40.5 |

### Event-Tag Analysis (sources: manual: 20)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | boj_pm_rift | 1 | 100.0% | - | 27.8 |
| baseline_prev_day_direction | geopolitical_shock | 1 | 0.0% | - | 146.0 |
| baseline_prev_day_direction | hawkish_fed | 1 | 100.0% | - | 31.5 |
| baseline_prev_day_direction | intervention_warning | 2 | 100.0% | - | 23.9 |
| baseline_prev_day_direction | oil_retreat | 1 | 0.0% | - | 66.7 |
| baseline_prev_day_direction | ppi_us | 1 | 100.0% | - | 31.5 |
| baseline_prev_day_direction | us_iran | 4 | 50.0% | - | 66.0 |
| baseline_random_walk | boj_pm_rift | 1 | 0.0% | - | 20.7 |
| baseline_random_walk | geopolitical_shock | 1 | 0.0% | - | 49.6 |
| baseline_random_walk | hawkish_fed | 1 | 0.0% | - | 48.5 |
| baseline_random_walk | intervention_warning | 2 | 0.0% | - | 30.7 |
| baseline_random_walk | oil_retreat | 1 | 0.0% | - | 17.0 |
| baseline_random_walk | ppi_us | 1 | 0.0% | - | 48.5 |
| baseline_random_walk | us_iran | 4 | 0.0% | - | 39.0 |
| baseline_simple_technical | boj_pm_rift | 1 | 100.0% | - | 19.3 |
| baseline_simple_technical | geopolitical_shock | 1 | 0.0% | - | 90.3 |
| baseline_simple_technical | hawkish_fed | 1 | 100.0% | - | 9.5 |
| baseline_simple_technical | intervention_warning | 2 | 100.0% | - | 9.8 |
| baseline_simple_technical | oil_retreat | 1 | 100.0% | - | 25.2 |
| baseline_simple_technical | ppi_us | 1 | 100.0% | - | 9.5 |
| baseline_simple_technical | us_iran | 4 | 75.0% | - | 31.3 |
| ugh | boj_pm_rift | 1 | 100.0% | 100.0% | 20.5 |
| ugh | geopolitical_shock | 1 | 0.0% | 0.0% | 49.9 |
| ugh | hawkish_fed | 1 | 100.0% | 0.0% | 48.3 |
| ugh | intervention_warning | 2 | 100.0% | 100.0% | 30.5 |
| ugh | oil_retreat | 1 | 100.0% | 100.0% | 16.8 |
| ugh | ppi_us | 1 | 100.0% | 0.0% | 48.3 |
| ugh | us_iran | 4 | 75.0% | 50.0% | 38.9 |

## Annotation Coverage

- **Total observations**: 20
- **Confirmed**: 20
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

### Field-Level Coverage

| Field | Populated | Rate | Confirmed | Pending | Unlabeled |
|---|---|---|---|---|---|
| regime_label | 20 | 100.0% | 20 | 0 | 0 |
| event_tags | 20 | 100.0% | 20 | 0 | 0 |
| volatility_label | 20 | 100.0% | 20 | 0 | 0 |
| intervention_risk | 20 | 100.0% | 20 | 0 | 0 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 100.0% | - | 23.9 |
| baseline_prev_day_direction | medium | 3 | 33.3% | - | 81.4 |
| baseline_random_walk | high | 2 | 0.0% | - | 30.7 |
| baseline_random_walk | medium | 3 | 0.0% | - | 38.4 |
| baseline_simple_technical | high | 2 | 100.0% | - | 9.8 |
| baseline_simple_technical | medium | 3 | 66.7% | - | 41.7 |
| ugh | high | 2 | 100.0% | 100.0% | 30.5 |
| ugh | medium | 3 | 66.7% | 33.3% | 38.3 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | mixed | 1 | 0.0% | - | 146.0 |
| baseline_prev_day_direction | trending | 4 | 75.0% | - | 36.5 |
| baseline_random_walk | mixed | 1 | 0.0% | - | 49.6 |
| baseline_random_walk | trending | 4 | 0.0% | - | 31.7 |
| baseline_simple_technical | mixed | 1 | 0.0% | - | 90.3 |
| baseline_simple_technical | trending | 4 | 100.0% | - | 13.6 |
| ugh | mixed | 1 | 0.0% | 0.0% | 49.9 |
| ugh | trending | 4 | 100.0% | 75.0% | 31.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 2 | 50.0% | - | 88.7 |
| baseline_prev_day_direction | normal | 3 | 66.7% | - | 38.2 |
| baseline_random_walk | high | 2 | 0.0% | - | 49.1 |
| baseline_random_walk | normal | 3 | 0.0% | - | 26.1 |
| baseline_simple_technical | high | 2 | 50.0% | - | 49.9 |
| baseline_simple_technical | normal | 3 | 100.0% | - | 14.9 |
| ugh | high | 2 | 50.0% | 0.0% | 49.1 |
| ugh | normal | 3 | 100.0% | 100.0% | 25.9 |

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
