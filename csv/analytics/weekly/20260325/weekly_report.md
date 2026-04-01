# FX Weekly Report v2 — 20260318 to 20260324

Generated: 2026-04-01T04:28:10Z
Report date (JST): 2026-03-25T08:00:00+09:00
Business days: 5
Total observations: 12
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 3 | 0 | 0.0% | - | - | 147.4 | 146.0 |
| baseline_random_walk | 3 | 0 | 0.0% | - | - | 54.4 | 49.6 |
| baseline_simple_technical | 3 | 2 | 66.7% | - | - | 58.6 | 60.5 |
| ugh | 3 | 2 | 66.7% | 33.3% | 100.0% | 54.3 | 49.9 |

### Event-Tag Analysis (sources: manual_compat: 8, none: 4)

| Strategy | Tag | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | geopolitical_shock | 1 | 0.0% | - | 146.0 |
| baseline_prev_day_direction | oil_retreat | 1 | 0.0% | - | 66.7 |
| baseline_prev_day_direction | us_iran | 2 | 0.0% | - | 106.3 |
| baseline_random_walk | geopolitical_shock | 1 | 0.0% | - | 49.6 |
| baseline_random_walk | oil_retreat | 1 | 0.0% | - | 17.0 |
| baseline_random_walk | us_iran | 2 | 0.0% | - | 33.3 |
| baseline_simple_technical | geopolitical_shock | 1 | 0.0% | - | 90.3 |
| baseline_simple_technical | oil_retreat | 1 | 100.0% | - | 25.2 |
| baseline_simple_technical | us_iran | 2 | 50.0% | - | 57.7 |
| ugh | geopolitical_shock | 1 | 0.0% | 0.0% | 49.9 |
| ugh | oil_retreat | 1 | 100.0% | 100.0% | 16.8 |
| ugh | us_iran | 2 | 50.0% | 50.0% | 33.3 |

## AI Annotation Layer

- **AI annotated**: 12
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 12 | 0 | 0 | 12 | 0 |
| event_tags | 0 | 0 | 8 | 8 | 4 |
| volatility_label | 12 | 0 | 0 | 12 | 0 |
| intervention_risk | 12 | 0 | 0 | 12 | 0 |
| failure_reason | 1 | 0 | 0 | 1 | 11 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 0.0% | - | 106.3 |
| baseline_prev_day_direction | medium | 1 | 0.0% | - | 229.6 |
| baseline_random_walk | low | 2 | 0.0% | - | 33.3 |
| baseline_random_walk | medium | 1 | 0.0% | - | 96.4 |
| baseline_simple_technical | low | 2 | 50.0% | - | 57.7 |
| baseline_simple_technical | medium | 1 | 100.0% | - | 60.5 |
| ugh | low | 2 | 50.0% | 50.0% | 33.3 |
| ugh | medium | 1 | 100.0% | 0.0% | 96.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 3 | 0.0% | - | 147.4 |
| baseline_random_walk | choppy | 3 | 0.0% | - | 54.4 |
| baseline_simple_technical | choppy | 1 | 0.0% | - | 90.3 |
| baseline_simple_technical | trending | 2 | 100.0% | - | 42.8 |
| ugh | choppy | 1 | 0.0% | 0.0% | 49.9 |
| ugh | trending | 2 | 100.0% | 50.0% | 56.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 3 | 0.0% | - | 147.4 |
| baseline_random_walk | high | 1 | 0.0% | - | 96.4 |
| baseline_random_walk | low | 1 | 0.0% | - | 17.0 |
| baseline_random_walk | normal | 1 | 0.0% | - | 49.6 |
| baseline_simple_technical | high | 2 | 50.0% | - | 75.4 |
| baseline_simple_technical | normal | 1 | 100.0% | - | 25.2 |
| ugh | high | 1 | 100.0% | 0.0% | 96.2 |
| ugh | low | 1 | 100.0% | 100.0% | 16.8 |
| ugh | normal | 1 | 0.0% | 0.0% | 49.9 |

## Provider Health Summary

- **Total runs**: 0
- **Success**: 0
- **Failed**: 0
- **Skipped**: 0
- **Fallback adjustments**: 0
- **Lag occurrences**: 0

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
