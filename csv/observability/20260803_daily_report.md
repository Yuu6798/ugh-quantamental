# FX Daily Report — 2026-08-03

Generated: 2026-08-03T13:34:57Z

## Run Summary

- **as_of_jst**: 2026-08-03T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260803T080000_v1_648ae165480de09a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -119.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -35.1 | - |
| ugh_v2_alpha | DOWN | -22.5 | fire |
| ugh_v2_beta | DOWN | -26.0 | fire |
| ugh_v2_delta | DOWN | -23.8 | fire |
| ugh_v2_gamma | DOWN | -22.4 | fire |

## Previous Window Outcome

- **Window**: 2026-07-31T08:00:00+09:00 → 2026-08-03T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -119.1 bp
- **OHLC**: O=159.47 H=160.87 L=157.57 C=157.57
- **Range**: 3.30

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 117.7 | 117.7 | No |
| baseline_random_walk | False | - | 119.1 | 119.1 | No |
| baseline_simple_technical | False | - | 149.1 | 89.2 | No |
| ugh_v2_alpha | False | False | 119.1 | 119.1 | No |
| ugh_v2_beta | True | False | 111.5 | 111.5 | No |
| ugh_v2_delta | True | False | 113.9 | 113.9 | No |
| ugh_v2_gamma | False | False | 119.1 | 119.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **119.1 bp**
- Baseline direction hits: 1/3
