# FX Daily Report — 2026-08-10

Generated: 2026-08-10T11:42:29Z

## Run Summary

- **as_of_jst**: 2026-08-10T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260810T080000_v1_a1a31ac2fd0ef182
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -39.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -34.7 | - |
| ugh_v2_alpha | DOWN | -39.0 | fire |
| ugh_v2_beta | DOWN | -40.9 | fire |
| ugh_v2_delta | DOWN | -41.6 | fire |
| ugh_v2_gamma | DOWN | -37.2 | fire |

## Previous Window Outcome

- **Window**: 2026-08-07T08:00:00+09:00 → 2026-08-10T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -39.8 bp
- **OHLC**: O=158.41 H=158.57 L=157.01 C=157.78
- **Range**: 1.56

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 82.9 | 3.3 | No |
| baseline_random_walk | False | - | 39.8 | 39.8 | No |
| baseline_simple_technical | True | - | 5.0 | 5.0 | No |
| ugh_v2_alpha | True | True | 32.1 | 32.1 | No |
| ugh_v2_beta | False | True | 39.8 | 39.8 | No |
| ugh_v2_delta | False | True | 39.8 | 39.8 | No |
| ugh_v2_gamma | True | True | 32.2 | 32.2 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **32.1 bp**
- Baseline direction hits: 1/3
