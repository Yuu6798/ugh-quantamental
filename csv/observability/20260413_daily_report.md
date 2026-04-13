# FX Daily Report — 2026-04-13

Generated: 2026-04-13T07:14:56Z

## Run Summary

- **as_of_jst**: 2026-04-13T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260413T080000_v1_3eb3eee817795822
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +21.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +37.6 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-10T08:00:00+09:00 → 2026-04-13T08:00:00+09:00
- **Direction**: UP
- **Close change**: +21.4 bp
- **OHLC**: O=158.95 H=159.37 L=158.90 C=159.29
- **Range**: 0.47

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 3.2 | 3.2 | No |
| baseline_random_walk | False | - | 21.4 | 21.4 | No |
| baseline_simple_technical | True | - | 16.3 | 16.3 | No |
| ugh | False | True | 21.5 | 21.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **21.5 bp**
- Baseline direction hits: 2/3
