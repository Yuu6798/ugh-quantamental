# FX Weekly Report v2 — 20260615 to 20260619

Generated: 2026-06-22T06:23:24Z
Report date (JST): 2026-06-22T08:00:00+09:00
Business days: 5
Total observations: 28
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 4 | 4 | 100.0% | - | - | 12.5 | 9.1 |
| baseline_random_walk | 4 | 0 | 0.0% | - | - | 18.8 | 12.5 |
| baseline_simple_technical | 4 | 4 | 100.0% | - | - | 11.3 | 5.5 |
| ugh_v2_alpha | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.3 | 6.9 |
| ugh_v2_beta | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.0 | 6.3 |
| ugh_v2_delta | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.2 | 6.6 |
| ugh_v2_gamma | 4 | 4 | 100.0% | 75.0% | 100.0% | 13.5 | 7.1 |

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
| failure_reason | 0 | 0 | 0 | 0 | 28 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 100.0% | - | 12.5 |
| baseline_random_walk | low | 4 | 0.0% | - | 18.8 |
| baseline_simple_technical | low | 4 | 100.0% | - | 11.3 |
| ugh_v2_alpha | low | 4 | 100.0% | 75.0% | 13.3 |
| ugh_v2_beta | low | 4 | 100.0% | 75.0% | 13.0 |
| ugh_v2_delta | low | 4 | 100.0% | 75.0% | 13.2 |
| ugh_v2_gamma | low | 4 | 100.0% | 75.0% | 13.5 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 4 | 100.0% | - | 12.5 |
| baseline_random_walk | choppy | 4 | 0.0% | - | 18.8 |
| baseline_simple_technical | trending | 4 | 100.0% | - | 11.3 |
| ugh_v2_alpha | trending | 4 | 100.0% | 75.0% | 13.3 |
| ugh_v2_beta | trending | 4 | 100.0% | 75.0% | 13.0 |
| ugh_v2_delta | trending | 4 | 100.0% | 75.0% | 13.2 |
| ugh_v2_gamma | trending | 4 | 100.0% | 75.0% | 13.5 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 100.0% | - | 7.1 |
| baseline_prev_day_direction | normal | 1 | 100.0% | - | 28.6 |
| baseline_random_walk | low | 3 | 0.0% | - | 10.4 |
| baseline_random_walk | normal | 1 | 0.0% | - | 44.2 |
| baseline_simple_technical | low | 3 | 100.0% | - | 4.7 |
| baseline_simple_technical | normal | 1 | 100.0% | - | 31.2 |
| ugh_v2_alpha | low | 3 | 100.0% | 100.0% | 4.6 |
| ugh_v2_alpha | normal | 1 | 100.0% | 0.0% | 39.4 |
| ugh_v2_beta | low | 3 | 100.0% | 100.0% | 4.7 |
| ugh_v2_beta | normal | 1 | 100.0% | 0.0% | 38.0 |
| ugh_v2_delta | low | 3 | 100.0% | 100.0% | 4.7 |
| ugh_v2_delta | normal | 1 | 100.0% | 0.0% | 38.6 |
| ugh_v2_gamma | low | 3 | 100.0% | 100.0% | 4.9 |
| ugh_v2_gamma | normal | 1 | 100.0% | 0.0% | 39.5 |

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
