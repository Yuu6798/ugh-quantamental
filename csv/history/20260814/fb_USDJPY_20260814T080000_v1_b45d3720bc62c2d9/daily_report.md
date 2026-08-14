# FX Daily Report — 2026-08-14

Generated: 2026-08-14T08:13:41Z

## Run Summary

- **as_of_jst**: 2026-08-14T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260814T080000_v1_b45d3720bc62c2d9
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +4.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.6 | - |
| ugh_v2_alpha | DOWN | -8.5 | fire |
| ugh_v2_beta | DOWN | -3.4 | setup |
| ugh_v2_delta | DOWN | -5.8 | setup |
| ugh_v2_gamma | DOWN | -7.6 | fire |

## Previous Window Outcome

- **Window**: 2026-08-13T08:00:00+09:00 → 2026-08-14T08:00:00+09:00
- **Direction**: UP
- **Close change**: +4.4 bp
- **OHLC**: O=159.41 H=159.56 L=159.01 C=159.48
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 5.7 | 5.7 | No |
| baseline_random_walk | False | - | 4.4 | 4.4 | No |
| baseline_simple_technical | False | - | 41.4 | 32.6 | No |
| ugh_v2_alpha | False | True | 12.6 | 3.8 | No |
| ugh_v2_beta | False | True | 4.4 | 4.4 | No |
| ugh_v2_delta | False | True | 9.4 | 0.7 | No |
| ugh_v2_gamma | False | True | 11.8 | 3.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **12.6 bp**
- Baseline direction hits: 1/3
