# FX Daily Report — 2026-04-16

Generated: 2026-04-16T06:57:47Z

## Run Summary

- **as_of_jst**: 2026-04-16T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260416T080000_v1_cf9e66323d033dd9
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +10.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -35.7 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-15T08:00:00+09:00 → 2026-04-16T08:00:00+09:00
- **Direction**: UP
- **Close change**: +10.1 bp
- **OHLC**: O=158.80 H=159.15 L=158.63 C=158.96
- **Range**: 0.52

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 52.1 | 31.9 | No |
| baseline_random_walk | False | - | 10.1 | 10.1 | No |
| baseline_simple_technical | False | - | 47.9 | 27.7 | No |
| ugh | False | True | 10.2 | 9.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **10.2 bp**
- Baseline direction hits: 0/3
