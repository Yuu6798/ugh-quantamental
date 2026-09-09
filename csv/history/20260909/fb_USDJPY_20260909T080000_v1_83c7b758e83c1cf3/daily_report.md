# FX Daily Report — 2026-09-09

Generated: 2026-09-09T12:23:18Z

## Run Summary

- **as_of_jst**: 2026-09-09T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260909T080000_v1_83c7b758e83c1cf3
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -25.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.7 | - |
| ugh_v2_alpha | DOWN | -39.8 | fire |
| ugh_v2_beta | DOWN | -35.4 | fire |
| ugh_v2_delta | DOWN | -37.5 | fire |
| ugh_v2_gamma | DOWN | -39.8 | fire |

## Previous Window Outcome

- **Window**: 2026-09-08T08:00:00+09:00 → 2026-09-09T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -25.3 bp
- **OHLC**: O=154.35 H=154.41 L=152.87 C=153.96
- **Range**: 1.54

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 76.7 | 76.7 | No |
| baseline_random_walk | False | - | 25.3 | 25.3 | No |
| baseline_simple_technical | True | - | 11.3 | 11.3 | No |
| ugh_v2_alpha | True | True | 31.9 | 31.9 | No |
| ugh_v2_beta | True | True | 31.9 | 31.9 | No |
| ugh_v2_delta | True | True | 31.9 | 31.9 | No |
| ugh_v2_gamma | True | True | 31.9 | 31.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **31.9 bp**
- Baseline direction hits: 2/3
