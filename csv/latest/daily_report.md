# FX Daily Report — 2026-08-13

Generated: 2026-08-13T08:18:54Z

## Run Summary

- **as_of_jst**: 2026-08-13T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260813T080000_v1_7732798962faff35
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +10.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.0 | - |
| ugh_v2_alpha | DOWN | -8.2 | fire |
| ugh_v2_beta | FLAT | +0.0 | fire |
| ugh_v2_delta | DOWN | -5.0 | fire |
| ugh_v2_gamma | DOWN | -7.4 | fire |

## Previous Window Outcome

- **Window**: 2026-08-12T08:00:00+09:00 → 2026-08-13T08:00:00+09:00
- **Direction**: UP
- **Close change**: +10.0 bp
- **OHLC**: O=159.25 H=159.54 L=158.67 C=159.41
- **Range**: 0.87

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 7.5 | 7.5 | No |
| baseline_random_walk | False | - | 10.0 | 10.0 | No |
| baseline_simple_technical | False | - | 46.6 | 26.5 | No |
| ugh_v2_alpha | False | True | 20.1 | 0.0 | No |
| ugh_v2_beta | False | True | 14.8 | 5.3 | No |
| ugh_v2_delta | False | True | 17.5 | 2.6 | No |
| ugh_v2_gamma | False | True | 19.2 | 0.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **20.1 bp**
- Baseline direction hits: 1/3
