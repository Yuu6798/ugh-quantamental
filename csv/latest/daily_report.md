# FX Daily Report — 2026-04-20

Generated: 2026-04-20T11:58:58Z

## Run Summary

- **as_of_jst**: 2026-04-20T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260420T080000_v1_41ea4270d8a0ddc0
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -32.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -26.4 | - |
| ugh | DOWN | -0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-04-17T08:00:00+09:00 → 2026-04-20T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -32.1 bp
- **OHLC**: O=159.12 H=159.52 L=157.57 C=158.61
- **Range**: 1.95

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 43.4 | 20.7 | No |
| baseline_random_walk | False | - | 32.1 | 32.1 | No |
| baseline_simple_technical | True | - | 2.5 | 2.5 | No |
| ugh | True | False | 31.9 | 31.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **31.9 bp**
- Baseline direction hits: 1/3
