# FX Daily Report — 2026-07-30

Generated: 2026-07-30T07:38:10Z

## Run Summary

- **as_of_jst**: 2026-07-30T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260730T080000_v1_9d36e17977388e27
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -26.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +22.8 | - |
| ugh_v2_alpha | UP | +6.4 | failure |
| ugh_v2_beta | FLAT | +0.0 | failure |
| ugh_v2_delta | FLAT | +0.0 | failure |
| ugh_v2_gamma | UP | +6.1 | failure |

## Previous Window Outcome

- **Window**: 2026-07-29T08:00:00+09:00 → 2026-07-30T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -26.9 bp
- **OHLC**: O=163.82 H=163.90 L=163.22 C=163.38
- **Range**: 0.68

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 36.0 | 17.7 | No |
| baseline_random_walk | False | - | 26.9 | 26.9 | No |
| baseline_simple_technical | False | - | 48.4 | 5.3 | No |
| ugh_v2_alpha | False | False | 39.3 | 14.4 | No |
| ugh_v2_beta | False | False | 38.3 | 15.5 | No |
| ugh_v2_delta | False | False | 38.8 | 14.9 | No |
| ugh_v2_gamma | False | False | 38.5 | 15.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **39.3 bp**
- Baseline direction hits: 0/3
