# FX Weekly Report v2 — 20260511 to 20260515

Generated: 2026-05-18T05:02:38Z
Report date (JST): 2026-05-18T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | 28.4 | 18.2 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 32.0 | 31.1 |
| baseline_simple_technical | 4 | 0 | 0.0% | - | - | 70.5 | 70.3 |
| ugh_v2_alpha | 4 | 0 | 0.0% | 100.0% | 100.0% | 37.7 | 32.8 |
| ugh_v2_beta | 4 | 3 | 75.0% | 100.0% | 100.0% | 33.2 | 27.5 |
| ugh_v2_delta | 4 | 2 | 50.0% | 100.0% | 100.0% | 35.7 | 30.1 |
| ugh_v2_gamma | 4 | 1 | 25.0% | 100.0% | 100.0% | 37.2 | 32.3 |

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
| failure_reason | 10 | 0 | 0 | 10 | 18 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 28.4 |
| baseline_random_walk | low | 4 | 0.0% | - | 32.0 |
| baseline_simple_technical | low | 4 | 0.0% | - | 70.5 |
| ugh_v2_alpha | low | 4 | 0.0% | 100.0% | 37.7 |
| ugh_v2_beta | low | 4 | 75.0% | 100.0% | 33.2 |
| ugh_v2_delta | low | 4 | 50.0% | 100.0% | 35.7 |
| ugh_v2_gamma | low | 4 | 25.0% | 100.0% | 37.2 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 64.5 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 16.4 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 32.0 |
| baseline_simple_technical | choppy | 4 | 0.0% | - | 70.5 |
| ugh_v2_alpha | choppy | 4 | 0.0% | 100.0% | 37.7 |
| ugh_v2_beta | choppy | 1 | 0.0% | 100.0% | 62.8 |
| ugh_v2_beta | trending | 3 | 100.0% | 100.0% | 23.3 |
| ugh_v2_delta | choppy | 2 | 0.0% | 100.0% | 41.2 |
| ugh_v2_delta | trending | 2 | 100.0% | 100.0% | 30.1 |
| ugh_v2_gamma | choppy | 3 | 0.0% | 100.0% | 38.7 |
| ugh_v2_gamma | trending | 1 | 100.0% | 100.0% | 32.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | high | 1 | 0.0% | - | 64.5 |
| baseline_prev_day_direction | low | 3 | 100.0% | - | 16.4 |
| baseline_random_walk | low | 1 | 0.0% | - | 16.5 |
| baseline_random_walk | normal | 3 | 0.0% | - | 37.1 |
| baseline_simple_technical | high | 4 | 0.0% | - | 70.5 |
| ugh_v2_alpha | high | 1 | 0.0% | 100.0% | 65.5 |
| ugh_v2_alpha | low | 1 | 0.0% | 100.0% | 19.9 |
| ugh_v2_alpha | normal | 2 | 0.0% | 100.0% | 32.8 |
| ugh_v2_beta | high | 1 | 0.0% | 100.0% | 62.8 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 14.9 |
| ugh_v2_beta | normal | 2 | 100.0% | 100.0% | 27.5 |
| ugh_v2_delta | high | 1 | 0.0% | 100.0% | 64.8 |
| ugh_v2_delta | low | 1 | 0.0% | 100.0% | 17.6 |
| ugh_v2_delta | normal | 2 | 100.0% | 100.0% | 30.1 |
| ugh_v2_gamma | high | 1 | 0.0% | 100.0% | 64.8 |
| ugh_v2_gamma | low | 1 | 0.0% | 100.0% | 19.7 |
| ugh_v2_gamma | normal | 2 | 50.0% | 100.0% | 32.3 |

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
