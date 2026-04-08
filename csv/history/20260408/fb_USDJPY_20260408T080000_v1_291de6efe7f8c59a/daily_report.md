# FX Daily Report — 2026-04-08

Generated: 2026-04-08T06:21:35Z

## Run Summary

- **as_of_jst**: 2026-04-08T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260408T080000_v1_291de6efe7f8c59a
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -3.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +37.6 | - |
| ugh | DOWN | -0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-04-07T08:00:00+09:00 → 2026-04-08T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -3.8 bp
- **OHLC**: O=159.67 H=160.03 L=159.45 C=159.61
- **Range**: 0.58

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 15.7 | 8.2 | No |
| baseline_random_walk | False | - | 3.8 | 3.8 | No |
| baseline_simple_technical | False | - | 42.4 | 34.9 | No |
| ugh | True | True | 3.6 | 3.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.6 bp**
- Baseline direction hits: 0/3
