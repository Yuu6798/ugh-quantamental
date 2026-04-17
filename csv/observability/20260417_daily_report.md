# FX Daily Report — 2026-04-17

Generated: 2026-04-17T06:58:29Z

## Run Summary

- **as_of_jst**: 2026-04-17T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260417T080000_v1_32530025311a79eb
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +11.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -29.6 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-16T08:00:00+09:00 → 2026-04-17T08:00:00+09:00
- **Direction**: UP
- **Close change**: +11.3 bp
- **OHLC**: O=159.00 H=159.30 L=158.25 C=159.18
- **Range**: 1.05

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 1.2 | 1.2 | No |
| baseline_random_walk | False | - | 11.3 | 11.3 | No |
| baseline_simple_technical | False | - | 47.0 | 24.4 | No |
| ugh | False | True | 11.4 | 11.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **11.4 bp**
- Baseline direction hits: 1/3
