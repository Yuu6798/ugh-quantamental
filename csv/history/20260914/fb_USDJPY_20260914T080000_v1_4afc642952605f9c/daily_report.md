# FX Daily Report — 2026-09-14

Generated: 2026-09-14T10:48:48Z

## Run Summary

- **as_of_jst**: 2026-09-14T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260914T080000_v1_4afc642952605f9c
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -54.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -43.4 | - |
| ugh_v2_alpha | DOWN | -56.3 | fire |
| ugh_v2_beta | DOWN | -56.3 | fire |
| ugh_v2_delta | DOWN | -56.3 | fire |
| ugh_v2_gamma | DOWN | -54.4 | fire |

## Previous Window Outcome

- **Window**: 2026-09-11T08:00:00+09:00 → 2026-09-14T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -54.4 bp
- **OHLC**: O=154.38 H=154.61 L=153.23 C=153.54
- **Range**: 1.38

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 110.4 | 1.6 | No |
| baseline_random_walk | False | - | 54.4 | 54.4 | No |
| baseline_simple_technical | True | - | 13.1 | 13.1 | No |
| ugh_v2_alpha | True | True | 46.4 | 46.4 | No |
| ugh_v2_beta | False | True | 54.4 | 54.4 | No |
| ugh_v2_delta | False | True | 54.4 | 54.4 | No |
| ugh_v2_gamma | True | True | 46.7 | 46.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **46.4 bp**
- Baseline direction hits: 1/3
