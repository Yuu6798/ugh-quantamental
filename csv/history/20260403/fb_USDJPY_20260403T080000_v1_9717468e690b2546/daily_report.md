# FX Daily Report — 2026-04-03

Generated: 2026-04-03T08:01:58Z

## Run Summary

- **as_of_jst**: 2026-04-03T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260403T080000_v1_9717468e690b2546
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +51.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +39.2 | - |
| ugh | UP | +0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-02T08:00:00+09:00 → 2026-04-03T08:00:00+09:00
- **Direction**: UP
- **Close change**: +51.0 bp
- **OHLC**: O=158.78 H=159.74 L=158.52 C=159.59
- **Range**: 1.22

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 46.0 | 46.0 | No |
| baseline_random_walk | False | - | 51.0 | 51.0 | No |
| baseline_simple_technical | True | - | 12.7 | 12.7 | No |
| ugh | True | False | 50.9 | 50.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **50.9 bp**
- Baseline direction hits: 2/3
