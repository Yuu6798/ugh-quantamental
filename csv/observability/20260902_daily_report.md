# FX Daily Report — 2026-09-02

Generated: 2026-09-02T09:24:47Z

## Run Summary

- **as_of_jst**: 2026-09-02T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260902T080000_v1_9516cacd55386e72
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +27.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +25.7 | - |
| ugh_v2_alpha | UP | +13.5 | setup |
| ugh_v2_beta | UP | +16.6 | setup |
| ugh_v2_delta | UP | +15.2 | setup |
| ugh_v2_gamma | UP | +12.5 | setup |

## Previous Window Outcome

- **Window**: 2026-09-01T08:00:00+09:00 → 2026-09-02T08:00:00+09:00
- **Direction**: UP
- **Close change**: +27.5 bp
- **OHLC**: O=159.73 H=160.27 L=159.62 C=160.17
- **Range**: 0.65

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 47.5 | 7.6 | No |
| baseline_random_walk | False | - | 27.5 | 27.5 | No |
| baseline_simple_technical | True | - | 1.4 | 1.4 | No |
| ugh_v2_alpha | True | True | 22.8 | 22.8 | No |
| ugh_v2_beta | False | True | 27.5 | 27.5 | No |
| ugh_v2_delta | False | True | 27.5 | 27.5 | No |
| ugh_v2_gamma | True | True | 22.9 | 22.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **22.8 bp**
- Baseline direction hits: 1/3
