# FX Weekly Report v2 — 20260914 to 20260918

Generated: 2026-09-18T15:02:48Z
Report date (JST): 2026-09-19T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 2 | 50.0% | - | - | - | 63.9 | 60.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | - | 51.0 | 55.6 |
| baseline_simple_technical | 4 | 1 | 25.0% | - | - | - | 88.3 | 100.2 |
| ugh_v2_alpha | 4 | 1 | 25.0% | 100.0% | 100.0% | 25.0% | 67.0 | 68.4 |
| ugh_v2_beta | 4 | 2 | 50.0% | 100.0% | 100.0% | 25.0% | 62.5 | 56.2 |
| ugh_v2_delta | 4 | 0 | 0.0% | 100.0% | 100.0% | 25.0% | 65.0 | 61.4 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 100.0% | 100.0% | 25.0% | 66.4 | 67.9 |

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
| failure_reason | 12 | 0 | 0 | 0 | 12 | 16 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 50.0% | - | 54.7 |
| baseline_prev_day_direction | medium | 2 | 50.0% | - | 73.2 |
| baseline_random_walk | low | 2 | 0.0% | - | 32.3 |
| baseline_random_walk | medium | 2 | 0.0% | - | 69.7 |
| baseline_simple_technical | low | 2 | 50.0% | - | 61.4 |
| baseline_simple_technical | medium | 2 | 0.0% | - | 115.2 |
| ugh_v2_alpha | low | 2 | 50.0% | 100.0% | 32.8 |
| ugh_v2_alpha | medium | 2 | 0.0% | 100.0% | 101.2 |
| ugh_v2_beta | low | 2 | 50.0% | 100.0% | 29.8 |
| ugh_v2_beta | medium | 2 | 50.0% | 100.0% | 95.1 |
| ugh_v2_delta | low | 2 | 0.0% | 100.0% | 32.3 |
| ugh_v2_delta | medium | 2 | 0.0% | 100.0% | 97.8 |
| ugh_v2_gamma | low | 2 | 50.0% | 100.0% | 32.8 |
| ugh_v2_gamma | medium | 2 | 0.0% | 100.0% | 100.0 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 50.0% | - | 63.9 |
| baseline_random_walk | trending | 4 | 0.0% | - | 51.0 |
| baseline_simple_technical | trending | 4 | 25.0% | - | 88.3 |
| ugh_v2_alpha | trending | 4 | 25.0% | 100.0% | 67.0 |
| ugh_v2_beta | trending | 4 | 50.0% | 100.0% | 62.5 |
| ugh_v2_delta | trending | 4 | 0.0% | 100.0% | 65.0 |
| ugh_v2_gamma | trending | 4 | 25.0% | 100.0% | 66.4 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 4 | 50.0% | - | 63.9 |
| baseline_random_walk | normal | 4 | 0.0% | - | 51.0 |
| baseline_simple_technical | normal | 4 | 25.0% | - | 88.3 |
| ugh_v2_alpha | normal | 4 | 25.0% | 100.0% | 67.0 |
| ugh_v2_beta | normal | 4 | 50.0% | 100.0% | 62.5 |
| ugh_v2_delta | normal | 4 | 0.0% | 100.0% | 65.0 |
| ugh_v2_gamma | normal | 4 | 25.0% | 100.0% | 66.4 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
