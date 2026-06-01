# FX Weekly Report v2 — 20260504 to 20260508

Generated: 2026-06-01T06:26:07Z
Report date (JST): 2026-05-11T08:00:00+09:00
Business days: 5
Total observations: 7
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 1 | 0 | 0.0% | - | - | 49.2 | 49.2 |
| baseline_random_walk | 1 | 0 | 0.0% | - | - | 15.3 | 15.3 |
| baseline_simple_technical | 1 | 1 | 100.0% | - | - | 21.9 | 21.9 |
| ugh_v2_alpha | 1 | 1 | 100.0% | - | 0.0% | 11.1 | 11.1 |
| ugh_v2_beta | 1 | 0 | 0.0% | - | 100.0% | 17.9 | 17.9 |
| ugh_v2_delta | 1 | 1 | 100.0% | - | 0.0% | 14.9 | 14.9 |
| ugh_v2_gamma | 1 | 1 | 100.0% | - | 0.0% | 11.3 | 11.3 |
| ugh_v2_ensemble |  |  | - | 100.0% | - | - | - |

## AI Annotation Layer

- **AI annotated**: 7
- **Auto annotated**: 0
- **Manual compat**: 0
- **Unannotated**: 0
- **Model versions**: deterministic-v1
- **Prompt versions**: deterministic-p1
- **Slices interpretable**: Yes

### Field-Level Coverage

| Field | AI | Auto | Manual | Effective | Missing |
|---|---|---|---|---|---|
| regime_label | 7 | 0 | 0 | 7 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 7 |
| volatility_label | 7 | 0 | 0 | 7 | 0 |
| intervention_risk | 7 | 0 | 0 | 7 | 0 |
| failure_reason | 1 | 0 | 0 | 1 | 6 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 0.0% | - | 49.2 |
| baseline_random_walk | low | 1 | 0.0% | - | 15.3 |
| baseline_simple_technical | low | 1 | 100.0% | - | 21.9 |
| ugh_v2_alpha | low | 1 | 100.0% | - | 11.1 |
| ugh_v2_beta | low | 1 | 0.0% | - | 17.9 |
| ugh_v2_delta | low | 1 | 100.0% | - | 14.9 |
| ugh_v2_gamma | low | 1 | 100.0% | - | 11.3 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 49.2 |
| baseline_random_walk | choppy | 1 | 0.0% | - | 15.3 |
| baseline_simple_technical | trending | 1 | 100.0% | - | 21.9 |
| ugh_v2_alpha | trending | 1 | 100.0% | - | 11.1 |
| ugh_v2_beta | choppy | 1 | 0.0% | - | 17.9 |
| ugh_v2_delta | trending | 1 | 100.0% | - | 14.9 |
| ugh_v2_gamma | trending | 1 | 100.0% | - | 11.3 |
| ugh_v2_ensemble | choppy |  | - | 100.0% | - |
| ugh_v2_ensemble | trending |  | - | 100.0% | - |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 49.2 |
| baseline_random_walk | low | 1 | 0.0% | - | 15.3 |
| baseline_simple_technical | normal | 1 | 100.0% | - | 21.9 |
| ugh_v2_alpha | low | 1 | 100.0% | - | 11.1 |
| ugh_v2_beta | low | 1 | 0.0% | - | 17.9 |
| ugh_v2_delta | low | 1 | 100.0% | - | 14.9 |
| ugh_v2_gamma | low | 1 | 100.0% | - | 11.3 |
| ugh_v2_ensemble | low |  | - | 100.0% | - |

## Provider Health Summary

- **Total runs**: 4
- **Success**: 2
- **Failed**: 0
- **Skipped**: 2
- **Fallback adjustments**: 0
- **Lag occurrences**: 0
- **Providers used**: alpha_vantage (4)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
