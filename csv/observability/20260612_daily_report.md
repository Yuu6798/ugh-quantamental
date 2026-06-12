# FX Daily Report — 2026-06-12

Generated: 2026-06-12T13:59:43Z

## Run Summary

- **as_of_jst**: 2026-06-12T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260612T080000_v1_81ad0a2142ed88e7
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -36.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | failure |
| ugh_v2_beta | FLAT | +0.0 | failure |
| ugh_v2_delta | FLAT | +0.0 | failure |
| ugh_v2_gamma | FLAT | +0.0 | failure |

## Previous Window Outcome

- **Window**: 2026-06-11T08:00:00+09:00 → 2026-06-12T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -36.1 bp
- **OHLC**: O=160.50 H=160.59 L=159.64 C=159.92
- **Range**: 0.95

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 48.0 | 24.3 | No |
| baseline_random_walk | False | - | 36.1 | 36.1 | No |
| baseline_simple_technical | False | - | 50.0 | 22.3 | No |
| ugh_v2_alpha | False | False | 43.5 | 28.8 | No |
| ugh_v2_beta | False | False | 44.3 | 28.0 | No |
| ugh_v2_delta | False | False | 43.9 | 28.4 | No |
| ugh_v2_gamma | False | False | 43.0 | 29.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **43.5 bp**
- Baseline direction hits: 0/3
