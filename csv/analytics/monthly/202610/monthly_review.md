# FX Monthly Review v1 — USDJPY

Generated: 2026-10-01T08:00:00+09:00
Window: 20 business days requested, 19 included, 1 missing

## Monthly Summary

> Review magnitude/close-error mapping in UGH engine. Review state-to-magnitude mapping — state hits are good but errors high.

## Review Flags

- **inspect_magnitude_mapping**: UGH mean abs close error is 7.4 bp worse than baseline_random_walk (threshold: 5.0 bp). Magnitude mapping may need review.
- **inspect_state_mapping**: State proxy hit rate (73.7%) is high but magnitude error (39.7 bp) exceeds threshold (30.0 bp). State-to-magnitude mapping may need review.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Dir Rate (excl_flat) | Range Rate | State Persist | State Correct | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - | - | - |
| ugh_v2_alpha | 19 | 8 | 42.1% | 53.3% | 89.5% | 73.7% | 26.3% | 59.7 | 46.4 | 39.7 | 31.9 |
| ugh_v2_beta | 19 | 10 | 52.6% | 66.7% | 89.5% | 68.4% | 26.3% | 56.8 | 42.2 | 38.9 | 31.9 |
| ugh_v2_gamma | 19 | 8 | 42.1% | 53.3% | 89.5% | 73.7% | 26.3% | 59.5 | 46.6 | 40.2 | 31.9 |
| ugh_v2_delta | 19 | 6 | 31.6% | 54.5% | 89.5% | 73.7% | 26.3% | 58.7 | 47.3 | 40.6 | 31.9 |
| baseline_random_walk | 19 | 0 | 0.0% | - | - | - | - | 52.3 | 47.3 | 52.3 | 47.3 |
| baseline_prev_day_direction | 19 | 9 | 47.4% | 47.4% | - | - | - | 74.0 | 77.6 | 46.3 | 31.9 |
| baseline_simple_technical | 19 | 8 | 42.1% | 42.1% | - | - | - | 69.5 | 63.4 | 29.1 | 17.1 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Dir Acc Delta (excl_flat) | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|---|
| baseline_random_walk | -0.42 | -0.53 | -7.41 bp | +12.61 bp | - |
| baseline_prev_day_direction | +0.05 | -0.07 | +14.23 bp | +6.64 bp | - |
| baseline_simple_technical | 0.00 | -0.07 | +9.74 bp | -10.63 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| failure | 5 | 100.0% | 44.4 |
| fire | 44 | 34.1% | 52.6 |
| setup | 27 | 44.4% | 71.2 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| trending | 76 | 42.1% | 58.7 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 12 | 8.3% | 134.3 |
| low | 8 | 50.0% | 8.3 |
| normal | 56 | 48.2% | 49.7 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 8 | 12.5% | 141.1 |
| low | 40 | 60.0% | 21.1 |
| medium | 28 | 25.0% | 88.7 |

## Provider Health Summary

- **Total runs**: 59
- **Success**: 20
- **Failed**: 0
- **Skipped**: 39
- **Fallback adjustments**: 17
- **Lagged snapshots**: 17
- **Providers**: alpha_vantage (58), yahoo_finance (1)

## Annotation Coverage

- **Total observations**: 133
- **Confirmed**: 133
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-09-22T08:00:00+09:00** — Predicted up (11.358884373685937 bp), Realized up (10.177469626613865 bp), Error: 1.2 bp
2. **2026-09-22T08:00:00+09:00** — Predicted up (7.9638811359407935 bp), Realized up (10.177469626613865 bp), Error: 2.2 bp
3. **2026-09-24T08:00:00+09:00** — Predicted up (30.47188016627277 bp), Realized up (34.74854687894942 bp), Error: 4.3 bp

## Representative Failures

1. **2026-09-03T08:00:00+09:00** — Predicted flat (0.0 bp), Realized down (-181.5087918321041 bp), Error: 181.5 bp
2. **2026-09-03T08:00:00+09:00** — Predicted flat (0.0 bp), Realized down (-181.5087918321041 bp), Error: 181.5 bp
3. **2026-09-03T08:00:00+09:00** — Predicted flat (0.0 bp), Realized down (-181.5087918321041 bp), Error: 181.5 bp

## Recommendation Summary

Review magnitude/close-error mapping in UGH engine. Review state-to-magnitude mapping — state hits are good but errors high.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
