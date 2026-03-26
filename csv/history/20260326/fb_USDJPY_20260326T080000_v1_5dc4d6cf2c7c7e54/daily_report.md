# FX Daily Report — 2026-03-26

Generated: 2026-03-26T08:02:05Z

## Run Summary

- **as_of_jst**: 2026-03-26T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260326T080000_v1_5dc4d6cf2c7c7e54
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +48.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +40.0 | - |
| ugh | UP | +0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-03-25T08:00:00+09:00 → 2026-03-26T08:00:00+09:00
- **Direction**: UP
- **Close change**: +48.5 bp
- **OHLC**: O=158.69 H=159.50 L=158.55 C=159.46
- **Range**: 0.95

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 31.5 | 31.5 | No |
| baseline_random_walk | False | - | 48.5 | 48.5 | No |
| baseline_simple_technical | True | - | 9.5 | 9.5 | No |
| ugh | True | False | 48.3 | 48.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **48.3 bp**
- Baseline direction hits: 2/3
