# FX Execution Report — 2026-10-05 to 2026-10-09

Generated: 2026-10-09T17:28:46.512239+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-10-05T08:00:00+09:00 to 2026-10-08T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 4 | - | 25.0% | 50.0% | 24.1 | -21.6 | - | - | 3.5 | 12.0 | 0.59 | -6,481 | 4,248 | 2,993,519 | 3,004,248 | 0.2% | 0.1% | 0.00 | 153 | 579 |
| ugh_beta_unit | 4 | 4 | - | 25.0% | 50.0% | 24.1 | -26.8 | - | - | 5.4 | 16.4 | 0.66 | -8,037 | 6,478 | 2,991,963 | 3,006,478 | 0.3% | 0.1% | 0.00 | 190 | 762 |
| ugh_consensus | 4 | 4 | - | 25.0% | 50.0% | 24.1 | -26.8 | - | - | 5.4 | 16.4 | 0.66 | -8,037 | 6,478 | 2,991,963 | 3,006,478 | 0.3% | 0.1% | 0.00 | 190 | 762 |
| ugh_divergence | 4 | 0 | agree_with_technical=4 | 25.0% | - | 0.0 | - | - | - | - | - | - | 0 | 0 | 3,000,000 | 3,000,000 | 0.0% | 0.0% | - | 0 | 0 |
| bench_gpt_m3 | 4 | 4 | - | 25.0% | 50.0% | 24.1 | -26.8 | - | - | 5.4 | 16.4 | 0.66 | -8,037 | 6,478 | 2,991,963 | 3,006,478 | 0.3% | 0.1% | 0.00 | 190 | 762 |
| bench_long | 4 | 4 | - | 25.0% | 50.0% | 24.1 | -26.8 | - | - | 5.4 | 16.4 | 0.66 | -8,037 | 6,478 | 2,991,963 | 3,006,478 | 0.3% | 0.1% | 0.00 | 190 | 762 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 1,556 | 0.0 |
| bench_long | 1,556 | 0.0 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-10-08T08:00:00+09:00, 1 ugh_x1 trades, 1 windows, 0 calendar days, 0 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 1 trades, 0 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | - | >= 2.00 | no |
| 3. max drawdown (live) | 0.2% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | -6,481 | > bench_gpt_m3 -8,037, bench_long -8,037 | yes |

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
