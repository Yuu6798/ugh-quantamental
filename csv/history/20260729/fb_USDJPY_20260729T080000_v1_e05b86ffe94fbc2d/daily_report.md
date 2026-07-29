# FX Daily Report — 2026-07-29

Generated: 2026-07-29T07:47:53Z

## Run Summary

- **as_of_jst**: 2026-07-29T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260729T080000_v1_e05b86ffe94fbc2d
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +9.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +21.6 | - |
| ugh_v2_alpha | UP | +12.5 | setup |
| ugh_v2_beta | UP | +11.4 | setup |
| ugh_v2_delta | UP | +11.9 | setup |
| ugh_v2_gamma | UP | +11.6 | setup |

## Previous Window Outcome

- **Window**: 2026-07-28T08:00:00+09:00 → 2026-07-29T08:00:00+09:00
- **Direction**: UP
- **Close change**: +9.2 bp
- **OHLC**: O=163.67 H=163.94 L=163.63 C=163.82
- **Range**: 0.31

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 6.7 | 6.7 | No |
| baseline_random_walk | False | - | 9.2 | 9.2 | No |
| baseline_simple_technical | True | - | 13.8 | 13.8 | No |
| ugh_v2_alpha | True | True | 1.0 | 1.0 | No |
| ugh_v2_beta | True | True | 1.0 | 1.0 | No |
| ugh_v2_delta | True | True | 0.1 | 0.1 | No |
| ugh_v2_gamma | True | True | 0.5 | 0.5 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **1.0 bp**
- Baseline direction hits: 2/3
