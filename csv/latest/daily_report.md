# FX Daily Report — 2026-08-20

Generated: 2026-08-20T07:39:19Z

## Run Summary

- **as_of_jst**: 2026-08-20T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260820T080000_v1_76a56f2be2976fb8
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -90.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -40.4 | - |
| ugh_v2_alpha | DOWN | -9.2 | setup |
| ugh_v2_beta | DOWN | -13.7 | setup |
| ugh_v2_delta | DOWN | -12.0 | setup |
| ugh_v2_gamma | DOWN | -7.7 | setup |

## Previous Window Outcome

- **Window**: 2026-08-19T08:00:00+09:00 → 2026-08-20T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -90.2 bp
- **OHLC**: O=159.60 H=159.64 L=158.03 C=158.16
- **Range**: 1.61

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 104.0 | 76.4 | No |
| baseline_random_walk | False | - | 90.2 | 90.2 | No |
| baseline_simple_technical | True | - | 54.2 | 54.2 | No |
| ugh_v2_alpha | False | True | 90.2 | 90.2 | No |
| ugh_v2_beta | False | True | 95.8 | 84.7 | No |
| ugh_v2_delta | False | True | 93.8 | 86.7 | No |
| ugh_v2_gamma | False | True | 90.2 | 90.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **90.2 bp**
- Baseline direction hits: 1/3
