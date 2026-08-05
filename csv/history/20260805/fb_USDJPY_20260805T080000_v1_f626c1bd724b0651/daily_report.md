# FX Daily Report — 2026-08-05

Generated: 2026-08-05T09:35:18Z

## Run Summary

- **as_of_jst**: 2026-08-05T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260805T080000_v1_f626c1bd724b0651
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +35.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -34.8 | - |
| ugh_v2_alpha | DOWN | -6.6 | fire |
| ugh_v2_beta | FLAT | +0.0 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | DOWN | -6.6 | fire |

## Previous Window Outcome

- **Window**: 2026-08-04T08:00:00+09:00 → 2026-08-05T08:00:00+09:00
- **Direction**: UP
- **Close change**: +35.0 bp
- **OHLC**: O=157.17 H=157.95 L=157.15 C=157.72
- **Range**: 0.80

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 39.4 | 30.5 | No |
| baseline_random_walk | False | - | 35.0 | 35.0 | No |
| baseline_simple_technical | False | - | 68.0 | 2.0 | No |
| ugh_v2_alpha | False | True | 52.0 | 18.0 | No |
| ugh_v2_beta | False | True | 46.0 | 24.0 | No |
| ugh_v2_delta | False | True | 48.7 | 21.3 | No |
| ugh_v2_gamma | False | True | 52.0 | 18.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **52.0 bp**
- Baseline direction hits: 0/3
