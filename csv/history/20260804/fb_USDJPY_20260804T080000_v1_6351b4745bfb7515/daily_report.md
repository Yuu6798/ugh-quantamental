# FX Daily Report — 2026-08-04

Generated: 2026-08-04T09:37:39Z

## Run Summary

- **as_of_jst**: 2026-08-04T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260804T080000_v1_6351b4745bfb7515
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -4.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -33.0 | - |
| ugh_v2_alpha | DOWN | -17.0 | fire |
| ugh_v2_beta | DOWN | -11.0 | fire |
| ugh_v2_delta | DOWN | -13.7 | fire |
| ugh_v2_gamma | DOWN | -17.0 | fire |

## Previous Window Outcome

- **Window**: 2026-08-03T08:00:00+09:00 → 2026-08-04T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -4.5 bp
- **OHLC**: O=157.23 H=157.88 L=155.21 C=157.16
- **Range**: 2.67

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 114.7 | 114.7 | No |
| baseline_random_walk | False | - | 4.5 | 4.5 | No |
| baseline_simple_technical | True | - | 30.6 | 30.6 | No |
| ugh_v2_alpha | True | True | 18.1 | 18.1 | No |
| ugh_v2_beta | True | True | 21.5 | 21.5 | No |
| ugh_v2_delta | True | True | 19.4 | 19.4 | No |
| ugh_v2_gamma | True | True | 17.9 | 17.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **18.1 bp**
- Baseline direction hits: 2/3
