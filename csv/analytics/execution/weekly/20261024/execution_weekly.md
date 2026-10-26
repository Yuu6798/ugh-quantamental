# FX Execution Report — 2026-10-19 to 2026-10-23

Generated: 2026-10-26T12:44:06.699986+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-10-19T08:00:00+09:00 to 2026-10-22T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 2 | flat=2 | 100.0% | 50.0% | 12.7 | 9.4 | 10.2 | - | 5.7 | 36.7 | - | 5,652 | 3,418 | 3,005,652 | 3,003,418 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_beta_unit | 4 | 2 | flat=2 | 100.0% | 50.0% | 12.7 | 9.4 | 10.2 | - | 5.7 | 36.7 | - | 5,652 | 3,418 | 3,005,652 | 3,003,418 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_consensus | 4 | 3 | no_consensus=1 | 100.0% | 33.3% | -73.9 | 4.7 | 10.9 | 0.74 | -10.7 | 38.5 | -0.48 | 4,216 | -9,687 | 3,004,216 | 2,990,313 | 0.0% | 0.6% | 3.93 | 475 | 475 |
| ugh_divergence | 4 | 0 | agree_with_technical=2;flat=2 | 100.0% | - | 0.0 | - | - | - | - | - | - | 0 | 0 | 3,000,000 | 3,000,000 | 0.0% | 0.0% | - | 0 | 0 |
| bench_gpt_m3 | 4 | 4 | - | 100.0% | 25.0% | -100.6 | -7.6 | 8.1 | -1.88 | -25.8 | 46.2 | -1.12 | -9,081 | -30,922 | 2,990,919 | 2,969,078 | 0.3% | 1.0% | 0.02 | 759 | 757 |
| bench_long | 4 | 4 | - | 100.0% | 25.0% | -75.2 | 2.5 | 10.8 | 0.46 | -19.4 | 50.1 | -0.78 | 2,969 | -23,357 | 3,002,969 | 2,976,643 | 0.1% | 1.1% | 2.03 | 761 | 760 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 14,733 | 113.3 |
| bench_long | 2,684 | 87.9 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-10-22T08:00:00+09:00, 7 ugh_x1 trades, 11 windows, 14 calendar days, 1 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 7 trades, 14 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 0.62 | >= 2.00 | no |
| 3. max drawdown (live) | 0.2% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 6,230 | > bench_gpt_m3 -12,212, bench_long -211 | yes |

Passed: no
Blocked reasons: none

## Archive inventory (blocking)

- incomplete_batches: 0
- missing_evaluations: 0
- incomplete_decision_batches: 0
- missing_decisions: 0
- missing_live: 0
- duplicate_batches: 0

### Archive defects (report only, never block)

- incomplete_batches: 0
- missing_evaluations: 0
- incomplete_decision_batches: 0
- missing_decisions: 0
- missing_live: 0
- duplicate_batches: 0

## Notes

- Generated from persisted execution_evaluation.csv archives only.
- Live series: entry_status == live rows; bar series: every row incl. backfill.
- Gate cohort: current execution_version, live rows, complete batches, all history.
