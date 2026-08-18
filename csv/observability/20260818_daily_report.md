# FX Daily Report — 2026-08-18

Generated: 2026-08-18T11:18:56Z

## Run Summary

- **as_of_jst**: 2026-08-18T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260818T080000_v1_4f39f15ce800614a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +13.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.4 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | UP | +4.5 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-08-17T08:00:00+09:00 → 2026-08-18T08:00:00+09:00
- **Direction**: UP
- **Close change**: +13.8 bp
- **OHLC**: O=159.21 H=159.59 L=158.82 C=159.43
- **Range**: 0.77

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 25.7 | 1.9 | No |
| baseline_random_walk | False | - | 13.8 | 13.8 | No |
| baseline_simple_technical | False | - | 51.0 | 23.3 | No |
| ugh_v2_alpha | False | True | 24.0 | 3.7 | No |
| ugh_v2_beta | False | True | 20.8 | 6.8 | No |
| ugh_v2_delta | False | True | 22.3 | 5.3 | No |
| ugh_v2_gamma | False | True | 22.4 | 5.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **24.0 bp**
- Baseline direction hits: 0/3
