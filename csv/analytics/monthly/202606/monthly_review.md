# FX Monthly Review v1 — USDJPY

Generated: 2026-06-01T08:00:00+09:00
Window: 20 business days requested, 15 included, 5 missing

## Monthly Summary

> All monthly metrics are within acceptable thresholds. Recommend keeping current logic unchanged for next period.

## Review Flags

- **keep_current_logic**: No review flags triggered. Current logic performance is within acceptable thresholds.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - |
| ugh_v2_alpha | 15 | 8 | 53.3% | - | 73.3% | 20.7 | 19.9 | 14.1 | 11.1 |
| ugh_v2_beta | 15 | 10 | 66.7% | - | 86.7% | 19.1 | 17.6 | 13.3 | 12.7 |
| ugh_v2_gamma | 15 | 9 | 60.0% | - | 80.0% | 20.1 | 18.9 | 13.7 | 11.9 |
| ugh_v2_delta | 15 | 10 | 66.7% | - | 80.0% | 19.9 | 17.6 | 14.1 | 12.3 |
| baseline_random_walk | 15 | 0 | 0.0% | - | - | 19.4 | 16.5 | 19.4 | 16.5 |
| baseline_prev_day_direction | 15 | 8 | 53.3% | - | - | 20.9 | 15.7 | 12.8 | 10.7 |
| baseline_simple_technical | 15 | 6 | 40.0% | - | - | 46.0 | 47.8 | 20.9 | 21.9 |
| ugh_v2_ensemble |  |  | - | 100.0% | - | - | - | - | - |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|
| baseline_random_walk | -0.53 | -1.32 bp | +5.35 bp | - |
| baseline_prev_day_direction | 0.00 | +0.12 bp | -1.22 bp | - |
| baseline_simple_technical | -0.13 | +25.26 bp | +6.86 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| dormant | 7 | 57.1% | 19.3 |
| fire | 3 | 100.0% | 12.4 |
| setup | 50 | 60.0% | 20.5 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| choppy | 23 | 0.0% | 32.4 |
| trending | 37 | 100.0% | 12.2 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 4 | 0.0% | 64.5 |
| low | 36 | 83.3% | 10.4 |
| normal | 20 | 35.0% | 28.3 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 60 | 61.7% | 20.0 |

## Provider Health Summary

- **Total runs**: 47
- **Success**: 17
- **Failed**: 0
- **Skipped**: 30
- **Fallback adjustments**: 0
- **Lagged snapshots**: 0
- **Providers**: alpha_vantage (47)

## Annotation Coverage

- **Total observations**: 105
- **Confirmed**: 105
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-05-22T08:00:00+09:00** — Predicted up (15.567383929692548 bp), Realized up (15.0990877634482 bp), Error: 0.5 bp
2. **2026-05-22T08:00:00+09:00** — Predicted up (14.617955006508252 bp), Realized up (15.0990877634482 bp), Error: 0.5 bp
3. **2026-05-22T08:00:00+09:00** — Predicted up (15.657839621446369 bp), Realized up (15.0990877634482 bp), Error: 0.6 bp

## Representative Failures

1. **2026-05-11T08:00:00+09:00** — Predicted down (-16.316288885639082 bp), Realized up (49.23588464735663 bp), Error: 65.6 bp
2. **2026-05-11T08:00:00+09:00** — Predicted down (-15.560182451502355 bp), Realized up (49.23588464735663 bp), Error: 64.8 bp
3. **2026-05-11T08:00:00+09:00** — Predicted down (-15.525726898953526 bp), Realized up (49.23588464735663 bp), Error: 64.8 bp

## Recommendation Summary

All monthly metrics are within acceptable thresholds. Recommend keeping current logic unchanged for next period.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
