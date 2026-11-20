# FX Execution Report — 2026-11-16 to 2026-11-20

Generated: 2026-11-20T19:09:54.425838+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-11-16T08:00:00+09:00 to 2026-11-19T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 4 | - | 100.0% | 25.0% | 0.7 | -7.4 | 6.4 | -2.30 | -0.5 | 15.0 | -0.06 | -8,821 | -566 | 2,991,179 | 2,999,434 | 0.3% | 0.2% | 0.00 | 751 | 752 |
| ugh_beta_unit | 4 | 4 | - | 100.0% | 25.0% | 0.7 | -7.4 | 6.4 | -2.30 | -0.5 | 15.0 | -0.06 | -8,821 | -566 | 2,991,179 | 2,999,434 | 0.3% | 0.2% | 0.00 | 751 | 752 |
| ugh_consensus | 4 | 4 | - | 100.0% | 25.0% | 0.7 | -7.4 | 6.4 | -2.30 | -0.5 | 15.0 | -0.06 | -8,821 | -566 | 2,991,179 | 2,999,434 | 0.3% | 0.2% | 0.00 | 751 | 752 |
| ugh_divergence | 4 | 0 | agree_with_technical=4 | 100.0% | - | 0.0 | - | - | - | - | - | - | 0 | 0 | 3,000,000 | 3,000,000 | 0.0% | 0.0% | - | 0 | 0 |
| bench_gpt_m3 | 4 | 4 | - | 100.0% | 25.0% | -38.3 | -0.4 | 10.1 | -0.08 | -10.2 | 10.1 | -2.01 | -500 | -12,216 | 2,999,500 | 2,987,784 | 0.1% | 0.4% | 0.88 | 751 | 752 |
| bench_long | 4 | 4 | - | 100.0% | 25.0% | 0.7 | -7.4 | 6.4 | -2.30 | -0.5 | 15.0 | -0.06 | -8,821 | -566 | 2,991,179 | 2,999,434 | 0.3% | 0.2% | 0.00 | 751 | 752 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | -8,321 | 38.9 |
| bench_long | 0 | 0.0 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-11-19T08:00:00+09:00, 22 ugh_x1 trades, 30 windows, 42 calendar days, 1 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 22 trades, 42 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 0.58 | >= 2.00 | no |
| 3. max drawdown (live) | 0.5% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 12,363 | > bench_gpt_m3 -54,355, bench_long 10,619 | yes |

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
