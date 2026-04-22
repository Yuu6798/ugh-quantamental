# FX Daily Report — 2026-04-22

Generated: 2026-04-22T11:49:05Z

## Run Summary

- **as_of_jst**: 2026-04-22T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260422T080000_v1_f79bbd2c0fd7b3ee
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +38.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -25.6 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-21T08:00:00+09:00 → 2026-04-22T08:00:00+09:00
- **Direction**: UP
- **Close change**: +38.4 bp
- **OHLC**: O=158.76 H=159.64 L=158.66 C=159.37
- **Range**: 0.98

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 25.8 | 25.8 | No |
| baseline_random_walk | False | - | 38.4 | 38.4 | No |
| baseline_simple_technical | False | - | 63.0 | 13.9 | No |
| ugh | False | False | 38.6 | 38.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **38.6 bp**
- Baseline direction hits: 1/3
