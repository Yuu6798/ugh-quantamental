# FX Daily Report — 2026-03-25

Generated: 2026-03-25T07:52:07Z

## Run Summary

- **as_of_jst**: 2026-03-25T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260325T080000_v1_a299e8fb64a5c586
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +17.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +39.0 | - |
| ugh | UP | +0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-03-24T08:00:00+09:00 → 2026-03-25T08:00:00+09:00
- **Direction**: UP
- **Close change**: +17.0 bp
- **OHLC**: O=158.41 H=159.18 L=158.25 C=158.68
- **Range**: 0.93

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 66.7 | 32.6 | No |
| baseline_random_walk | False | - | 17.0 | 17.0 | No |
| baseline_simple_technical | True | - | 25.2 | 25.2 | No |
| ugh | True | True | 16.8 | 16.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **16.8 bp**
- Baseline direction hits: 1/3
