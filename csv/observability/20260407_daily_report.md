# FX Daily Report — 2026-04-07

Generated: 2026-04-07T11:42:30Z

## Run Summary

- **as_of_jst**: 2026-04-07T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260407T080000_v1_1bd67b74db73fb41
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +11.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.6 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-06T08:00:00+09:00 → 2026-04-07T08:00:00+09:00
- **Direction**: UP
- **Close change**: +11.9 bp
- **OHLC**: O=159.49 H=159.82 L=159.28 C=159.68
- **Range**: 0.54

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 15.7 | 8.2 | No |
| baseline_random_walk | False | - | 11.9 | 11.9 | No |
| baseline_simple_technical | True | - | 26.6 | 26.6 | No |
| ugh | False | True | 11.9 | 11.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **11.9 bp**
- Baseline direction hits: 1/3
