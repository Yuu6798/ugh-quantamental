# FX Monthly Review v1 — USDJPY

Generated: 2026-08-01T08:00:00+09:00
Window: 20 business days requested, 19 included, 1 missing

## Monthly Summary

> Review direction prediction logic — baseline outperforming.

## Review Flags

- **inspect_direction_logic**: UGH direction accuracy is 10.5 pct points below baseline_simple_technical (threshold: 10%). Direction logic may need review.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Range Rate | State Persist | State Correct | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|---|
| ugh | 0 | 0 | - | - | - | - | - | - | - | - |
| ugh_v2_alpha | 19 | 11 | 57.9% | 42.1% | 84.2% | 21.1% | 32.9 | 20.7 | 28.8 | 12.2 |
| ugh_v2_beta | 19 | 10 | 52.6% | 42.1% | 84.2% | 26.3% | 33.4 | 24.4 | 29.6 | 14.6 |
| ugh_v2_gamma | 19 | 11 | 57.9% | 42.1% | 84.2% | 21.1% | 32.7 | 20.4 | 28.8 | 11.3 |
| ugh_v2_delta | 19 | 11 | 57.9% | 42.1% | 89.5% | 26.3% | 32.8 | 22.8 | 29.1 | 13.5 |
| baseline_random_walk | 19 | 0 | 0.0% | - | - | - | 30.6 | 12.3 | 30.6 | 12.3 |
| baseline_prev_day_direction | 19 | 12 | 63.2% | - | - | - | 42.1 | 34.5 | 33.6 | 27.9 |
| baseline_simple_technical | 19 | 13 | 68.4% | - | - | - | 37.9 | 22.6 | 28.4 | 20.5 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|
| baseline_random_walk | -0.58 | -2.22 bp | +1.88 bp | - |
| baseline_prev_day_direction | +0.05 | +9.25 bp | +4.87 bp | - |
| baseline_simple_technical | +0.11 | +5.06 bp | -0.37 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| failure | 5 | 0.0% | 202.7 |
| fire | 2 | 100.0% | 18.3 |
| setup | 69 | 59.4% | 21.1 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| trending | 76 | 56.6% | 33.0 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 16 | 50.0% | 89.4 |
| low | 24 | 83.3% | 10.7 |
| normal | 36 | 41.7% | 22.7 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 4 | 0.0% | 240.0 |
| low | 68 | 63.2% | 19.6 |
| medium | 4 | 0.0% | 53.2 |

## Provider Health Summary

- **Total runs**: 60
- **Success**: 20
- **Failed**: 0
- **Skipped**: 40
- **Fallback adjustments**: 0
- **Lagged snapshots**: 0
- **Providers**: alpha_vantage (58), yahoo_finance (2)

## Annotation Coverage

- **Total observations**: 133
- **Confirmed**: 133
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-07-28T08:00:00+09:00** — Predicted up (9.058742901347895 bp), Realized up (9.164782794648115 bp), Error: 0.1 bp
2. **2026-07-28T08:00:00+09:00** — Predicted up (9.637926032663717 bp), Realized up (9.164782794648115 bp), Error: 0.5 bp
3. **2026-07-28T08:00:00+09:00** — Predicted up (10.20290668521033 bp), Realized up (9.164782794648115 bp), Error: 1.0 bp

## Representative Failures

1. **2026-07-30T08:00:00+09:00** — Predicted up (6.392735605195131 bp), Realized down (-236.8710980536176 bp), Error: 243.3 bp
2. **2026-07-30T08:00:00+09:00** — Predicted up (6.126055754012194 bp), Realized down (-236.8710980536176 bp), Error: 243.0 bp
3. **2026-07-30T08:00:00+09:00** — Predicted flat (0.0 bp), Realized down (-236.8710980536176 bp), Error: 236.9 bp

## Recommendation Summary

Review direction prediction logic — baseline outperforming.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
