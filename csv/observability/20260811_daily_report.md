# FX Daily Report — 2026-08-11

Generated: 2026-08-11T05:57:11Z

## Run Summary

- **as_of_jst**: 2026-08-11T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260811T080000_v1_d6436feda414565c
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +98.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | fire |
| ugh_v2_beta | UP | +4.6 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | FLAT | +0.0 | fire |

## Previous Window Outcome

- **Window**: 2026-08-10T08:00:00+09:00 → 2026-08-11T08:00:00+09:00
- **Direction**: UP
- **Close change**: +98.9 bp
- **OHLC**: O=157.74 H=159.36 L=157.60 C=159.30
- **Range**: 1.76

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 138.7 | 59.1 | No |
| baseline_random_walk | False | - | 98.9 | 98.9 | No |
| baseline_simple_technical | False | - | 133.6 | 64.2 | No |
| ugh_v2_alpha | False | False | 137.9 | 59.9 | No |
| ugh_v2_beta | False | False | 139.8 | 58.0 | No |
| ugh_v2_delta | False | False | 140.5 | 57.3 | No |
| ugh_v2_gamma | False | False | 136.1 | 61.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **137.9 bp**
- Baseline direction hits: 0/3
