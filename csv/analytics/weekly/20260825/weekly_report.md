# FX Weekly Report v2 — 20260818 to 20260824

Generated: 2026-09-01T06:30:34Z
Report date (JST): 2026-08-25T08:00:00+09:00
Business days: 5
Total observations: 49
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 7 | 1 | 14.3% | - | - | - | 58.2 | 61.3 |
| baseline_random_walk | 7 | 0 | 0.0% | - | - | - | 27.8 | 12.0 |
| baseline_simple_technical | 7 | 3 | 42.9% | - | - | - | 54.4 | 53.2 |
| ugh_v2_alpha | 7 | 0 | 0.0% | 100.0% | 57.1% | 42.9% | 30.3 | 12.0 |
| ugh_v2_beta | 7 | 1 | 14.3% | 100.0% | 57.1% | 42.9% | 33.3 | 17.0 |
| ugh_v2_delta | 7 | 0 | 0.0% | 100.0% | 57.1% | 42.9% | 32.3 | 13.2 |
| ugh_v2_gamma | 7 | 0 | 0.0% | 100.0% | 57.1% | 42.9% | 30.1 | 12.0 |

## AI Annotation Layer

- **AI annotated**: 49
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
| regime_label | 49 | 0 | 0 | 0 | 49 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 49 |
| volatility_label | 49 | 0 | 0 | 0 | 49 | 0 |
| intervention_risk | 49 | 0 | 0 | 0 | 49 | 0 |
| failure_reason | 27 | 0 | 0 | 0 | 27 | 22 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 20.0% | - | 31.3 |
| baseline_prev_day_direction | medium | 2 | 0.0% | - | 125.3 |
| baseline_random_walk | low | 5 | 0.0% | - | 9.6 |
| baseline_random_walk | medium | 2 | 0.0% | - | 73.2 |
| baseline_simple_technical | low | 5 | 40.0% | - | 45.9 |
| baseline_simple_technical | medium | 2 | 50.0% | - | 75.5 |
| ugh_v2_alpha | low | 5 | 0.0% | 100.0% | 11.3 |
| ugh_v2_alpha | medium | 2 | 0.0% | 100.0% | 77.9 |
| ugh_v2_beta | low | 5 | 20.0% | 100.0% | 13.4 |
| ugh_v2_beta | medium | 2 | 0.0% | 100.0% | 82.9 |
| ugh_v2_delta | low | 5 | 0.0% | 100.0% | 12.8 |
| ugh_v2_delta | medium | 2 | 0.0% | 100.0% | 81.0 |
| ugh_v2_gamma | low | 5 | 0.0% | 100.0% | 11.3 |
| ugh_v2_gamma | medium | 2 | 0.0% | 100.0% | 77.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 7 | 14.3% | - | 58.2 |
| baseline_random_walk | trending | 7 | 0.0% | - | 27.8 |
| baseline_simple_technical | trending | 7 | 42.9% | - | 54.4 |
| ugh_v2_alpha | trending | 7 | 0.0% | 100.0% | 30.3 |
| ugh_v2_beta | trending | 7 | 14.3% | 100.0% | 33.3 |
| ugh_v2_delta | trending | 7 | 0.0% | 100.0% | 32.3 |
| ugh_v2_gamma | trending | 7 | 0.0% | 100.0% | 30.1 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 104.0 |
| baseline_prev_day_direction | normal | 6 | 16.7% | - | 50.5 |
| baseline_random_walk | high | 1 | 0.0% | - | 90.2 |
| baseline_random_walk | normal | 6 | 0.0% | - | 17.3 |
| baseline_simple_technical | high | 1 | 100.0% | - | 54.2 |
| baseline_simple_technical | normal | 6 | 33.3% | - | 54.4 |
| ugh_v2_alpha | high | 1 | 0.0% | 100.0% | 90.2 |
| ugh_v2_alpha | normal | 6 | 0.0% | 100.0% | 20.3 |
| ugh_v2_beta | high | 1 | 0.0% | 100.0% | 95.8 |
| ugh_v2_beta | normal | 6 | 16.7% | 100.0% | 22.9 |
| ugh_v2_delta | high | 1 | 0.0% | 100.0% | 93.8 |
| ugh_v2_delta | normal | 6 | 0.0% | 100.0% | 22.1 |
| ugh_v2_gamma | high | 1 | 0.0% | 100.0% | 90.2 |
| ugh_v2_gamma | normal | 6 | 0.0% | 100.0% | 20.1 |

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
