# FX Execution Report — 2026-10-05 to 2026-10-30

Generated: 2026-11-01T07:49:47.308058+00:00
Current execution_version: x1
Rows in window: 108 (18 complete batches)

## Stratum execution_version=x1

Windows: 18 (2026-10-05T08:00:00+09:00 to 2026-10-29T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 18 | 13 | flat=5 | 83.3% | 53.8% | 84.5 | 4.6 | 12.3 | 1.18 | 4.8 | 19.4 | 0.90 | 13,794 | 18,860 | 3,013,794 | 3,018,860 | 0.2% | 0.4% | 2.57 | 1,803 | 2,236 |
| ugh_beta_unit | 18 | 13 | flat=5 | 83.3% | 53.8% | 84.5 | 4.1 | 13.6 | 0.96 | 5.9 | 20.9 | 1.01 | 12,438 | 22,897 | 3,012,438 | 3,022,897 | 0.3% | 0.4% | 2.20 | 1,897 | 2,480 |
| ugh_consensus | 18 | 12 | no_consensus=6 | 83.3% | 50.0% | -23.7 | 3.1 | 13.7 | 0.67 | 1.0 | 24.9 | 0.14 | 8,308 | 3,605 | 3,008,308 | 3,003,605 | 0.3% | 0.7% | 1.84 | 1,612 | 2,191 |
| ugh_divergence | 18 | 2 | agree_with_technical=11;flat=5 | 83.3% | 50.0% | 21.6 | 4.5 | 15.4 | - | 10.2 | 23.3 | - | 2,682 | 6,095 | 3,002,682 | 3,006,095 | 0.1% | 0.1% | 2.40 | 381 | 381 |
| bench_gpt_m3 | 18 | 17 | momentum_zero=1 | 83.3% | 29.4% | -194.5 | -5.7 | 11.7 | -1.82 | -12.1 | 28.5 | -1.74 | -23,891 | -61,165 | 2,976,109 | 2,938,835 | 0.8% | 2.5% | 0.28 | 2,650 | 3,215 |
| bench_long | 18 | 18 | - | 83.3% | 44.4% | 24.8 | -0.0 | 12.4 | -0.01 | 0.7 | 29.9 | 0.11 | -109 | 3,799 | 2,999,891 | 3,003,799 | 0.3% | 1.2% | 0.99 | 2,847 | 3,430 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 37,685 | 279.0 |
| bench_long | 13,903 | 59.7 |

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
