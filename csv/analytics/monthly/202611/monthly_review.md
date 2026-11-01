# FX Monthly Review v1 — USDJPY

Generated: 2026-11-01T08:00:00+09:00
Window: 20 business days requested, 18 included, 2 missing

## Monthly Summary

> Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

## Review Flags

- **regime_direction_collapse**: UGH direction rate collapsed below 40% in confirmed regime slice(s): trending (33%). Blended metrics mask this per-regime failure; direction logic needs regime-specific review.
- **volatility_direction_collapse**: UGH direction rate collapsed below 40% in confirmed volatility slice(s): normal (33%). Blended metrics mask this per-volatility failure; direction logic needs volatility-specific review.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Dir Rate (excl_flat) | Range Rate | State Persist | State Correct | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - | - | - |
| ugh_v2_alpha | 18 | 6 | 33.3% | 46.2% | 94.4% | 100.0% | 72.2% | 22.3 | 20.2 | 17.6 | 15.1 |
| ugh_v2_beta | 18 | 7 | 38.9% | 53.8% | 94.4% | 100.0% | 72.2% | 22.1 | 20.9 | 17.2 | 14.0 |
| ugh_v2_gamma | 18 | 6 | 33.3% | 46.2% | 94.4% | 100.0% | 72.2% | 22.2 | 19.9 | 17.7 | 15.0 |
| ugh_v2_delta | 18 | 7 | 38.9% | 53.8% | 94.4% | 100.0% | 72.2% | 22.0 | 20.2 | 17.4 | 15.0 |
| baseline_random_walk | 18 | 0 | 0.0% | - | - | - | - | 20.9 | 19.6 | 20.9 | 19.6 |
| baseline_prev_day_direction | 18 | 11 | 61.1% | 61.1% | - | - | - | 28.2 | 19.9 | 19.8 | 17.4 |
| baseline_simple_technical | 18 | 8 | 44.4% | 44.4% | - | - | - | 34.9 | 31.5 | 19.6 | 15.9 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Dir Acc Delta (excl_flat) | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|---|
| baseline_random_walk | -0.33 | -0.46 | -1.44 bp | +3.29 bp | - |
| baseline_prev_day_direction | +0.28 | +0.15 | +5.88 bp | +2.19 bp | - |
| baseline_simple_technical | +0.11 | 0.00 | +12.59 bp | +2.04 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| setup | 72 | 36.1% | 22.2 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| trending | 72 | 36.1% | 22.2 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 4 | 0.0% | 89.0 |
| low | 8 | 75.0% | 20.2 |
| normal | 60 | 33.3% | 18.0 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 68 | 38.2% | 18.2 |
| medium | 4 | 0.0% | 89.0 |

## Provider Health Summary

- **Total runs**: 59
- **Success**: 19
- **Failed**: 0
- **Skipped**: 40
- **Fallback adjustments**: 2
- **Lagged snapshots**: 2
- **Providers**: alpha_vantage (59)

## Annotation Coverage

- **Total observations**: 126
- **Confirmed**: 126
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-10-29T08:00:00+09:00** — Predicted down (-3.6045141272760945 bp), Realized down (-6.9708491761732345 bp), Error: 3.4 bp
2. **2026-10-29T08:00:00+09:00** — Predicted down (-3.4174739542697528 bp), Realized down (-6.9708491761732345 bp), Error: 3.6 bp
3. **2026-10-29T08:00:00+09:00** — Predicted down (-3.3227774342767016 bp), Realized down (-6.9708491761732345 bp), Error: 3.6 bp

## Representative Failures

1. **2026-10-22T08:00:00+09:00** — Predicted up (3.3268176103035767 bp), Realized down (-86.6375766774176 bp), Error: 90.0 bp
2. **2026-10-22T08:00:00+09:00** — Predicted up (3.2242966612828172 bp), Realized down (-86.6375766774176 bp), Error: 89.9 bp
3. **2026-10-22T08:00:00+09:00** — Predicted up (3.060545778202513 bp), Realized down (-86.6375766774176 bp), Error: 89.7 bp

## Recommendation Summary

Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
