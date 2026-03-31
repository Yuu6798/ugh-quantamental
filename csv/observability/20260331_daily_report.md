# FX Daily Report — 2026-03-31

Generated: 2026-03-31T08:08:42Z

## Run Summary

- **as_of_jst**: 2026-03-31T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260331T080000_v1_aa21631dfb3becfe
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -10.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +37.2 | - |
| ugh | UP | +0.4 | setup |

## Previous Window Outcome

- **Window**: 2026-03-30T08:00:00+09:00 → 2026-03-31T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -10.6 bp
- **OHLC**: O=159.89 H=160.46 L=159.30 C=159.72
- **Range**: 1.16

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 51.3 | 30.1 | No |
| baseline_random_walk | False | - | 10.6 | 10.6 | No |
| baseline_simple_technical | False | - | 52.8 | 31.5 | No |
| ugh | False | False | 10.9 | 10.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **10.9 bp**
- Baseline direction hits: 0/3
