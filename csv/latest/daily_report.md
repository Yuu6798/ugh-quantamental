# FX Daily Report — 2026-04-10

Generated: 2026-04-10T11:37:53Z

## Run Summary

- **as_of_jst**: 2026-04-10T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260410T080000_v1_596f7a0242396983
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +24.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +37.7 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-09T08:00:00+09:00 → 2026-04-10T08:00:00+09:00
- **Direction**: UP
- **Close change**: +24.6 bp
- **OHLC**: O=158.55 H=159.29 L=158.43 C=158.94
- **Range**: 0.86

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 83.5 | 34.3 | No |
| baseline_random_walk | False | - | 24.6 | 24.6 | No |
| baseline_simple_technical | True | - | 13.1 | 13.1 | No |
| ugh | False | True | 24.6 | 24.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **24.6 bp**
- Baseline direction hits: 1/3
