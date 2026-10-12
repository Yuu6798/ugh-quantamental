# FX Daily Report — 2026-10-12

Generated: 2026-10-12T20:20:34Z

## Run Summary

- **as_of_jst**: 2026-10-12T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261012T080000_v1_f6423be7a9d3fd3d
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +28.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +33.6 | - |
| ugh_v2_alpha | UP | +15.2 | setup |
| ugh_v2_beta | UP | +17.7 | setup |
| ugh_v2_delta | UP | +16.8 | setup |
| ugh_v2_gamma | UP | +13.9 | setup |

## Previous Window Outcome

- **Window**: 2026-10-09T08:00:00+09:00 → 2026-10-12T08:00:00+09:00
- **Direction**: UP
- **Close change**: +28.5 bp
- **OHLC**: O=157.86 H=158.42 L=157.74 C=158.31
- **Range**: 0.68

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 39.3 | 17.7 | No |
| baseline_random_walk | False | - | 28.5 | 28.5 | No |
| baseline_simple_technical | True | - | 6.4 | 6.4 | No |
| ugh_v2_alpha | True | True | 18.6 | 18.6 | No |
| ugh_v2_beta | True | True | 22.5 | 22.5 | No |
| ugh_v2_delta | True | True | 20.5 | 20.5 | No |
| ugh_v2_gamma | True | True | 19.2 | 19.2 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **18.6 bp**
- Baseline direction hits: 1/3
