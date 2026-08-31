# FX Weekly Report v2 — 20260824 to 20260828

Generated: 2026-08-31T06:29:29Z
Report date (JST): 2026-08-31T08:00:00+09:00
Business days: 5
Total observations: 21
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 3 | 2 | 66.7% | - | - | - | 6.9 | 3.1 |
| baseline_random_walk | 3 | 0 | 0.0% | - | - | - | 9.6 | 8.8 |
| baseline_simple_technical | 3 | 0 | 0.0% | - | - | - | 51.2 | 50.5 |
| ugh_v2_alpha | 3 | 2 | 66.7% | 100.0% | 100.0% | 100.0% | 6.9 | 5.1 |
| ugh_v2_beta | 3 | 2 | 66.7% | 100.0% | 100.0% | 100.0% | 5.4 | 2.4 |
| ugh_v2_delta | 3 | 2 | 66.7% | 100.0% | 100.0% | 100.0% | 6.2 | 3.8 |
| ugh_v2_gamma | 3 | 2 | 66.7% | 100.0% | 100.0% | 100.0% | 6.9 | 5.0 |

## AI Annotation Layer

- **AI annotated**: 21
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
| regime_label | 21 | 0 | 0 | 0 | 21 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 21 |
| volatility_label | 21 | 0 | 0 | 0 | 21 | 0 |
| intervention_risk | 21 | 0 | 0 | 0 | 21 | 0 |
| failure_reason | 4 | 0 | 0 | 0 | 4 | 17 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 6.9 |
| baseline_random_walk | low | 3 | 0.0% | - | 9.6 |
| baseline_simple_technical | low | 3 | 0.0% | - | 51.2 |
| ugh_v2_alpha | low | 3 | 66.7% | 100.0% | 6.9 |
| ugh_v2_beta | low | 3 | 66.7% | 100.0% | 5.4 |
| ugh_v2_delta | low | 3 | 66.7% | 100.0% | 6.2 |
| ugh_v2_gamma | low | 3 | 66.7% | 100.0% | 6.9 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 3 | 66.7% | - | 6.9 |
| baseline_random_walk | trending | 3 | 0.0% | - | 9.6 |
| baseline_simple_technical | trending | 3 | 0.0% | - | 51.2 |
| ugh_v2_alpha | trending | 3 | 66.7% | 100.0% | 6.9 |
| ugh_v2_beta | trending | 3 | 66.7% | 100.0% | 5.4 |
| ugh_v2_delta | trending | 3 | 66.7% | 100.0% | 6.2 |
| ugh_v2_gamma | trending | 3 | 66.7% | 100.0% | 6.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 1 | 100.0% | - | 3.1 |
| baseline_prev_day_direction | normal | 2 | 50.0% | - | 8.8 |
| baseline_random_walk | low | 1 | 0.0% | - | 8.8 |
| baseline_random_walk | normal | 2 | 0.0% | - | 10.1 |
| baseline_simple_technical | low | 1 | 0.0% | - | 50.5 |
| baseline_simple_technical | normal | 2 | 0.0% | - | 51.5 |
| ugh_v2_alpha | low | 1 | 100.0% | 100.0% | 5.1 |
| ugh_v2_alpha | normal | 2 | 50.0% | 100.0% | 7.8 |
| ugh_v2_beta | low | 1 | 100.0% | 100.0% | 2.4 |
| ugh_v2_beta | normal | 2 | 50.0% | 100.0% | 7.0 |
| ugh_v2_delta | low | 1 | 100.0% | 100.0% | 3.8 |
| ugh_v2_delta | normal | 2 | 50.0% | 100.0% | 7.4 |
| ugh_v2_gamma | low | 1 | 100.0% | 100.0% | 5.0 |
| ugh_v2_gamma | normal | 2 | 50.0% | 100.0% | 7.8 |

## Provider Health Summary

- **Total runs**: 12
- **Success**: 4
- **Failed**: 0
- **Skipped**: 8
- **Fallback adjustments**: 3
- **Lag occurrences**: 3
- **Providers used**: alpha_vantage (12)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
