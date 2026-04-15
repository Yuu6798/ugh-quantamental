# FX Daily Report — 2026-04-15

Generated: 2026-04-15T06:55:05Z

## Run Summary

- **as_of_jst**: 2026-04-15T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260415T080000_v1_146251d2ab823966
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -42.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.8 | - |
| ugh | DOWN | -0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-04-14T08:00:00+09:00 → 2026-04-15T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -42.0 bp
- **OHLC**: O=159.44 H=159.46 L=158.59 C=158.77
- **Range**: 0.87

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 42.6 | 41.4 | No |
| baseline_random_walk | False | - | 42.0 | 42.0 | No |
| baseline_simple_technical | True | - | 6.0 | 6.0 | No |
| ugh | True | False | 41.8 | 41.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **41.8 bp**
- Baseline direction hits: 1/3
