# FX Weekly Report v2 — 20260608 to 20260612

Generated: 2026-06-15T06:17:45Z
Report date (JST): 2026-06-15T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | 20.0 | 14.4 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 16.2 | 13.4 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | 16.9 | 8.8 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 50.0% | 0.0% | 16.0 | 8.2 |
| ugh_v2_beta | 4 | 3 | 75.0% | 50.0% | 0.0% | 16.5 | 9.4 |
| ugh_v2_delta | 4 | 3 | 75.0% | 50.0% | 0.0% | 16.3 | 8.8 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 50.0% | 0.0% | 15.9 | 8.1 |

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
| failure_reason | 4 | 0 | 0 | 4 | 24 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 20.0 |
| baseline_random_walk | low | 4 | 0.0% | - | 16.2 |
| baseline_simple_technical | low | 4 | 75.0% | - | 16.9 |
| ugh_v2_alpha | low | 4 | 75.0% | 50.0% | 16.0 |
| ugh_v2_beta | low | 4 | 75.0% | 50.0% | 16.5 |
| ugh_v2_delta | low | 4 | 75.0% | 50.0% | 16.3 |
| ugh_v2_gamma | low | 4 | 75.0% | 50.0% | 15.9 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 48.0 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 10.6 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 16.2 |
| baseline_simple_technical | choppy | 1 | 0.0% | - | 50.0 |
| baseline_simple_technical | trending | 3 | 100.0% | - | 5.9 |
| ugh_v2_alpha | choppy | 1 | 0.0% | 0.0% | 43.5 |
| ugh_v2_alpha | trending | 3 | 100.0% | 66.7% | 6.9 |
| ugh_v2_beta | choppy | 1 | 0.0% | 0.0% | 44.3 |
| ugh_v2_beta | trending | 3 | 100.0% | 66.7% | 7.3 |
| ugh_v2_delta | choppy | 1 | 0.0% | 0.0% | 43.9 |
| ugh_v2_delta | trending | 3 | 100.0% | 66.7% | 7.1 |
| ugh_v2_gamma | choppy | 1 | 0.0% | 0.0% | 43.0 |
| ugh_v2_gamma | trending | 3 | 100.0% | 66.7% | 6.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 100.0% | - | 10.6 |
| baseline_prev_day_direction | normal | 1 | 0.0% | - | 48.0 |
| baseline_random_walk | low | 3 | 0.0% | - | 9.6 |
| baseline_random_walk | normal | 1 | 0.0% | - | 36.1 |
| baseline_simple_technical | low | 3 | 100.0% | - | 5.9 |
| baseline_simple_technical | normal | 1 | 0.0% | - | 50.0 |
| ugh_v2_alpha | low | 3 | 100.0% | 66.7% | 6.9 |
| ugh_v2_alpha | normal | 1 | 0.0% | 0.0% | 43.5 |
| ugh_v2_beta | low | 3 | 100.0% | 66.7% | 7.3 |
| ugh_v2_beta | normal | 1 | 0.0% | 0.0% | 44.3 |
| ugh_v2_delta | low | 3 | 100.0% | 66.7% | 7.1 |
| ugh_v2_delta | normal | 1 | 0.0% | 0.0% | 43.9 |
| ugh_v2_gamma | low | 3 | 100.0% | 66.7% | 6.9 |
| ugh_v2_gamma | normal | 1 | 0.0% | 0.0% | 43.0 |

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
