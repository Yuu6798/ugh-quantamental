# FX Daily Report — 2026-07-13

Generated: 2026-07-13T10:24:02Z

## Run Summary

- **as_of_jst**: 2026-07-13T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260713T080000_v1_a24fb334ba49f426
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -41.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +21.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | failure |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-07-10T08:00:00+09:00 → 2026-07-13T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -41.9 bp
- **OHLC**: O=162.37 H=162.42 L=161.26 C=161.69
- **Range**: 1.16

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 29.0 | 29.0 | No |
| baseline_random_walk | False | - | 41.9 | 41.9 | No |
| baseline_simple_technical | False | - | 61.7 | 22.1 | No |
| ugh_v2_alpha | False | False | 41.9 | 41.9 | No |
| ugh_v2_beta | False | False | 41.9 | 41.9 | No |
| ugh_v2_delta | False | False | 41.9 | 41.9 | No |
| ugh_v2_gamma | False | False | 41.9 | 41.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **41.9 bp**
- Baseline direction hits: 1/3
