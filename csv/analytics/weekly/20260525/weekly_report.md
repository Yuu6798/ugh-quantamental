# FX Weekly Report v2 — 20260518 to 20260522

Generated: 2026-06-01T06:26:07Z
Report date (JST): 2026-05-25T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 3 | 60.0% | - | - | 11.6 | 10.1 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | 13.0 | 15.1 |
| baseline_simple_technical | 5 | 3 | 60.0% | - | - | 37.9 | 34.0 |
| ugh_v2_alpha | 5 | 4 | 80.0% | - | 100.0% | 10.2 | 6.3 |
| ugh_v2_beta | 5 | 4 | 80.0% | - | 100.0% | 8.3 | 3.7 |
| ugh_v2_delta | 5 | 4 | 80.0% | - | 100.0% | 9.1 | 4.8 |
| ugh_v2_gamma | 5 | 4 | 80.0% | - | 100.0% | 9.7 | 6.7 |
| ugh_v2_ensemble |  |  | - | 100.0% | - | - | - |

## AI Annotation Layer

- **AI annotated**: 35
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 35 | 0 | 0 | 35 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 35 |
| volatility_label | 35 | 0 | 0 | 35 | 0 |
| intervention_risk | 35 | 0 | 0 | 35 | 0 |
| failure_reason | 4 | 0 | 0 | 4 | 31 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 60.0% | - | 11.6 |
| baseline_random_walk | low | 5 | 0.0% | - | 13.0 |
| baseline_simple_technical | low | 5 | 60.0% | - | 37.9 |
| ugh_v2_alpha | low | 5 | 80.0% | - | 10.2 |
| ugh_v2_beta | low | 5 | 80.0% | - | 8.3 |
| ugh_v2_delta | low | 5 | 80.0% | - | 9.1 |
| ugh_v2_gamma | low | 5 | 80.0% | - | 9.7 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 2 | 0.0% | - | 19.2 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 6.5 |
| baseline_random_walk | choppy | 5 | 0.0% | - | 13.0 |
| baseline_simple_technical | choppy | 2 | 0.0% | - | 53.9 |
| baseline_simple_technical | trending | 3 | 100.0% | - | 27.3 |
| ugh_v2_alpha | choppy | 1 | 0.0% | - | 22.7 |
| ugh_v2_alpha | trending | 4 | 100.0% | - | 7.1 |
| ugh_v2_beta | choppy | 1 | 0.0% | - | 23.4 |
| ugh_v2_beta | trending | 4 | 100.0% | - | 4.5 |
| ugh_v2_delta | choppy | 1 | 0.0% | - | 23.0 |
| ugh_v2_delta | trending | 4 | 100.0% | - | 5.6 |
| ugh_v2_gamma | choppy | 1 | 0.0% | - | 21.6 |
| ugh_v2_gamma | trending | 4 | 100.0% | - | 6.8 |
| ugh_v2_ensemble | choppy |  | - | 100.0% | - |
| ugh_v2_ensemble | trending |  | - | 100.0% | - |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 8.3 |
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 24.6 |
| baseline_random_walk | low | 4 | 0.0% | - | 11.2 |
| baseline_random_walk | normal | 1 | 0.0% | - | 20.2 |
| baseline_simple_technical | high | 1 | 0.0% | - | 59.9 |
| baseline_simple_technical | normal | 4 | 75.0% | - | 32.4 |
| ugh_v2_alpha | low | 4 | 100.0% | - | 7.1 |
| ugh_v2_alpha | normal | 1 | 0.0% | - | 22.7 |
| ugh_v2_beta | low | 4 | 100.0% | - | 4.5 |
| ugh_v2_beta | normal | 1 | 0.0% | - | 23.4 |
| ugh_v2_delta | low | 4 | 100.0% | - | 5.6 |
| ugh_v2_delta | normal | 1 | 0.0% | - | 23.0 |
| ugh_v2_gamma | low | 4 | 100.0% | - | 6.8 |
| ugh_v2_gamma | normal | 1 | 0.0% | - | 21.6 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |
| ugh_v2_ensemble | normal |  | - | 100.0% | - |

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
