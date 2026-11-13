# FX Execution Report — 2026-11-09 to 2026-11-13

Generated: 2026-11-13T18:36:10.147772+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-11-09T08:00:00+09:00 to 2026-11-12T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 4 | - | 100.0% | 50.0% | -8.6 | 3.8 | 24.1 | 0.32 | -2.8 | 50.1 | -0.11 | 4,528 | -3,440 | 3,004,528 | 2,996,560 | 0.3% | 0.8% | 1.59 | 755 | 754 |
| ugh_beta_unit | 4 | 4 | - | 100.0% | 50.0% | -8.6 | 3.8 | 24.1 | 0.32 | -2.8 | 50.1 | -0.11 | 4,528 | -3,440 | 3,004,528 | 2,996,560 | 0.3% | 0.8% | 1.59 | 755 | 754 |
| ugh_consensus | 4 | 3 | no_consensus=1 | 100.0% | 66.7% | 44.0 | 12.3 | 20.9 | 1.02 | 14.0 | 45.5 | 0.53 | 11,048 | 12,586 | 3,011,048 | 3,012,586 | 0.0% | 0.3% | 10.38 | 567 | 566 |
| ugh_divergence | 4 | 1 | agree_with_technical=3 | 100.0% | 0.0% | -52.6 | -21.7 | - | - | -53.2 | - | - | -6,496 | -15,959 | 2,993,504 | 2,984,041 | 0.2% | 0.5% | 0.00 | 189 | 190 |
| bench_gpt_m3 | 4 | 4 | - | 100.0% | 50.0% | -86.5 | -12.8 | 20.2 | -1.27 | -22.3 | 43.5 | -1.02 | -15,360 | -26,714 | 2,984,640 | 2,973,286 | 0.6% | 1.2% | 0.13 | 754 | 754 |
| bench_long | 4 | 4 | - | 100.0% | 75.0% | 96.6 | 14.3 | 17.5 | 1.63 | 23.5 | 41.7 | 1.13 | 17,188 | 28,231 | 3,017,188 | 3,028,231 | 0.0% | 0.3% | 15.60 | 757 | 758 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 19,889 | 78.0 |
| bench_long | -12,660 | -105.1 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-11-12T08:00:00+09:00, 17 ugh_x1 trades, 25 windows, 35 calendar days, 1 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 17 trades, 35 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 1.38 | >= 2.00 | no |
| 3. max drawdown (live) | 0.3% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 26,697 | > bench_gpt_m3 -48,549, bench_long 24,945 | yes |

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
