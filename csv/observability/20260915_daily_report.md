# FX Daily Report — 2026-09-15

Generated: 2026-09-15T10:12:06Z

## Run Summary

- **as_of_jst**: 2026-09-15T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260915T080000_v1_a9c6d767d941d483
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +63.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -45.9 | - |
| ugh_v2_alpha | DOWN | -7.2 | fire |
| ugh_v2_beta | UP | +5.1 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | DOWN | -6.7 | fire |

## Previous Window Outcome

- **Window**: 2026-09-14T08:00:00+09:00 → 2026-09-15T08:00:00+09:00
- **Direction**: UP
- **Close change**: +63.9 bp
- **OHLC**: O=153.37 H=154.99 L=153.29 C=154.35
- **Range**: 1.70

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 118.3 | 9.5 | No |
| baseline_random_walk | False | - | 63.9 | 63.9 | No |
| baseline_simple_technical | False | - | 107.3 | 20.5 | No |
| ugh_v2_alpha | False | True | 120.2 | 7.6 | No |
| ugh_v2_beta | False | True | 120.2 | 7.6 | No |
| ugh_v2_delta | False | True | 120.2 | 7.6 | No |
| ugh_v2_gamma | False | True | 118.3 | 9.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **120.2 bp**
- Baseline direction hits: 0/3
