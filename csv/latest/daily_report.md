# FX Daily Report — 2026-06-16

Generated: 2026-06-16T12:11:12Z

## Run Summary

- **as_of_jst**: 2026-06-16T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260616T080000_v1_93e63ad07577f528
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +6.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.0 | - |
| ugh_v2_alpha | UP | +6.0 | setup |
| ugh_v2_beta | UP | +6.1 | setup |
| ugh_v2_delta | UP | +6.0 | setup |
| ugh_v2_gamma | UP | +5.7 | setup |

## Previous Window Outcome

- **Window**: 2026-06-15T08:00:00+09:00 → 2026-06-16T08:00:00+09:00
- **Direction**: UP
- **Close change**: +6.2 bp
- **OHLC**: O=160.22 H=160.39 L=159.72 C=160.32
- **Range**: 0.67

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 11.9 | 11.9 | No |
| baseline_random_walk | False | - | 6.2 | 6.2 | No |
| baseline_simple_technical | True | - | 7.4 | 7.4 | No |
| ugh_v2_alpha | True | True | 0.0 | 0.0 | No |
| ugh_v2_beta | True | True | 1.4 | 1.4 | No |
| ugh_v2_delta | True | True | 0.7 | 0.7 | No |
| ugh_v2_gamma | True | True | 0.4 | 0.4 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **0.0 bp**
- Baseline direction hits: 2/3
