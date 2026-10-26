# FX Execution Report — 2026-10-19 to 2026-10-23

Generated: 2026-10-26T05:39:52.825442+00:00
Current execution_version: x1
Rows in window: 18 (3 complete batches)

## Stratum execution_version=x1

Windows: 3 (2026-10-19T08:00:00+09:00 to 2026-10-21T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 3 | 2 | flat=1 | 100.0% | 50.0% | 12.7 | 9.4 | 10.2 | - | 5.7 | 36.7 | - | 5,652 | 3,418 | 3,005,652 | 3,003,418 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_beta_unit | 3 | 2 | flat=1 | 100.0% | 50.0% | 12.7 | 9.4 | 10.2 | - | 5.7 | 36.7 | - | 5,652 | 3,418 | 3,005,652 | 3,003,418 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_consensus | 3 | 2 | no_consensus=1 | 100.0% | 50.0% | 12.7 | 9.4 | 10.2 | - | 5.7 | 36.7 | - | 5,652 | 3,418 | 3,005,652 | 3,003,418 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_divergence | 3 | 0 | agree_with_technical=2;flat=1 | 100.0% | - | 0.0 | - | - | - | - | - | - | 0 | 0 | 3,000,000 | 3,000,000 | 0.0% | 0.0% | - | 0 | 0 |
| bench_gpt_m3 | 3 | 3 | - | 100.0% | 33.3% | -14.0 | -6.9 | 9.7 | -1.23 | -5.3 | 26.1 | -0.35 | -6,219 | -4,783 | 2,993,781 | 2,995,217 | 0.2% | 0.3% | 0.03 | 568 | 568 |
| bench_long | 3 | 3 | - | 100.0% | 33.3% | 11.5 | 6.5 | 8.8 | 1.28 | 3.2 | 26.3 | 0.21 | 5,842 | 2,849 | 3,005,842 | 3,002,849 | 0.0% | 0.2% | - | 570 | 570 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 11,871 | 26.7 |
| bench_long | -190 | 1.3 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-10-21T08:00:00+09:00, 7 ugh_x1 trades, 10 windows, 13 calendar days, 1 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 7 trades, 13 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 0.62 | >= 2.00 | no |
| 3. max drawdown (live) | 0.2% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 6,230 | > bench_gpt_m3 -9,353, bench_long 2,659 | yes |

Passed: no
Blocked reasons: missing_evaluations

## Archive inventory (blocking)

- incomplete_batches: 0
- missing_evaluations: 1: {"forecast_batch_id": "fb_USDJPY_20261022T080000_v1_5182871dd92a86c0", "execution_version": "x1", "as_of_jst": "2026-10-22T08:00:00+09:00", "window_end_jst": "2026-10-23T08:00:00+09:00"}
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
