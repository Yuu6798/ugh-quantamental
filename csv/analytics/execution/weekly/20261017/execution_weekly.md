# FX Execution Report — 2026-10-12 to 2026-10-16

Generated: 2026-10-16T15:24:37.938575+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-10-12T08:00:00+09:00 to 2026-10-15T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 3 | flat=1 | 100.0% | 33.3% | -9.4 | 7.2 | 8.1 | 1.54 | -4.4 | 27.3 | -0.28 | 6,485 | -4,018 | 3,006,485 | 2,995,982 | 0.0% | 0.4% | 17.72 | 537 | 537 |
| ugh_beta_unit | 4 | 3 | flat=1 | 100.0% | 33.3% | -9.4 | 7.3 | 8.2 | 1.54 | -3.8 | 29.6 | -0.22 | 6,598 | -3,414 | 3,006,598 | 2,996,586 | 0.0% | 0.4% | 16.17 | 569 | 569 |
| ugh_consensus | 4 | 3 | no_consensus=1 | 100.0% | 33.3% | -9.4 | 7.3 | 8.2 | 1.54 | -3.8 | 29.6 | -0.22 | 6,598 | -3,414 | 3,006,598 | 2,996,586 | 0.0% | 0.4% | 16.17 | 569 | 569 |
| ugh_divergence | 4 | 0 | agree_with_technical=3;flat=1 | 100.0% | - | 0.0 | - | - | - | - | - | - | 0 | 0 | 3,000,000 | 3,000,000 | 0.0% | 0.0% | - | 0 | 0 |
| bench_gpt_m3 | 4 | 4 | - | 100.0% | 0.0% | -73.9 | 3.5 | 10.6 | 0.67 | -19.1 | 11.8 | -3.24 | 4,225 | -22,870 | 3,004,225 | 2,977,130 | 0.1% | 0.8% | 2.48 | 759 | 755 |
| bench_long | 4 | 4 | - | 100.0% | 25.0% | -11.9 | 3.1 | 10.8 | 0.58 | -3.6 | 24.1 | -0.30 | 3,733 | -4,360 | 3,003,733 | 2,995,640 | 0.1% | 0.4% | 2.13 | 758 | 759 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 2,260 | 64.5 |
| bench_long | 2,752 | 2.5 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-10-15T08:00:00+09:00, 5 ugh_x1 trades, 6 windows, 7 calendar days, 0 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 5 trades, 7 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 0.06 | >= 2.00 | no |
| 3. max drawdown (live) | 0.2% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 576 | > bench_gpt_m3 -3,141, bench_long -3,632 | yes |

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
