# FX Weekly Report v2 — 20260825 to 20260831

Generated: 2026-09-01T06:30:34Z
Report date (JST): 2026-09-01T08:00:00+09:00
Business days: 5
Total observations: 42
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 6 | 6 | 100.0% | - | - | - | 1.9 | 1.9 |
| baseline_random_walk | 6 | 0 | 0.0% | - | - | - | 7.8 | 8.2 |
| baseline_simple_technical | 6 | 2 | 33.3% | - | - | - | 45.0 | 49.9 |
| ugh_v2_alpha | 6 | 6 | 100.0% | 100.0% | 100.0% | 66.7% | 5.2 | 5.1 |
| ugh_v2_beta | 6 | 6 | 100.0% | 100.0% | 100.0% | 66.7% | 3.7 | 2.4 |
| ugh_v2_delta | 6 | 6 | 100.0% | 100.0% | 100.0% | 66.7% | 4.4 | 3.8 |
| ugh_v2_gamma | 6 | 6 | 100.0% | 100.0% | 100.0% | 66.7% | 4.8 | 5.0 |

## AI Annotation Layer

- **AI annotated**: 42
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
| regime_label | 42 | 0 | 0 | 0 | 42 | 0 |
| event_tags | 0 | 0 | 0 | 0 | 0 | 42 |
| volatility_label | 42 | 0 | 0 | 0 | 42 | 0 |
| intervention_risk | 42 | 0 | 0 | 0 | 42 | 0 |
| failure_reason | 0 | 0 | 0 | 0 | 0 | 42 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 6 | 100.0% | - | 1.9 |
| baseline_random_walk | low | 6 | 0.0% | - | 7.8 |
| baseline_simple_technical | low | 6 | 33.3% | - | 45.0 |
| ugh_v2_alpha | low | 6 | 100.0% | 100.0% | 5.2 |
| ugh_v2_beta | low | 6 | 100.0% | 100.0% | 3.7 |
| ugh_v2_delta | low | 6 | 100.0% | 100.0% | 4.4 |
| ugh_v2_gamma | low | 6 | 100.0% | 100.0% | 4.8 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 6 | 100.0% | - | 1.9 |
| baseline_random_walk | trending | 6 | 0.0% | - | 7.8 |
| baseline_simple_technical | trending | 6 | 33.3% | - | 45.0 |
| ugh_v2_alpha | trending | 6 | 100.0% | 100.0% | 5.2 |
| ugh_v2_beta | trending | 6 | 100.0% | 100.0% | 3.7 |
| ugh_v2_delta | trending | 6 | 100.0% | 100.0% | 4.4 |
| ugh_v2_gamma | trending | 6 | 100.0% | 100.0% | 4.8 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 4 | 100.0% | - | 2.5 |
| baseline_prev_day_direction | normal | 2 | 100.0% | - | 0.6 |
| baseline_random_walk | low | 4 | 0.0% | - | 7.5 |
| baseline_random_walk | normal | 2 | 0.0% | - | 8.2 |
| baseline_simple_technical | low | 4 | 50.0% | - | 42.5 |
| baseline_simple_technical | normal | 2 | 0.0% | - | 49.9 |
| ugh_v2_alpha | low | 4 | 100.0% | 100.0% | 5.9 |
| ugh_v2_alpha | normal | 2 | 100.0% | 100.0% | 3.6 |
| ugh_v2_beta | low | 4 | 100.0% | 100.0% | 4.5 |
| ugh_v2_beta | normal | 2 | 100.0% | 100.0% | 2.0 |
| ugh_v2_delta | low | 4 | 100.0% | 100.0% | 5.2 |
| ugh_v2_delta | normal | 2 | 100.0% | 100.0% | 2.8 |
| ugh_v2_gamma | low | 4 | 100.0% | 100.0% | 5.4 |
| ugh_v2_gamma | normal | 2 | 100.0% | 100.0% | 3.7 |

## Provider Health Summary

- **Total runs**: 13
- **Success**: 4
- **Failed**: 0
- **Skipped**: 9
- **Fallback adjustments**: 4
- **Lag occurrences**: 4
- **Providers used**: alpha_vantage (13)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
