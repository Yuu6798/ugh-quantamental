# FX Weekly Report v2 — 20260511 to 20260515

Generated: 2026-06-01T06:26:07Z
Report date (JST): 2026-05-18T08:00:00+09:00
Business days: 5
Total observations: 35
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 5 | 4 | 80.0% | - | - | 24.3 | 16.4 |
| baseline_random_walk | 5 | 0 | 0.0% | - | - | 30.6 | 29.3 |
| baseline_simple_technical | 5 | 0 | 0.0% | - | - | 69.5 | 68.6 |
| ugh_v2_alpha | 5 | 1 | 20.0% | - | 100.0% | 34.6 | 31.9 |
| ugh_v2_beta | 5 | 4 | 80.0% | - | 100.0% | 30.1 | 26.0 |
| ugh_v2_delta | 5 | 3 | 60.0% | - | 100.0% | 32.5 | 29.0 |
| ugh_v2_gamma | 5 | 2 | 40.0% | - | 100.0% | 34.2 | 31.6 |
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
| failure_reason | 10 | 0 | 0 | 10 | 25 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 5 | 80.0% | - | 24.3 |
| baseline_random_walk | low | 5 | 0.0% | - | 30.6 |
| baseline_simple_technical | low | 5 | 0.0% | - | 69.5 |
| ugh_v2_alpha | low | 5 | 20.0% | - | 34.6 |
| ugh_v2_beta | low | 5 | 80.0% | - | 30.1 |
| ugh_v2_delta | low | 5 | 60.0% | - | 32.5 |
| ugh_v2_gamma | low | 5 | 40.0% | - | 34.2 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 64.5 |
| baseline_prev_day_direction | trending | 4 | 100.0% | - | 14.2 |
| baseline_random_walk | choppy | 5 | 0.0% | - | 30.6 |
| baseline_simple_technical | choppy | 5 | 0.0% | - | 69.5 |
| ugh_v2_alpha | choppy | 4 | 0.0% | - | 37.7 |
| ugh_v2_alpha | trending | 1 | 100.0% | - | 22.2 |
| ugh_v2_beta | choppy | 1 | 0.0% | - | 62.8 |
| ugh_v2_beta | trending | 4 | 100.0% | - | 21.9 |
| ugh_v2_delta | choppy | 2 | 0.0% | - | 41.2 |
| ugh_v2_delta | trending | 3 | 100.0% | - | 26.7 |
| ugh_v2_gamma | choppy | 3 | 0.0% | - | 38.7 |
| ugh_v2_gamma | trending | 2 | 100.0% | - | 27.5 |
| ugh_v2_ensemble | choppy |  | - | 100.0% | - |
| ugh_v2_ensemble | trending |  | - | 100.0% | - |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 64.5 |
| baseline_prev_day_direction | low | 4 | 100.0% | - | 14.2 |
| baseline_random_walk | low | 1 | 0.0% | - | 16.5 |
| baseline_random_walk | normal | 4 | 0.0% | - | 34.2 |
| baseline_simple_technical | high | 5 | 0.0% | - | 69.5 |
| ugh_v2_alpha | high | 1 | 0.0% | - | 65.5 |
| ugh_v2_alpha | low | 1 | 0.0% | - | 19.9 |
| ugh_v2_alpha | normal | 3 | 33.3% | - | 29.2 |
| ugh_v2_beta | high | 1 | 0.0% | - | 62.8 |
| ugh_v2_beta | low | 2 | 100.0% | - | 16.3 |
| ugh_v2_beta | normal | 2 | 100.0% | - | 27.5 |
| ugh_v2_delta | high | 1 | 0.0% | - | 64.8 |
| ugh_v2_delta | low | 2 | 50.0% | - | 18.7 |
| ugh_v2_delta | normal | 2 | 100.0% | - | 30.1 |
| ugh_v2_gamma | high | 1 | 0.0% | - | 64.8 |
| ugh_v2_gamma | low | 1 | 0.0% | - | 19.7 |
| ugh_v2_gamma | normal | 3 | 66.7% | - | 28.9 |
| ugh_v2_ensemble | high |  | - | 100.0% | - |
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
