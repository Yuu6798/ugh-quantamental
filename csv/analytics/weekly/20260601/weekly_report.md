# FX Weekly Report v2 — 20260525 to 20260529

Generated: 2026-06-01T06:26:07Z
Report date (JST): 2026-06-01T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 1 | 25.0% | - | - | 21.1 | 20.8 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 14.4 | 16.0 |
| baseline_simple_technical | 4 | 2 | 50.0% | - | - | 32.8 | 31.8 |
| ugh_v2_alpha | 4 | 2 | 50.0% | - | 25.0% | 18.9 | 15.7 |
| ugh_v2_beta | 4 | 2 | 50.0% | - | 50.0% | 19.2 | 16.6 |
| ugh_v2_delta | 4 | 2 | 50.0% | - | 50.0% | 19.1 | 16.1 |
| ugh_v2_gamma | 4 | 2 | 50.0% | - | 50.0% | 17.8 | 15.4 |
| ugh_v2_ensemble |  |  | - | 100.0% | - | - | - |

## AI Annotation Layer

- **AI annotated**: 28
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 28 | 0 | 0 | 28 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 28 |
| volatility_label | 28 | 0 | 0 | 28 | 0 |
| intervention_risk | 28 | 0 | 0 | 28 | 0 |
| failure_reason | 8 | 0 | 0 | 8 | 20 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 25.0% | - | 21.1 |
| baseline_random_walk | low | 4 | 0.0% | - | 14.4 |
| baseline_simple_technical | low | 4 | 50.0% | - | 32.8 |
| ugh_v2_alpha | low | 4 | 50.0% | - | 18.9 |
| ugh_v2_beta | low | 4 | 50.0% | - | 19.2 |
| ugh_v2_delta | low | 4 | 50.0% | - | 19.1 |
| ugh_v2_gamma | low | 4 | 50.0% | - | 17.8 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 3 | 0.0% | - | 24.5 |
| baseline_prev_day_direction | trending | 1 | 100.0% | - | 10.7 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 14.4 |
| baseline_simple_technical | choppy | 2 | 0.0% | - | 46.9 |
| baseline_simple_technical | trending | 2 | 100.0% | - | 18.6 |
| ugh_v2_alpha | choppy | 2 | 0.0% | - | 28.9 |
| ugh_v2_alpha | trending | 2 | 100.0% | - | 8.8 |
| ugh_v2_beta | choppy | 2 | 0.0% | - | 27.7 |
| ugh_v2_beta | trending | 2 | 100.0% | - | 10.7 |
| ugh_v2_delta | choppy | 2 | 0.0% | - | 28.3 |
| ugh_v2_delta | trending | 2 | 100.0% | - | 9.9 |
| ugh_v2_gamma | choppy | 2 | 0.0% | - | 27.4 |
| ugh_v2_gamma | trending | 2 | 100.0% | - | 8.3 |
| ugh_v2_ensemble | choppy |  | - | 100.0% | - |
| ugh_v2_ensemble | trending |  | - | 100.0% | - |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 2 | 50.0% | - | 13.2 |
| baseline_prev_day_direction | normal | 2 | 0.0% | - | 28.9 |
| baseline_random_walk | low | 3 | 0.0% | - | 10.9 |
| baseline_random_walk | normal | 1 | 0.0% | - | 25.2 |
| baseline_simple_technical | high | 1 | 0.0% | - | 54.5 |
| baseline_simple_technical | low | 1 | 100.0% | - | 12.9 |
| baseline_simple_technical | normal | 2 | 50.0% | - | 31.8 |
| ugh_v2_alpha | low | 2 | 100.0% | - | 8.8 |
| ugh_v2_alpha | normal | 2 | 0.0% | - | 28.9 |
| ugh_v2_beta | low | 3 | 66.7% | - | 13.7 |
| ugh_v2_beta | normal | 1 | 0.0% | - | 35.8 |
| ugh_v2_delta | low | 2 | 100.0% | - | 9.9 |
| ugh_v2_delta | normal | 2 | 0.0% | - | 28.3 |
| ugh_v2_gamma | low | 3 | 66.7% | - | 11.8 |
| ugh_v2_gamma | normal | 1 | 0.0% | - | 35.8 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |
| ugh_v2_ensemble | normal |  | - | 100.0% | - |

## Provider Health Summary

- **Total runs**: 13
- **Success**: 5
- **Failed**: 0
- **Skipped**: 8
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (13)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
