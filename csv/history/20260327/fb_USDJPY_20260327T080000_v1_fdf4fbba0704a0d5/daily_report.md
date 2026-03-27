# FX Daily Report — 2026-03-27

Generated: 2026-03-27T05:08:48Z

## Run Summary

- **as_of_jst**: 2026-03-27T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260327T080000_v1_fdf4fbba0704a0d5
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +20.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +40.3 | - |
| ugh | UP | +0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-03-26T08:00:00+09:00 → 2026-03-27T08:00:00+09:00
- **Direction**: UP
- **Close change**: +20.7 bp
- **OHLC**: O=159.47 H=159.84 L=159.26 C=159.80
- **Range**: 0.58

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 27.8 | 27.8 | No |
| baseline_random_walk | False | - | 20.7 | 20.7 | No |
| baseline_simple_technical | True | - | 19.3 | 19.3 | No |
| ugh | True | True | 20.5 | 20.5 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **20.5 bp**
- Baseline direction hits: 2/3
