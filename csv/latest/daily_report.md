# FX Daily Report — 2026-08-06

Generated: 2026-08-06T12:52:48Z

## Run Summary

- **as_of_jst**: 2026-08-06T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260806T080000_v1_f5a938afcbcfbf8c
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -1.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -33.3 | - |
| ugh_v2_alpha | DOWN | -14.8 | fire |
| ugh_v2_beta | DOWN | -8.7 | fire |
| ugh_v2_delta | DOWN | -11.5 | fire |
| ugh_v2_gamma | DOWN | -14.8 | fire |

## Previous Window Outcome

- **Window**: 2026-08-05T08:00:00+09:00 → 2026-08-06T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -1.3 bp
- **OHLC**: O=157.76 H=157.87 L=157.27 C=157.74
- **Range**: 0.60

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 36.3 | 33.7 | No |
| baseline_random_walk | False | - | 1.3 | 1.3 | No |
| baseline_simple_technical | True | - | 33.5 | 33.5 | No |
| ugh_v2_alpha | True | True | 5.3 | 5.3 | No |
| ugh_v2_beta | False | True | 1.3 | 1.3 | No |
| ugh_v2_delta | False | True | 1.3 | 1.3 | No |
| ugh_v2_gamma | True | True | 5.3 | 5.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **5.3 bp**
- Baseline direction hits: 1/3
