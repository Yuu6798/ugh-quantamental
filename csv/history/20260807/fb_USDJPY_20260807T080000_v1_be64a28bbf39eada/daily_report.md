# FX Daily Report — 2026-08-07

Generated: 2026-08-07T06:11:56Z

## Run Summary

- **as_of_jst**: 2026-08-07T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260807T080000_v1_be64a28bbf39eada
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +43.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -34.8 | - |
| ugh_v2_alpha | DOWN | -7.6 | fire |
| ugh_v2_beta | FLAT | +0.0 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | DOWN | -7.6 | fire |

## Previous Window Outcome

- **Window**: 2026-08-06T08:00:00+09:00 → 2026-08-07T08:00:00+09:00
- **Direction**: UP
- **Close change**: +43.1 bp
- **OHLC**: O=157.74 H=158.55 L=157.54 C=158.42
- **Range**: 1.01

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 44.4 | 41.8 | No |
| baseline_random_walk | False | - | 43.1 | 43.1 | No |
| baseline_simple_technical | False | - | 76.4 | 9.8 | No |
| ugh_v2_alpha | False | True | 57.9 | 28.3 | No |
| ugh_v2_beta | False | True | 51.8 | 34.4 | No |
| ugh_v2_delta | False | True | 54.6 | 31.6 | No |
| ugh_v2_gamma | False | True | 57.9 | 28.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **57.9 bp**
- Baseline direction hits: 0/3
