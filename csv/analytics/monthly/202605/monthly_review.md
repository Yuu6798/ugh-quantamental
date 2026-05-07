# FX Monthly Review v1 — USDJPY

Generated: 2026-05-01T08:00:00+09:00
Window: 20 business days requested, 16 included, 4 missing

## Monthly Summary

> Review direction prediction logic — baseline outperforming.

## Review Flags

- **inspect_direction_logic**: UGH direction accuracy is 12.5 pct points below baseline_simple_technical (threshold: 10%). Direction logic may need review.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|
| ugh | 16 | 5 | 31.2% | 75.0% | 100.0% | 19.2 | 13.4 | 19.1 | 13.0 |
| baseline_random_walk | 16 | 0 | 0.0% | - | - | 19.2 | 13.2 | 19.2 | 13.2 |
| baseline_prev_day_direction | 16 | 7 | 43.8% | - | - | 32.8 | 29.6 | 22.2 | 20.8 |
| baseline_simple_technical | 16 | 7 | 43.8% | - | - | 35.0 | 37.2 | 19.3 | 17.2 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|
| baseline_random_walk | -0.31 | -0.04 bp | +0.11 bp | - |
| baseline_prev_day_direction | +0.12 | +13.51 bp | +3.12 bp | - |
| baseline_simple_technical | +0.12 | +15.73 bp | +0.25 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| setup | 16 | 31.2% | 19.2 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| choppy | 11 | 0.0% | 14.3 |
| trending | 5 | 100.0% | 30.1 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 1 | 100.0% | 58.9 |
| low | 10 | 20.0% | 9.1 |
| normal | 5 | 40.0% | 31.7 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 15 | 26.7% | 16.6 |
| medium | 1 | 100.0% | 58.9 |

## Provider Health Summary

- **Total runs**: 49
- **Success**: 17
- **Failed**: 0
- **Skipped**: 32
- **Fallback adjustments**: 0
- **Lagged snapshots**: 0
- **Providers**: alpha_vantage (49)

## Annotation Coverage

- **Total observations**: 64
- **Confirmed**: 64
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-04-07T08:00:00+09:00** — Predicted down (-0.12226360697890969 bp), Realized down (-3.7577503601161055 bp), Error: 3.6 bp
2. **2026-04-24T08:00:00+09:00** — Predicted down (-0.11102175107630358 bp), Realized down (-14.411027568921664 bp), Error: 14.3 bp
3. **2026-04-17T08:00:00+09:00** — Predicted down (-0.10862909684343455 bp), Realized down (-32.051282051281476 bp), Error: 31.9 bp

## Representative Failures

1. **2026-04-21T08:00:00+09:00** — Predicted down (-0.16238425545457746 bp), Realized up (38.422776518015475 bp), Error: 38.6 bp
2. **2026-04-09T08:00:00+09:00** — Predicted down (-0.04782258856483676 bp), Realized up (24.597918637652874 bp), Error: 24.6 bp
3. **2026-04-10T08:00:00+09:00** — Predicted down (-0.09656874790387807 bp), Realized up (21.39037433155102 bp), Error: 21.5 bp

## Recommendation Summary

Review direction prediction logic — baseline outperforming.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
