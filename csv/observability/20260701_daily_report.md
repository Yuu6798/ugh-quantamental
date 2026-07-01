# FX Daily Report — 2026-07-01

Generated: 2026-07-01T10:40:45Z

## Run Summary

- **as_of_jst**: 2026-07-01T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260701T080000_v1_287d73b70f3fceed
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +37.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.3 | - |
| ugh_v2_alpha | UP | +11.2 | fire |
| ugh_v2_beta | UP | +12.3 | fire |
| ugh_v2_delta | UP | +11.8 | fire |
| ugh_v2_gamma | UP | +10.4 | fire |

## Previous Window Outcome

- **Window**: 2026-06-30T08:00:00+09:00 → 2026-07-01T08:00:00+09:00
- **Direction**: UP
- **Close change**: +37.7 bp
- **OHLC**: O=161.93 H=162.66 L=161.83 C=162.54
- **Range**: 0.83

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 23.4 | 23.4 | No |
| baseline_random_walk | False | - | 37.7 | 37.7 | No |
| baseline_simple_technical | True | - | 24.5 | 24.5 | No |
| ugh_v2_alpha | True | False | 27.2 | 27.2 | No |
| ugh_v2_beta | True | False | 25.9 | 25.9 | No |
| ugh_v2_delta | True | False | 26.5 | 26.5 | No |
| ugh_v2_gamma | True | False | 28.0 | 28.0 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **27.2 bp**
- Baseline direction hits: 2/3
