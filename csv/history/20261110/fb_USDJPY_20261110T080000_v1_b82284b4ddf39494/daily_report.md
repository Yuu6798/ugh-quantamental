# FX Daily Report — 2026-11-10

Generated: 2026-11-10T15:40:05Z

## Run Summary

- **as_of_jst**: 2026-11-10T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261110T080000_v1_b82284b4ddf39494
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -25.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.8 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | DOWN | -3.1 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-11-09T08:00:00+09:00 → 2026-11-10T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -25.3 bp
- **OHLC**: O=158.30 H=158.53 L=157.65 C=157.90
- **Range**: 0.88

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 74.7 | 24.2 | No |
| baseline_random_walk | False | - | 25.3 | 25.3 | No |
| baseline_simple_technical | False | - | 50.3 | 0.2 | No |
| ugh_v2_alpha | False | True | 31.6 | 18.9 | No |
| ugh_v2_beta | False | True | 34.7 | 15.8 | No |
| ugh_v2_delta | False | True | 33.3 | 17.2 | No |
| ugh_v2_gamma | False | True | 31.2 | 19.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **31.6 bp**
- Baseline direction hits: 0/3
