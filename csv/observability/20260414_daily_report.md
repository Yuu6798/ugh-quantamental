# FX Daily Report — 2026-04-14

Generated: 2026-04-14T06:53:39Z

## Run Summary

- **as_of_jst**: 2026-04-14T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260414T080000_v1_a3f817cd14360220
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +0.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.0 | - |
| ugh | DOWN | -0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-04-13T08:00:00+09:00 → 2026-04-14T08:00:00+09:00
- **Direction**: UP
- **Close change**: +0.6 bp
- **OHLC**: O=159.43 H=159.86 L=159.27 C=159.44
- **Range**: 0.59

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 20.8 | 20.8 | No |
| baseline_random_walk | False | - | 0.6 | 0.6 | No |
| baseline_simple_technical | True | - | 37.0 | 37.0 | No |
| ugh | False | True | 0.8 | 0.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **0.8 bp**
- Baseline direction hits: 2/3
