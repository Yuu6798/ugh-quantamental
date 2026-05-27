# FX Daily Report — 2026-05-27

Generated: 2026-05-27T08:42:48Z

## Run Summary

- **as_of_jst**: 2026-05-27T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260527T080000_v1_083973637f0f60a9
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +25.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.8 | - |
| ugh_v2_alpha | UP | +21.1 | dormant |
| ugh_v2_beta | UP | +22.2 | dormant |
| ugh_v2_delta | UP | +22.1 | dormant |
| ugh_v2_gamma | UP | +19.1 | dormant |

## Previous Window Outcome

- **Window**: 2026-05-26T08:00:00+09:00 → 2026-05-27T08:00:00+09:00
- **Direction**: UP
- **Close change**: +25.2 bp
- **OHLC**: O=158.89 H=159.38 L=158.81 C=159.29
- **Range**: 0.57

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 25.8 | 24.5 | No |
| baseline_random_walk | False | - | 25.2 | 25.2 | No |
| baseline_simple_technical | True | - | 13.0 | 13.0 | No |
| ugh_v2_alpha | True | True | 11.0 | 11.0 | No |
| ugh_v2_beta | True | True | 13.7 | 13.7 | No |
| ugh_v2_delta | True | True | 12.1 | 12.1 | No |
| ugh_v2_gamma | True | True | 11.9 | 11.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **11.0 bp**
- Baseline direction hits: 1/3
