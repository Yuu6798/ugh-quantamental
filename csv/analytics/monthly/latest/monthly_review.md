# FX Monthly Review v1 — USDJPY

Generated: 2026-09-01T08:00:00+09:00
Window: 20 business days requested, 19 included, 1 missing

## Monthly Summary

> Review magnitude/close-error mapping in UGH engine. Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

## Review Flags

- **inspect_magnitude_mapping**: UGH mean abs close error is 5.5 bp worse than baseline_random_walk (threshold: 5.0 bp). Magnitude mapping may need review.
- **regime_direction_collapse**: UGH direction rate collapsed below 40% in confirmed regime slice(s): trending (32%). Blended metrics mask this per-regime failure; direction logic needs regime-specific review.
- **volatility_direction_collapse**: UGH direction rate collapsed below 40% in confirmed volatility slice(s): normal (27%). Blended metrics mask this per-volatility failure; direction logic needs volatility-specific review.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Dir Rate (excl_flat) | Range Rate | State Persist | State Correct | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - | - | - |
| ugh_v2_alpha | 19 | 6 | 31.6% | 40.0% | 94.7% | 83.3% | 36.8% | 30.9 | 13.8 | 18.1 | 6.8 |
| ugh_v2_beta | 19 | 6 | 31.6% | 40.0% | 94.7% | 83.3% | 47.4% | 30.5 | 14.8 | 18.8 | 6.9 |
| ugh_v2_gamma | 19 | 6 | 31.6% | 40.0% | 94.7% | 83.3% | 36.8% | 30.5 | 13.8 | 18.4 | 5.8 |
| ugh_v2_delta | 19 | 4 | 21.1% | 28.6% | 94.7% | 83.3% | 47.4% | 31.1 | 13.8 | 18.3 | 6.4 |
| baseline_random_walk | 19 | 0 | 0.0% | - | - | - | - | 25.3 | 12.0 | 25.3 | 12.0 |
| baseline_prev_day_direction | 19 | 7 | 36.8% | 36.8% | - | - | - | 46.8 | 36.3 | 25.4 | 7.5 |
| baseline_simple_technical | 19 | 6 | 31.6% | 31.6% | - | - | - | 52.2 | 49.9 | 27.4 | 29.3 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Dir Acc Delta (excl_flat) | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|---|
| baseline_random_walk | -0.32 | -0.40 | -5.53 bp | +7.23 bp | - |
| baseline_prev_day_direction | +0.05 | -0.07 | +15.90 bp | +7.30 bp | - |
| baseline_simple_technical | 0.00 | -0.07 | +21.31 bp | +9.33 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| failure | 4 | 0.0% | 12.2 |
| fire | 32 | 21.9% | 38.4 |
| setup | 40 | 37.5% | 26.5 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| trending | 76 | 28.9% | 30.7 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 4 | 0.0% | 92.5 |
| low | 28 | 39.3% | 18.7 |
| normal | 44 | 25.0% | 32.8 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 64 | 34.4% | 17.9 |
| medium | 12 | 0.0% | 99.3 |

## Event Tag Analysis (UGH, confirmed annotations)

| Event Tag | N | Dir Rate | Mean Err |
|---|---|---|---|
| month_end | 4 | 0.0% | 33.0 |

## Provider Health Summary

- **Total runs**: 58
- **Success**: 19
- **Failed**: 0
- **Skipped**: 39
- **Fallback adjustments**: 4
- **Lagged snapshots**: 4
- **Providers**: alpha_vantage (57), yahoo_finance (1)

## Annotation Coverage

- **Total observations**: 133
- **Confirmed**: 133
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-08-26T08:00:00+09:00** — Predicted up (6.194711466200469 bp), Realized up (8.167881377230174 bp), Error: 2.0 bp
2. **2026-08-11T08:00:00+09:00** — Predicted up (4.588359293666709 bp), Realized up (2.5120894303850068 bp), Error: 2.1 bp
3. **2026-08-25T08:00:00+09:00** — Predicted up (6.411532044426531 bp), Realized up (8.803924034711757 bp), Error: 2.4 bp

## Representative Failures

1. **2026-08-10T08:00:00+09:00** — Predicted down (-41.642491223683045 bp), Realized up (98.89691898060113 bp), Error: 140.5 bp
2. **2026-08-10T08:00:00+09:00** — Predicted down (-40.90080223005485 bp), Realized up (98.89691898060113 bp), Error: 139.8 bp
3. **2026-08-10T08:00:00+09:00** — Predicted down (-39.01158314528641 bp), Realized up (98.89691898060113 bp), Error: 137.9 bp

## Recommendation Summary

Review magnitude/close-error mapping in UGH engine. Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
