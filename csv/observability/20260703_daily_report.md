# FX Daily Report — 2026-07-03

Generated: 2026-07-03T08:15:06Z

## Run Summary

- **as_of_jst**: 2026-07-03T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260703T080000_v1_60e52bdbb98d1417
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -92.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +18.6 | - |
| ugh_v2_alpha | FLAT | +0.0 | failure |
| ugh_v2_beta | FLAT | +0.0 | failure |
| ugh_v2_delta | FLAT | +0.0 | failure |
| ugh_v2_gamma | FLAT | +0.0 | failure |

## Previous Window Outcome

- **Window**: 2026-07-02T08:00:00+09:00 → 2026-07-03T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -92.9 bp
- **OHLC**: O=162.60 H=162.60 L=160.62 C=161.09
- **Range**: 1.98

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 95.3 | 90.4 | No |
| baseline_random_walk | False | - | 92.9 | 92.9 | No |
| baseline_simple_technical | False | - | 106.9 | 78.9 | No |
| ugh_v2_alpha | False | False | 98.9 | 86.9 | No |
| ugh_v2_beta | False | False | 97.7 | 88.0 | No |
| ugh_v2_delta | False | False | 98.2 | 87.5 | No |
| ugh_v2_gamma | False | False | 98.5 | 87.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **98.9 bp**
- Baseline direction hits: 0/3
