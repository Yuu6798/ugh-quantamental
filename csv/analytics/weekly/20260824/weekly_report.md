# FX Weekly Report v2 — 20260817 to 20260821

Generated: 2026-08-24T02:18:34Z
Report date (JST): 2026-08-24T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | - | 69.1 | 64.9 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 43.5 | 35.0 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 63.3 | 52.7 |
| ugh_v2_alpha | 4 | 0 | 0.0% | 100.0% | 75.0% | 50.0% | 48.4 | 44.7 |
| ugh_v2_beta | 4 | 1 | 25.0% | 100.0% | 75.0% | 50.0% | 49.0 | 45.4 |
| ugh_v2_delta | 4 | 0 | 0.0% | 100.0% | 75.0% | 50.0% | 49.5 | 45.3 |
| ugh_v2_gamma | 4 | 0 | 0.0% | 100.0% | 75.0% | 50.0% | 47.6 | 43.2 |

## AI Annotation Layer

- **AI annotated**: 28
- **Auto annotated**: 0
- **Manual compat**: 0
- **OHLC fallback**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Fallback | Effective | Missing |
|---|---|---|---|---|---|---|
| regime_label | 28 | 0 | 0 | 0 | 28 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 28 |
| volatility_label | 28 | 0 | 0 | 0 | 28 | 0 |
| intervention_risk | 28 | 0 | 0 | 0 | 28 | 0 |
| failure_reason | 15 | 0 | 0 | 0 | 15 | 13 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 50.0% | - | 12.9 |
| baseline_prev_day_direction | medium | 2 | 0.0% | - | 125.3 |
| baseline_random_walk | low | 2 | 0.0% | - | 13.8 |
| baseline_random_walk | medium | 2 | 0.0% | - | 73.2 |
| baseline_simple_technical | low | 2 | 0.0% | - | 51.1 |
| baseline_simple_technical | medium | 2 | 50.0% | - | 75.5 |
| ugh_v2_alpha | low | 2 | 0.0% | 100.0% | 18.9 |
| ugh_v2_alpha | medium | 2 | 0.0% | 100.0% | 77.9 |
| ugh_v2_beta | low | 2 | 50.0% | 100.0% | 15.1 |
| ugh_v2_beta | medium | 2 | 0.0% | 100.0% | 82.9 |
| ugh_v2_delta | low | 2 | 0.0% | 100.0% | 18.1 |
| ugh_v2_delta | medium | 2 | 0.0% | 100.0% | 81.0 |
| ugh_v2_gamma | low | 2 | 0.0% | 100.0% | 18.1 |
| ugh_v2_gamma | medium | 2 | 0.0% | 100.0% | 77.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 25.0% | - | 69.1 |
| baseline_random_walk | trending | 4 | 0.0% | - | 43.5 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 63.3 |
| ugh_v2_alpha | trending | 4 | 0.0% | 100.0% | 48.4 |
| ugh_v2_beta | trending | 4 | 25.0% | 100.0% | 49.0 |
| ugh_v2_delta | trending | 4 | 0.0% | 100.0% | 49.5 |
| ugh_v2_gamma | trending | 4 | 0.0% | 100.0% | 47.6 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 104.0 |
| baseline_prev_day_direction | normal | 3 | 33.3% | - | 57.4 |
| baseline_random_walk | high | 1 | 0.0% | - | 90.2 |
| baseline_random_walk | normal | 3 | 0.0% | - | 28.0 |
| baseline_simple_technical | high | 1 | 100.0% | - | 54.2 |
| baseline_simple_technical | normal | 3 | 0.0% | - | 66.3 |
| ugh_v2_alpha | high | 1 | 0.0% | 100.0% | 90.2 |
| ugh_v2_alpha | normal | 3 | 0.0% | 100.0% | 34.4 |
| ugh_v2_beta | high | 1 | 0.0% | 100.0% | 95.8 |
| ugh_v2_beta | normal | 3 | 33.3% | 100.0% | 33.4 |
| ugh_v2_delta | high | 1 | 0.0% | 100.0% | 93.8 |
| ugh_v2_delta | normal | 3 | 0.0% | 100.0% | 34.8 |
| ugh_v2_gamma | high | 1 | 0.0% | 100.0% | 90.2 |
| ugh_v2_gamma | normal | 3 | 0.0% | 100.0% | 33.4 |

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
