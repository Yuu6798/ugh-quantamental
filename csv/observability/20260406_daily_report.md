# FX Daily Report — 2026-04-06

Generated: 2026-04-06T08:22:08Z

## Run Summary

- **as_of_jst**: 2026-04-06T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260406T080000_v1_a479e1859ebdecc5
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -3.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.5 | - |
| ugh | DOWN | -0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-04-03T08:00:00+09:00 → 2026-04-06T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -3.8 bp
- **OHLC**: O=159.62 H=159.71 L=159.41 C=159.56
- **Range**: 0.30

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 54.8 | 47.3 | No |
| baseline_random_walk | False | - | 3.8 | 3.8 | No |
| baseline_simple_technical | False | - | 42.9 | 35.4 | No |
| ugh | False | True | 3.8 | 3.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **3.8 bp**
- Baseline direction hits: 0/3
