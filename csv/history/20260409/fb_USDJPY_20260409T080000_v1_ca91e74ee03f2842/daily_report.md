# FX Daily Report — 2026-04-09

Generated: 2026-04-09T06:22:54Z

## Run Summary

- **as_of_jst**: 2026-04-09T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260409T080000_v1_ca91e74ee03f2842
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -58.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +37.7 | - |
| ugh | DOWN | -0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-04-08T08:00:00+09:00 → 2026-04-09T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -58.9 bp
- **OHLC**: O=159.52 H=159.61 L=157.86 C=158.58
- **Range**: 1.75

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 55.2 | 55.2 | No |
| baseline_random_walk | False | - | 58.9 | 58.9 | No |
| baseline_simple_technical | False | - | 96.6 | 21.3 | No |
| ugh | True | False | 58.9 | 58.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **58.9 bp**
- Baseline direction hits: 1/3
