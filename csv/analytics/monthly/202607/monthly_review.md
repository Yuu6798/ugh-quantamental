# FX Monthly Review v1 — USDJPY

Generated: 2026-07-01T08:00:00+09:00
Window: 20 business days requested, 19 included, 1 missing

## Monthly Summary

> All monthly metrics are within acceptable thresholds. Recommend keeping current logic unchanged for next period.

## Review Flags

- **keep_current_logic**: No review flags triggered. Current logic performance is within acceptable thresholds.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - | - |
| ugh_v2_alpha | 19 | 14 | 73.7% | 68.4% | 47.4% | 0.0% | 12.2 | 9.3 | 10.4 | 8.5 |
| ugh_v2_beta | 19 | 13 | 68.4% | 52.6% | 47.4% | 0.0% | 12.7 | 9.8 | 10.8 | 9.5 |
| ugh_v2_gamma | 19 | 14 | 73.7% | 73.7% | 47.4% | 0.0% | 12.1 | 9.6 | 10.4 | 8.6 |
| ugh_v2_delta | 19 | 13 | 68.4% | 63.2% | 47.4% | 0.0% | 12.6 | 9.9 | 10.7 | 9.1 |
| baseline_random_walk | 19 | 0 | 0.0% | - | - | - | 13.1 | 11.8 | 13.1 | 11.8 |
| baseline_prev_day_direction | 19 | 11 | 57.9% | - | - | - | 18.9 | 14.9 | 13.9 | 13.1 |
| baseline_simple_technical | 19 | 15 | 79.0% | - | - | - | 11.7 | 7.4 | 9.2 | 7.4 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|
| baseline_random_walk | -0.74 | +0.87 bp | +2.68 bp | - |
| baseline_prev_day_direction | -0.16 | +6.71 bp | +3.47 bp | - |
| baseline_simple_technical | +0.05 | -0.55 bp | -1.24 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| failure | 4 | 0.0% | 18.1 |
| fire | 16 | 100.0% | 6.7 |
| setup | 56 | 67.9% | 13.6 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| trending | 76 | 71.0% | 12.4 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 12 | 66.7% | 29.0 |
| low | 12 | 100.0% | 10.2 |
| normal | 52 | 65.4% | 9.1 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 76 | 71.0% | 12.4 |

## Provider Health Summary

- **Total runs**: 60
- **Success**: 20
- **Failed**: 0
- **Skipped**: 40
- **Fallback adjustments**: 4
- **Lagged snapshots**: 4
- **Providers**: alpha_vantage (60)

## Annotation Coverage

- **Total observations**: 133
- **Confirmed**: 133
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-06-15T08:00:00+09:00** — Predicted up (6.194052666098202 bp), Realized up (6.241418050180646 bp), Error: 0.0 bp
2. **2026-06-15T08:00:00+09:00** — Predicted up (5.889331709230115 bp), Realized up (6.241418050180646 bp), Error: 0.4 bp
3. **2026-06-15T08:00:00+09:00** — Predicted up (6.9716569731077485 bp), Realized up (6.241418050180646 bp), Error: 0.7 bp

## Representative Failures

1. **2026-06-11T08:00:00+09:00** — Predicted up (8.125384280721685 bp), Realized down (-36.13707165109112 bp), Error: 44.3 bp
2. **2026-06-11T08:00:00+09:00** — Predicted up (7.751742655176852 bp), Realized down (-36.13707165109112 bp), Error: 43.9 bp
3. **2026-06-11T08:00:00+09:00** — Predicted up (7.326121647159016 bp), Realized down (-36.13707165109112 bp), Error: 43.5 bp

## Recommendation Summary

All monthly metrics are within acceptable thresholds. Recommend keeping current logic unchanged for next period.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
