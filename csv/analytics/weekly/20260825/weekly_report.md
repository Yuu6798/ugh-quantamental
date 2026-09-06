# FX Weekly Report v2 — 20260818 to 20260824

Generated: 2026-09-06T06:06:25Z
Report date (JST): 2026-08-25T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 1 | 20.0% | - | - | - | 65.8 | 61.3 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | - | 35.5 | 13.8 |
| baseline_simple_technical | 5 | 2 | 40.0% | - | - | - | 58.3 | 53.2 |
| ugh_v2_alpha | 5 | 0 | 0.0% | 100.0% | 60.0% | 40.0% | 38.2 | 13.8 |
| ugh_v2_beta | 5 | 1 | 20.0% | 100.0% | 60.0% | 40.0% | 40.8 | 17.0 |
| ugh_v2_delta | 5 | 0 | 0.0% | 100.0% | 60.0% | 40.0% | 40.2 | 13.8 |
| ugh_v2_gamma | 5 | 0 | 0.0% | 100.0% | 60.0% | 40.0% | 37.9 | 13.8 |

## AI Annotation Layer

- **AI annotated**: 35
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
| regime_label | 35 | 0 | 0 | 0 | 35 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 35 |
| volatility_label | 35 | 0 | 0 | 0 | 35 | 0 |
| intervention_risk | 35 | 0 | 0 | 0 | 35 | 0 |
| failure_reason | 19 | 0 | 0 | 0 | 19 | 16 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 33.3% | - | 26.1 |
| baseline_prev_day_direction | medium | 2 | 0.0% | - | 125.3 |
| baseline_random_walk | low | 3 | 0.0% | - | 10.3 |
| baseline_random_walk | medium | 2 | 0.0% | - | 73.2 |
| baseline_simple_technical | low | 3 | 33.3% | - | 46.8 |
| baseline_simple_technical | medium | 2 | 50.0% | - | 75.5 |
| ugh_v2_alpha | low | 3 | 0.0% | 100.0% | 11.7 |
| ugh_v2_alpha | medium | 2 | 0.0% | 100.0% | 77.9 |
| ugh_v2_beta | low | 3 | 33.3% | 100.0% | 12.8 |
| ugh_v2_beta | medium | 2 | 0.0% | 100.0% | 82.9 |
| ugh_v2_delta | low | 3 | 0.0% | 100.0% | 13.0 |
| ugh_v2_delta | medium | 2 | 0.0% | 100.0% | 81.0 |
| ugh_v2_gamma | low | 3 | 0.0% | 100.0% | 11.7 |
| ugh_v2_gamma | medium | 2 | 0.0% | 100.0% | 77.1 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 5 | 20.0% | - | 65.8 |
| baseline_random_walk | trending | 5 | 0.0% | - | 35.5 |
| baseline_simple_technical | trending | 5 | 40.0% | - | 58.3 |
| ugh_v2_alpha | trending | 5 | 0.0% | 100.0% | 38.2 |
| ugh_v2_beta | trending | 5 | 20.0% | 100.0% | 40.8 |
| ugh_v2_delta | trending | 5 | 0.0% | 100.0% | 40.2 |
| ugh_v2_gamma | trending | 5 | 0.0% | 100.0% | 37.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 104.0 |
| baseline_prev_day_direction | normal | 4 | 25.0% | - | 56.2 |
| baseline_random_walk | high | 1 | 0.0% | - | 90.2 |
| baseline_random_walk | normal | 4 | 0.0% | - | 21.8 |
| baseline_simple_technical | high | 1 | 100.0% | - | 54.2 |
| baseline_simple_technical | normal | 4 | 25.0% | - | 59.3 |
| ugh_v2_alpha | high | 1 | 0.0% | 100.0% | 90.2 |
| ugh_v2_alpha | normal | 4 | 0.0% | 100.0% | 25.1 |
| ugh_v2_beta | high | 1 | 0.0% | 100.0% | 95.8 |
| ugh_v2_beta | normal | 4 | 25.0% | 100.0% | 27.1 |
| ugh_v2_delta | high | 1 | 0.0% | 100.0% | 93.8 |
| ugh_v2_delta | normal | 4 | 0.0% | 100.0% | 26.8 |
| ugh_v2_gamma | high | 1 | 0.0% | 100.0% | 90.2 |
| ugh_v2_gamma | normal | 4 | 0.0% | 100.0% | 24.8 |

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
