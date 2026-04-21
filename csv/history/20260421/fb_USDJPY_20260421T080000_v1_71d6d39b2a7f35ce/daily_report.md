# FX Daily Report — 2026-04-21

Generated: 2026-04-21T11:51:02Z

## Run Summary

- **as_of_jst**: 2026-04-21T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260421T080000_v1_71d6d39b2a7f35ce
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +12.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -24.5 | - |
| ugh | DOWN | -0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-04-20T08:00:00+09:00 → 2026-04-21T08:00:00+09:00
- **Direction**: UP
- **Close change**: +12.6 bp
- **OHLC**: O=158.59 H=159.20 L=158.54 C=158.79
- **Range**: 0.66

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 44.7 | 19.4 | No |
| baseline_random_walk | False | - | 12.6 | 12.6 | No |
| baseline_simple_technical | False | - | 39.0 | 13.8 | No |
| ugh | False | True | 12.8 | 12.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **12.8 bp**
- Baseline direction hits: 0/3
