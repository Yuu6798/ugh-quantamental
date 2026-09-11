# FX Daily Report — 2026-09-11

Generated: 2026-09-11T09:51:32Z

## Run Summary

- **as_of_jst**: 2026-09-11T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260911T080000_v1_b784d911d25e38fd
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +56.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -41.3 | - |
| ugh_v2_alpha | DOWN | -8.0 | fire |
| ugh_v2_beta | FLAT | +0.0 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | DOWN | -7.8 | fire |

## Previous Window Outcome

- **Window**: 2026-09-10T08:00:00+09:00 → 2026-09-11T08:00:00+09:00
- **Direction**: UP
- **Close change**: +56.0 bp
- **OHLC**: O=153.56 H=154.65 L=153.26 C=154.42
- **Range**: 1.39

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 85.2 | 26.8 | No |
| baseline_random_walk | False | - | 56.0 | 56.0 | No |
| baseline_simple_technical | False | - | 94.7 | 17.3 | No |
| ugh_v2_alpha | False | True | 101.3 | 10.7 | No |
| ugh_v2_beta | False | True | 97.3 | 14.7 | No |
| ugh_v2_delta | False | True | 99.2 | 12.9 | No |
| ugh_v2_gamma | False | True | 101.3 | 10.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **101.3 bp**
- Baseline direction hits: 0/3
