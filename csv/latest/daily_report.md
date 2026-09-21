# FX Daily Report — 2026-09-21

Generated: 2026-09-21T17:07:36Z

## Run Summary

- **as_of_jst**: 2026-09-21T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260921T080000_v1_9dfc9e8e2725816c
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +60.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -47.6 | - |
| ugh_v2_alpha | FLAT | +0.0 | fire |
| ugh_v2_beta | UP | +7.6 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | FLAT | +0.0 | fire |

## Previous Window Outcome

- **Window**: 2026-09-18T08:00:00+09:00 → 2026-09-21T08:00:00+09:00
- **Direction**: UP
- **Close change**: +60.3 bp
- **OHLC**: O=155.92 H=158.05 L=155.86 C=156.86
- **Range**: 2.19

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 77.6 | 43.0 | No |
| baseline_random_walk | False | - | 60.3 | 60.3 | No |
| baseline_simple_technical | False | - | 105.2 | 15.4 | No |
| ugh_v2_alpha | False | True | 80.8 | 39.8 | No |
| ugh_v2_beta | False | True | 76.4 | 44.2 | No |
| ugh_v2_delta | False | True | 78.9 | 41.6 | No |
| ugh_v2_gamma | False | True | 79.6 | 41.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **80.8 bp**
- Baseline direction hits: 0/3
