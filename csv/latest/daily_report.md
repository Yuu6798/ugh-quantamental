# FX Daily Report — 2026-11-16

Generated: 2026-11-16T21:07:45Z

## Run Summary

- **as_of_jst**: 2026-11-16T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261116T080000_v1_ab8c82ac01c5932a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -10.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +29.2 | - |
| ugh_v2_alpha | UP | +6.8 | setup |
| ugh_v2_beta | UP | +3.3 | setup |
| ugh_v2_delta | UP | +5.0 | setup |
| ugh_v2_gamma | UP | +6.5 | setup |

## Previous Window Outcome

- **Window**: 2026-11-13T08:00:00+09:00 → 2026-11-16T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -10.6 bp
- **OHLC**: O=159.83 H=160.18 L=159.50 C=159.66
- **Range**: 0.68

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 15.6 | 5.6 | No |
| baseline_random_walk | False | - | 10.6 | 10.6 | No |
| baseline_simple_technical | False | - | 39.3 | 18.1 | No |
| ugh_v2_alpha | False | True | 20.6 | 0.7 | No |
| ugh_v2_beta | False | True | 18.6 | 2.7 | No |
| ugh_v2_delta | False | True | 19.3 | 1.9 | No |
| ugh_v2_gamma | False | True | 20.3 | 1.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **20.6 bp**
- Baseline direction hits: 0/3
