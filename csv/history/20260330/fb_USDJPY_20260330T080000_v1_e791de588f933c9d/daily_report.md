# FX Daily Report — 2026-03-30

Generated: 2026-03-30T23:26:58Z

## Run Summary

- **as_of_jst**: 2026-03-30T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260330T080000_v1_e791de588f933c9d
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +40.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +42.2 | - |
| ugh | UP | +0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-03-27T08:00:00+09:00 → 2026-03-30T08:00:00+09:00
- **Direction**: UP
- **Close change**: +40.7 bp
- **OHLC**: O=159.66 H=160.41 L=159.43 C=160.31
- **Range**: 0.98

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 20.0 | 20.0 | No |
| baseline_random_walk | False | - | 40.7 | 40.7 | No |
| baseline_simple_technical | True | - | 0.4 | 0.4 | No |
| ugh | True | True | 40.5 | 40.5 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **40.5 bp**
- Baseline direction hits: 2/3
