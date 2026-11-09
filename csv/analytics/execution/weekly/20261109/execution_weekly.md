# FX Execution Report — 2026-11-02 to 2026-11-06

Generated: 2026-11-09T07:30:05.392665+00:00
Current execution_version: x1
Rows in window: 24 (4 complete batches)

## Stratum execution_version=x1

Windows: 4 (2026-11-02T08:00:00+09:00 to 2026-11-05T08:00:00+09:00)

### Books

| Book | Decisions | Trades | Skips | Live cov | Hit rate | Capture (bp) | Live mean (bp) | Live sd | Live t | Bar mean (bp) | Bar sd | Bar t | P&L live (JPY) | P&L bar (JPY) | Equity live | Equity bar | Max DD live | Max DD bar | PF live | Cost live | Cost bar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ugh_x1 | 4 | 2 | flat=2 | 100.0% | 50.0% | 31.1 | 18.5 | 13.9 | - | 14.9 | 43.4 | - | 11,119 | 8,928 | 3,011,119 | 3,008,928 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_beta_unit | 4 | 2 | flat=2 | 100.0% | 50.0% | 31.1 | 18.5 | 13.9 | - | 14.9 | 43.4 | - | 11,119 | 8,928 | 3,011,119 | 3,008,928 | 0.0% | 0.2% | - | 380 | 380 |
| ugh_consensus | 4 | 0 | no_consensus=4 | 100.0% | - | 0.0 | - | - | - | - | - | - | 0 | 0 | 3,000,000 | 3,000,000 | 0.0% | 0.0% | - | 0 | 0 |
| ugh_divergence | 4 | 2 | flat=2 | 100.0% | 50.0% | 31.1 | 18.5 | 13.9 | - | 14.9 | 43.4 | - | 11,119 | 8,928 | 3,011,119 | 3,008,928 | 0.0% | 0.2% | - | 380 | 380 |
| bench_gpt_m3 | 4 | 4 | - | 100.0% | 25.0% | -76.3 | -16.3 | 30.2 | -1.08 | -19.7 | 36.5 | -1.08 | -19,586 | -23,644 | 2,980,414 | 2,976,356 | 0.7% | 1.1% | 0.21 | 758 | 759 |
| bench_long | 4 | 4 | - | 100.0% | 50.0% | 16.1 | -1.9 | 35.2 | -0.11 | 3.4 | 42.4 | 0.16 | -2,278 | 4,001 | 2,997,722 | 3,004,001 | 0.5% | 0.6% | 0.86 | 760 | 762 |

### Benchmark deltas (ugh_x1 minus benchmark)

| Benchmark | P&L live delta (JPY) | Capture delta (bp) |
|---|---|---|
| bench_gpt_m3 | 30,705 | 107.4 |
| bench_long | 13,397 | 15.0 |

## Acceptance gate (execution_version=x1, cumulative live cohort)

Cohort: 2026-10-08T08:00:00+09:00 to 2026-11-05T08:00:00+09:00, 12 ugh_x1 trades, 20 windows, 28 calendar days, 1 excluded days

| Criterion | Current | Threshold | Met |
|---|---|---|---|
| 1. ugh_x1 trades and observation span | 12 trades, 28 calendar days | >= 100 trades and >= 182 calendar days | no |
| 2. t-statistic of live daily return | 1.83 | >= 2.00 | no |
| 3. max drawdown (live) | 0.2% | <= 10.0% | yes |
| 4. ugh_x1 live P&L beats both benchmarks | 24,964 | > bench_gpt_m3 -35,756, bench_long 5,283 | yes |

Passed: no
Blocked reasons: missing_evaluations

## Archive inventory (blocking)

- incomplete_batches: 0
- missing_evaluations: 1: {"forecast_batch_id": "fb_USDJPY_20261106T080000_v1_cf4cb91e4da5e5fa", "execution_version": "x1", "as_of_jst": "2026-11-06T08:00:00+09:00", "window_end_jst": "2026-11-09T08:00:00+09:00"}
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
