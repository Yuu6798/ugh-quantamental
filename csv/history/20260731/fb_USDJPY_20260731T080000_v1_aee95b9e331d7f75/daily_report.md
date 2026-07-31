# FX Daily Report — 2026-07-31

Generated: 2026-07-31T07:55:37Z

## Run Summary

- **as_of_jst**: 2026-07-31T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260731T080000_v1_aee95b9e331d7f75
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -236.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +30.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | failure |
| ugh_v2_beta | DOWN | -7.7 | failure |
| ugh_v2_delta | DOWN | -5.2 | failure |
| ugh_v2_gamma | FLAT | +0.0 | failure |

## Previous Window Outcome

- **Window**: 2026-07-30T08:00:00+09:00 → 2026-07-31T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -236.9 bp
- **OHLC**: O=163.38 H=163.73 L=157.96 C=159.51
- **Range**: 5.77

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 210.0 | 210.0 | No |
| baseline_random_walk | False | - | 236.9 | 236.9 | No |
| baseline_simple_technical | False | - | 259.7 | 214.1 | No |
| ugh_v2_alpha | False | False | 243.3 | 230.5 | No |
| ugh_v2_beta | False | False | 236.9 | 236.9 | No |
| ugh_v2_delta | False | False | 236.9 | 236.9 | No |
| ugh_v2_gamma | False | False | 243.0 | 230.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **243.3 bp**
- Baseline direction hits: 1/3
