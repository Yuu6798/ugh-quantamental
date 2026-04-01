# FX Monthly Review v1 — USDJPY

Generated: 2026-04-01T08:00:00+09:00
Window: 20 business days requested, 7 included, 13 missing

## Monthly Summary

> Review state-to-magnitude mapping — state hits are good but errors high. Investigate missing protocol windows.

## Review Flags

- **inspect_state_mapping**: State proxy hit rate (100.0%) is high but magnitude error (40.3 bp) exceeds threshold (30.0 bp). State-to-magnitude mapping may need review.
- **missing_windows**: Missing window rate (65.0%) exceeds threshold (25%). Missing: 13/20.

## Strategy Performance

| Strategy | N | Dir Hit | Dir Rate | Range Rate | State Rate | Mean Err | Med Err | Mean Mag | Med Mag |
|---|---|---|---|---|---|---|---|---|---|
| ugh | 7 | 5 | 71.4% | 42.9% | 100.0% | 40.4 | 40.5 | 40.3 | 40.5 |
| baseline_random_walk | 7 | 0 | 0.0% | - | - | 40.5 | 40.7 | 40.5 | 40.7 |
| baseline_prev_day_direction | 7 | 3 | 42.9% | - | - | 81.8 | 51.3 | 32.2 | 31.5 |
| baseline_simple_technical | 7 | 5 | 71.4% | - | - | 36.8 | 25.2 | 22.2 | 19.3 |

## Baseline Comparisons (delta vs UGH)

| Baseline | Dir Acc Delta | Close Err Delta | Mag Err Delta | State Delta |
|---|---|---|---|---|
| baseline_random_walk | -0.71 | +0.11 bp | +0.24 bp | - |
| baseline_prev_day_direction | -0.29 | +41.44 bp | -8.05 bp | - |
| baseline_simple_technical | 0.00 | -3.57 bp | -18.10 bp | - |

## State Metrics (UGH)

| State | N | Dir Rate | Mean Err |
|---|---|---|---|
| setup | 7 | 71.4% | 40.4 |

## Regime Analysis (UGH, confirmed annotations)

| Regime | N | Dir Rate | Mean Err |
|---|---|---|---|
| choppy | 2 | 0.0% | 30.4 |
| trending | 5 | 100.0% | 44.4 |

## Volatility Analysis (UGH, confirmed annotations)

| Volatility | N | Dir Rate | Mean Err |
|---|---|---|---|
| high | 1 | 100.0% | 96.2 |
| low | 2 | 50.0% | 13.8 |
| normal | 4 | 75.0% | 39.8 |

## Intervention Risk Analysis (UGH, confirmed annotations)

| Intervention Risk | N | Dir Rate | Mean Err |
|---|---|---|---|
| low | 6 | 66.7% | 31.1 |
| medium | 1 | 100.0% | 96.2 |

## Event Tag Analysis (UGH, confirmed annotations)

| Event Tag | N | Dir Rate | Mean Err |
|---|---|---|---|
| boj_pm_rift | 1 | 100.0% | 20.5 |
| geopolitical_shock | 1 | 0.0% | 49.9 |
| hawkish_fed | 1 | 100.0% | 48.3 |
| intervention_warning | 2 | 100.0% | 30.5 |
| oil_retreat | 1 | 100.0% | 16.8 |
| ppi_us | 1 | 100.0% | 48.3 |
| us_iran | 4 | 75.0% | 38.9 |

## Provider Health Summary

- **Total runs**: 14
- **Success**: 4
- **Failed**: 0
- **Skipped**: 10
- **Fallback adjustments**: 1
- **Lagged snapshots**: 1
- **Providers**: alpha_vantage (14)

## Annotation Coverage

- **Total observations**: 28
- **Confirmed**: 28
- **Pending**: 0
- **Unlabeled**: 0
- **Coverage rate**: 100.0%

## Representative Successes

1. **2026-03-24T08:00:00+09:00** — Predicted up (0.233875 bp), Realized up (17.044378511458255 bp), Error: 16.8 bp
2. **2026-03-26T08:00:00+09:00** — Predicted up (0.233875 bp), Realized up (20.693547375682734 bp), Error: 20.5 bp
3. **2026-03-27T08:00:00+09:00** — Predicted up (0.233875 bp), Realized up (40.71151196292156 bp), Error: 40.5 bp

## Representative Failures

1. **2026-03-23T08:00:00+09:00** — Predicted up (0.233875 bp), Realized down (-49.616882301217935 bp), Error: 49.9 bp
2. **2026-03-30T08:00:00+09:00** — Predicted up (0.233875 bp), Realized down (-10.632309712926856 bp), Error: 10.9 bp

## Recommendation Summary

Review state-to-magnitude mapping — state hits are good but errors high. Investigate missing protocol windows.

---

*This report is generated from persisted CSV artifacts only. No forecast logic was re-executed. Internal UGH/baseline/engine logic is unchanged.*
