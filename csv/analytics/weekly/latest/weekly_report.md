# FX Weekly Report v2 — 20261019 to 20261023

Generated: 2026-10-26T05:39:52Z
Report date (JST): 2026-10-26T08:00:00+09:00
Business days: 5
Total observations: 21
Core analysis ready: Yes
Annotated analysis ready: Yes

## Core Analysis

### Strategy Performance

| Strategy | Obs | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err (bp) | Median Err (bp) |
|---|---|---|---|---|---|---|---|---|
| baseline_prev_day_direction | 3 | 2 | 66.7% | - | - | - | 33.9 | 31.6 |
| baseline_random_walk | 3 | 0 | 0.0% | - | - | - | 17.7 | 19.6 |
| baseline_simple_technical | 3 | 1 | 33.3% | - | - | - | 25.6 | 25.4 |
| ugh_v2_alpha | 3 | 1 | 33.3% | 100.0% | 100.0% | 100.0% | 18.0 | 25.3 |
| ugh_v2_beta | 3 | 1 | 33.3% | 100.0% | 100.0% | 100.0% | 19.1 | 27.9 |
| ugh_v2_delta | 3 | 1 | 33.3% | 100.0% | 100.0% | 100.0% | 18.6 | 26.7 |
| ugh_v2_gamma | 3 | 1 | 33.3% | 100.0% | 100.0% | 100.0% | 17.9 | 24.8 |

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
| failure_reason | 8 | 0 | 0 | 0 | 8 | 13 |

## Annotation-Dependent Analysis

### Intervention Risk

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | low | 3 | 66.7% | - | 33.9 |
| baseline_random_walk | low | 3 | 0.0% | - | 17.7 |
| baseline_simple_technical | low | 3 | 33.3% | - | 25.6 |
| ugh_v2_alpha | low | 3 | 33.3% | 100.0% | 18.0 |
| ugh_v2_beta | low | 3 | 33.3% | 100.0% | 19.1 |
| ugh_v2_delta | low | 3 | 33.3% | 100.0% | 18.6 |
| ugh_v2_gamma | low | 3 | 33.3% | 100.0% | 17.9 |

### Regime Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | trending | 3 | 66.7% | - | 33.9 |
| baseline_random_walk | trending | 3 | 0.0% | - | 17.7 |
| baseline_simple_technical | trending | 3 | 33.3% | - | 25.6 |
| ugh_v2_alpha | trending | 3 | 33.3% | 100.0% | 18.0 |
| ugh_v2_beta | trending | 3 | 33.3% | 100.0% | 19.1 |
| ugh_v2_delta | trending | 3 | 33.3% | 100.0% | 18.6 |
| ugh_v2_gamma | trending | 3 | 33.3% | 100.0% | 17.9 |

### Volatility Label

| Strategy | Label | Obs | Dir Rate | Range Rate | Mean Err (bp) |
|---|---|---|---|---|---|
| baseline_prev_day_direction | normal | 3 | 66.7% | - | 33.9 |
| baseline_random_walk | normal | 3 | 0.0% | - | 17.7 |
| baseline_simple_technical | normal | 3 | 33.3% | - | 25.6 |
| ugh_v2_alpha | normal | 3 | 33.3% | 100.0% | 18.0 |
| ugh_v2_beta | normal | 3 | 33.3% | 100.0% | 19.1 |
| ugh_v2_delta | normal | 3 | 33.3% | 100.0% | 18.6 |
| ugh_v2_gamma | normal | 3 | 33.3% | 100.0% | 17.9 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 4
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 2
- **Lag occurrences**: 2
- **Providers used**: alpha_vantage (14)

## Notes

- This report is generated from persisted CSV artifacts only.
- No forecast logic was re-executed.
- Core analysis (strategy performance) is always available.
- AI annotations are the primary source for slice analysis.
- Manual annotations are optional compatibility inputs.
