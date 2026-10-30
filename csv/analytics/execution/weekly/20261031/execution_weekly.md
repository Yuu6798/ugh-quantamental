# FX Execution Report — 2026-10-26 to 2026-10-30

Generated: 2026-10-30T17:03:32.885716+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-10-26T08:00:00+09:00 to 2026-10-29T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 3 | flat=1 | 100.0% | 66.7% | 28.6 | 8.4 | 12.8 | 1.13 | 8.9 | 16.6 | 0.92 | 7,549 | 8,000 | 3,007,549 | 3,008,000 | 0.1% | 0.1% | 4.93 | 571 | 571 |
| ugh_beta_unit | 4 | 3 | flat=1 | 100.0% | 66.7% | 28.6 | 8.4 | 12.8 | 1.13 | 8.9 | 16.6 | 0.92 | 7,549 | 8,000 | 3,007,549 | 3,008,000 | 0.1% | 0.1% | 4.93 | 571 | 571 |
| ugh_consensus | 4 | 1 | no_consensus=3 | 100.0% | 100.0% | 7.0 | 16.2 | - | - | 6.3 | - | - | 4,862 | 1,901 | 3,004,862 | 3,001,901 | 0.0% | 0.0% | - | 190 | 190 |
| ugh_divergence | 4 | 2 | agree_with_technical=1;flat=1 | 100.0% | 50.0% | 21.6 | 4.5 | 15.4 | - | 10.2 | 23.3 | - | 2,682 | 6,095 | 3,002,682 | 3,006,095 | 0.1% | 0.1% | 2.40 | 381 | 381 |
| bench_gpt_m3 | 4 | 4 | - | 100.0% | 25.0% | -72.6 | -9.8 | 10.5 | -1.87 | -18.8 | 22.0 | -1.71 | -11,726 | -22,492 | 2,988,274 | 2,977,508 | 0.4% | 0.7% | 0.12 | 760 | 758 |
| bench_long | 4 | 4 | - | 100.0% | 50.0% | 58.6 | 0.1 | 14.8 | 0.01 | 14.0 | 25.2 | 1.11 | 103 | 16,834 | 3,000,103 | 3,016,834 | 0.2% | 0.1% | 1.01 | 762 | 765 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 19,275 | 101.1 |
| bench_long | 7,446 | -30.1 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-10-29T08:00:00+09:00, 10 ugh_x1 trades, 15 windows, 21 calendar days, 1 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 10 trades, 21 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 1.18 | >= 2.00 | no |
| 3. max drawdown (live) | 0.2% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 13,794 | > bench_gpt_m3 -23,891, bench_long -109 | yes |

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
