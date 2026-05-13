# FX Daily Report — 2026-05-13

Generated: 2026-05-13T13:08:16Z

## Run Summary

- **as_of_jst**: 2026-05-13T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260513T080000_v1_3e1c8c6a94e04c03
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +29.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -38.7 | - |
| ugh_v2_alpha | DOWN | -3.4 | setup |
| ugh_v2_beta | UP | +1.6 | setup |
| ugh_v2_delta | DOWN | -1.1 | setup |
| ugh_v2_gamma | DOWN | -3.2 | setup |

## Previous Window Outcome

- **Window**: 2026-05-12T08:00:00+09:00 → 2026-05-13T08:00:00+09:00
- **Direction**: UP
- **Close change**: +29.3 bp
- **OHLC**: O=157.15 H=157.76 L=157.04 C=157.61
- **Range**: 0.72

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 20.0 | 20.0 | No |
| baseline_random_walk | False | - | 29.3 | 29.3 | No |
| baseline_simple_technical | False | - | 68.6 | 10.1 | No |
| ugh_v2_alpha | False | True | 31.9 | 26.7 | No |
| ugh_v2_beta | True | True | 26.0 | 26.0 | No |
| ugh_v2_delta | True | True | 29.0 | 29.0 | No |
| ugh_v2_gamma | False | True | 31.6 | 26.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **31.9 bp**
- Baseline direction hits: 1/3
