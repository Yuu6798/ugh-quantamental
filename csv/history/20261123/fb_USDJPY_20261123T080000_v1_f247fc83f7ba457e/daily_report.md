# FX Daily Report — 2026-11-23

Generated: 2026-11-23T19:20:11Z

## Run Summary

- **as_of_jst**: 2026-11-23T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261123T080000_v1_f247fc83f7ba457e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -72.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +27.6 | - |
| ugh_v2_alpha | FLAT | +0.0 | failure |
| ugh_v2_beta | FLAT | +0.0 | failure |
| ugh_v2_delta | FLAT | +0.0 | failure |
| ugh_v2_gamma | FLAT | +0.0 | failure |

## Previous Window Outcome

- **Window**: 2026-11-20T08:00:00+09:00 → 2026-11-23T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -72.6 bp
- **OHLC**: O=159.69 H=159.83 L=158.40 C=158.53
- **Range**: 1.43

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 94.0 | 51.3 | No |
| baseline_random_walk | False | - | 72.6 | 72.6 | No |
| baseline_simple_technical | False | - | 97.0 | 48.3 | No |
| ugh_v2_alpha | False | False | 85.1 | 60.2 | No |
| ugh_v2_beta | False | False | 85.9 | 59.4 | No |
| ugh_v2_delta | False | False | 85.5 | 59.8 | No |
| ugh_v2_gamma | False | False | 84.2 | 61.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **85.1 bp**
- Baseline direction hits: 0/3
