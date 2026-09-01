# FX Monthly Review v1 — USDJPY

Generated: 2026-09-01T08:00:00+09:00
Window: 20 business days requested, 18 included, 2 missing

## Monthly Summary

> Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

## Review Flags

- **regime_direction_collapse**: UGH direction rate collapsed below 40% in confirmed regime slice(s): trending (39%). Blended metrics mask this per-regime failure; direction logic needs regime-specific review.
- **volatility_direction_collapse**: UGH direction rate collapsed below 40% in confirmed volatility slice(s): normal (31%). Blended metrics mask this per-volatility failure; direction logic needs volatility-specific review.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Dir Rate (excl_flat) | Range Rate | State Persist | State Correct | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - | - | - |
| ugh_v2_alpha | 23 | 9 | 39.1% | 50.0% | 95.7% | 81.0% | 39.1% | 25.7 | 12.0 | 15.8 | 5.3 |
| ugh_v2_beta | 23 | 9 | 39.1% | 50.0% | 95.7% | 81.0% | 47.8% | 25.4 | 12.0 | 16.6 | 6.9 |
| ugh_v2_gamma | 23 | 9 | 39.1% | 50.0% | 95.7% | 81.0% | 39.1% | 25.4 | 11.8 | 16.0 | 5.3 |
| ugh_v2_delta | 23 | 7 | 30.4% | 41.2% | 95.7% | 81.0% | 47.8% | 25.9 | 12.0 | 16.1 | 6.1 |
| baseline_random_walk | 23 | 0 | 0.0% | - | - | - | - | 21.8 | 10.1 | 21.8 | 10.1 |
| baseline_prev_day_direction | 23 | 10 | 43.5% | 43.5% | - | - | - | 39.6 | 17.0 | 22.9 | 6.9 |
| baseline_simple_technical | 23 | 8 | 34.8% | 34.8% | - | - | - | 50.9 | 49.9 | 29.7 | 32.9 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Dir Acc Delta (excl_flat) | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|---|
| baseline_random_walk | -0.39 | -0.50 | -3.89 bp | +5.96 bp | - |
| baseline_prev_day_direction | +0.04 | -0.06 | +13.95 bp | +7.02 bp | - |
| baseline_simple_technical | -0.04 | -0.11 | +25.18 bp | +13.82 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| failure | 8 | 0.0% | 12.2 |
| fire | 32 | 21.9% | 38.4 |
| setup | 52 | 51.9% | 19.8 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| trending | 92 | 37.0% | 25.6 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 4 | 0.0% | 92.5 |
| low | 36 | 52.8% | 15.7 |
| normal | 52 | 28.8% | 27.3 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 80 | 42.5% | 14.5 |
| medium | 12 | 0.0% | 99.3 |

## Provider Health Summary

- **Total runs**: 58
- **Success**: 19
- **Failed**: 0
- **Skipped**: 39
- **Fallback adjustments**: 4
- **Lagged snapshots**: 4
- **Providers**: alpha_vantage (57), yahoo_finance (1)

## Annotation Coverage

- **Total observations**: 161
- **Confirmed**: 161
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-08-26T08:00:00+09:00** — Predicted up (6.194711466200469 bp), Realized up (8.167881377230174 bp), Error: 2.0 bp
2. **2026-08-26T08:00:00+09:00** — Predicted up (6.194711466200469 bp), Realized up (8.167881377230174 bp), Error: 2.0 bp
3. **2026-08-11T08:00:00+09:00** — Predicted up (4.588359293666709 bp), Realized up (2.5120894303850068 bp), Error: 2.1 bp

## Representative Failures

1. **2026-08-10T08:00:00+09:00** — Predicted down (-41.642491223683045 bp), Realized up (98.89691898060113 bp), Error: 140.5 bp
2. **2026-08-10T08:00:00+09:00** — Predicted down (-40.90080223005485 bp), Realized up (98.89691898060113 bp), Error: 139.8 bp
3. **2026-08-10T08:00:00+09:00** — Predicted down (-39.01158314528641 bp), Realized up (98.89691898060113 bp), Error: 137.9 bp

## Recommendation Summary

Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
