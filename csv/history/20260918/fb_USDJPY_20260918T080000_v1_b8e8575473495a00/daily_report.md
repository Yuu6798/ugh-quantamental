# FX Daily Report — 2026-09-18

Generated: 2026-09-18T09:54:58Z

## Run Summary

- **as_of_jst**: 2026-09-18T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260918T080000_v1_b8e8575473495a00
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -17.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -44.9 | - |
| ugh_v2_alpha | DOWN | -20.5 | fire |
| ugh_v2_beta | DOWN | -16.1 | fire |
| ugh_v2_delta | DOWN | -18.7 | fire |
| ugh_v2_gamma | DOWN | -19.3 | fire |

## Previous Window Outcome

- **Window**: 2026-09-17T08:00:00+09:00 → 2026-09-18T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -17.3 bp
- **OHLC**: O=156.23 H=156.31 L=155.32 C=155.96
- **Range**: 0.99

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 92.7 | 58.2 | No |
| baseline_random_walk | False | - | 17.3 | 17.3 | No |
| baseline_simple_technical | True | - | 29.6 | 29.6 | No |
| ugh_v2_alpha | True | True | 11.1 | 11.1 | No |
| ugh_v2_beta | False | True | 17.3 | 17.3 | No |
| ugh_v2_delta | False | True | 17.3 | 17.3 | No |
| ugh_v2_gamma | True | True | 11.6 | 11.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **11.1 bp**
- Baseline direction hits: 1/3
