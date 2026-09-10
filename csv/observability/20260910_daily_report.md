# FX Daily Report — 2026-09-10

Generated: 2026-09-10T12:16:40Z

## Run Summary

- **as_of_jst**: 2026-09-10T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260910T080000_v1_5ba2b35424c873b5
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -29.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -38.7 | - |
| ugh_v2_alpha | DOWN | -45.3 | fire |
| ugh_v2_beta | DOWN | -41.3 | fire |
| ugh_v2_delta | DOWN | -43.2 | fire |
| ugh_v2_gamma | DOWN | -45.3 | fire |

## Previous Window Outcome

- **Window**: 2026-09-09T08:00:00+09:00 → 2026-09-10T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -29.2 bp
- **OHLC**: O=153.99 H=153.99 L=152.92 C=153.54
- **Range**: 1.07

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 4.0 | 4.0 | No |
| baseline_random_walk | False | - | 29.2 | 29.2 | No |
| baseline_simple_technical | True | - | 8.5 | 8.5 | No |
| ugh_v2_alpha | True | True | 10.6 | 10.6 | No |
| ugh_v2_beta | True | True | 6.2 | 6.2 | No |
| ugh_v2_delta | True | True | 8.3 | 8.3 | No |
| ugh_v2_gamma | True | True | 10.6 | 10.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **10.6 bp**
- Baseline direction hits: 2/3
