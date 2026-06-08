# FX Weekly Report v2 — 20260601 to 20260605

Generated: 2026-06-08T05:25:06Z
Report date (JST): 2026-06-08T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 3 | 75.0% | - | - | 10.5 | 8.5 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 11.8 | 11.9 |
| baseline_simple_technical | 4 | 3 | 75.0% | - | - | 11.5 | 11.7 |
| ugh_v2_alpha | 4 | 3 | 75.0% | 75.0% | 100.0% | 6.9 | 7.7 |
| ugh_v2_beta | 4 | 3 | 75.0% | 75.0% | 100.0% | 7.2 | 7.4 |
| ugh_v2_delta | 4 | 3 | 75.0% | 75.0% | 100.0% | 6.9 | 7.5 |
| ugh_v2_gamma | 4 | 3 | 75.0% | 75.0% | 100.0% | 7.0 | 6.8 |

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
| baseline_prev_day_direction | low | 4 | 75.0% | - | 10.5 |
| baseline_random_walk | low | 4 | 0.0% | - | 11.8 |
| baseline_simple_technical | low | 4 | 75.0% | - | 11.5 |
| ugh_v2_alpha | low | 4 | 75.0% | 75.0% | 6.9 |
| ugh_v2_beta | low | 4 | 75.0% | 75.0% | 7.2 |
| ugh_v2_delta | low | 4 | 75.0% | 75.0% | 6.9 |
| ugh_v2_gamma | low | 4 | 75.0% | 75.0% | 7.0 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | choppy | 1 | 0.0% | - | 10.0 |
| baseline_prev_day_direction | trending | 3 | 100.0% | - | 10.7 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 11.8 |
| baseline_simple_technical | choppy | 1 | 0.0% | - | 19.9 |
| baseline_simple_technical | trending | 3 | 100.0% | - | 8.7 |
| ugh_v2_alpha | choppy | 1 | 0.0% | 100.0% | 10.7 |
| ugh_v2_alpha | trending | 3 | 100.0% | 66.7% | 5.6 |
| ugh_v2_beta | choppy | 1 | 0.0% | 100.0% | 10.1 |
| ugh_v2_beta | trending | 3 | 100.0% | 66.7% | 6.2 |
| ugh_v2_delta | choppy | 1 | 0.0% | 100.0% | 10.3 |
| ugh_v2_delta | trending | 3 | 100.0% | 66.7% | 5.7 |
| ugh_v2_gamma | choppy | 1 | 0.0% | 100.0% | 10.2 |
| ugh_v2_gamma | trending | 3 | 100.0% | 66.7% | 5.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 75.0% | - | 10.5 |
| baseline_random_walk | low | 3 | 0.0% | - | 8.3 |
| baseline_random_walk | normal | 1 | 0.0% | - | 22.0 |
| baseline_simple_technical | low | 4 | 75.0% | - | 11.5 |
| ugh_v2_alpha | low | 4 | 75.0% | 75.0% | 6.9 |
| ugh_v2_beta | low | 4 | 75.0% | 75.0% | 7.2 |
| ugh_v2_delta | low | 4 | 75.0% | 75.0% | 6.9 |
| ugh_v2_gamma | low | 4 | 75.0% | 75.0% | 7.0 |

## Provider Health Summary

- **Total runs**: 15
- **Success**: 5
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 2
- **Lag occurrences**: 2
- **Providers used**: alpha_vantage (15)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
