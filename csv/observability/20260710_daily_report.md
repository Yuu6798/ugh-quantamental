# FX Daily Report — 2026-07-10

Generated: 2026-07-10T10:22:35Z

## Run Summary

- **as_of_jst**: 2026-07-10T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260710T080000_v1_2ecfc079b3c4d546
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -12.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +19.8 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-07-09T08:00:00+09:00 → 2026-07-10T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -12.9 bp
- **OHLC**: O=162.58 H=162.62 L=162.23 C=162.37
- **Range**: 0.39

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 43.1 | 17.3 | No |
| baseline_random_walk | False | - | 12.9 | 12.9 | No |
| baseline_simple_technical | False | - | 33.8 | 8.0 | No |
| ugh_v2_alpha | False | False | 20.7 | 5.2 | No |
| ugh_v2_beta | False | False | 24.5 | 1.4 | No |
| ugh_v2_delta | False | False | 22.8 | 3.1 | No |
| ugh_v2_gamma | False | False | 20.4 | 5.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **20.7 bp**
- Baseline direction hits: 0/3
