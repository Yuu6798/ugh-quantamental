# FX Daily Report — 2026-06-04

Generated: 2026-06-04T08:55:38Z

## Run Summary

- **as_of_jst**: 2026-06-04T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260604T080000_v1_cacad83c37a83f0a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +8.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +18.7 | - |
| ugh_v2_alpha | UP | +9.4 | setup |
| ugh_v2_beta | UP | +8.8 | setup |
| ugh_v2_delta | UP | +9.1 | setup |
| ugh_v2_gamma | UP | +8.9 | setup |

## Previous Window Outcome

- **Window**: 2026-06-03T08:00:00+09:00 → 2026-06-04T08:00:00+09:00
- **Direction**: UP
- **Close change**: +8.8 bp
- **OHLC**: O=159.89 H=160.09 L=159.35 C=160.03
- **Range**: 0.74

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 6.3 | 6.3 | No |
| baseline_random_walk | False | - | 8.8 | 8.8 | No |
| baseline_simple_technical | True | - | 14.2 | 14.2 | No |
| ugh_v2_alpha | True | True | 4.7 | 4.7 | No |
| ugh_v2_beta | True | True | 4.7 | 4.7 | No |
| ugh_v2_delta | True | True | 4.7 | 4.7 | No |
| ugh_v2_gamma | True | True | 3.5 | 3.5 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **4.7 bp**
- Baseline direction hits: 2/3
