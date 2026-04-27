# FX Daily Report — 2026-04-27

Generated: 2026-04-27T09:16:31Z

## Run Summary

- **as_of_jst**: 2026-04-27T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260427T080000_v1_5f1d01574074396c
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -14.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +21.9 | - |
| ugh | UP | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-04-24T08:00:00+09:00 → 2026-04-27T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -14.4 bp
- **OHLC**: O=159.60 H=159.84 L=159.29 C=159.37
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 28.2 | 0.6 | No |
| baseline_random_walk | False | - | 14.4 | 14.4 | No |
| baseline_simple_technical | True | - | 8.8 | 8.8 | No |
| ugh | True | True | 14.3 | 14.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **14.3 bp**
- Baseline direction hits: 1/3
