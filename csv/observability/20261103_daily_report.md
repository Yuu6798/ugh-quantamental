# FX Daily Report — 2026-11-03

Generated: 2026-11-03T18:29:36Z

## Run Summary

- **as_of_jst**: 2026-11-03T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261103T080000_v1_5bc918db205a954e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +31.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -19.7 | - |
| ugh_v2_alpha | FLAT | +0.0 | failure |
| ugh_v2_beta | UP | +5.2 | failure |
| ugh_v2_delta | UP | +4.0 | failure |
| ugh_v2_gamma | FLAT | +0.0 | failure |

## Previous Window Outcome

- **Window**: 2026-11-02T08:00:00+09:00 → 2026-11-03T08:00:00+09:00
- **Direction**: UP
- **Close change**: +31.1 bp
- **OHLC**: O=157.45 H=157.99 L=157.43 C=157.94
- **Range**: 0.56

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 39.4 | 22.9 | No |
| baseline_random_walk | False | - | 31.1 | 31.1 | No |
| baseline_simple_technical | False | - | 50.7 | 11.6 | No |
| ugh_v2_alpha | False | True | 31.1 | 31.1 | No |
| ugh_v2_beta | False | True | 31.1 | 31.1 | No |
| ugh_v2_delta | False | True | 31.1 | 31.1 | No |
| ugh_v2_gamma | False | True | 31.1 | 31.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **31.1 bp**
- Baseline direction hits: 0/3
