# FX Daily Report — 2026-04-23

Generated: 2026-04-23T07:01:51Z

## Run Summary

- **as_of_jst**: 2026-04-23T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260423T080000_v1_a11ec9330b252b95
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +7.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -23.5 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-22T08:00:00+09:00 → 2026-04-23T08:00:00+09:00
- **Direction**: UP
- **Close change**: +7.5 bp
- **OHLC**: O=159.36 H=159.57 L=159.08 C=159.48
- **Range**: 0.49

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 30.9 | 30.9 | No |
| baseline_random_walk | False | - | 7.5 | 7.5 | No |
| baseline_simple_technical | False | - | 33.1 | 18.1 | No |
| ugh | False | True | 7.6 | 7.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **7.6 bp**
- Baseline direction hits: 1/3
