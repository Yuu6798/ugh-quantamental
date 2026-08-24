# FX Daily Report — 2026-08-24

Generated: 2026-08-24T05:43:18Z

## Run Summary

- **as_of_jst**: 2026-08-24T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260824T080000_v1_2649dcb9f5d67a20
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -5.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -41.2 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-08-21T08:00:00+09:00 → 2026-08-24T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -5.0 bp
- **OHLC**: O=159.01 H=159.13 L=158.33 C=158.93
- **Range**: 0.80

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 61.3 | 51.2 | No |
| baseline_random_walk | False | - | 5.0 | 5.0 | No |
| baseline_simple_technical | True | - | 36.0 | 36.0 | No |
| ugh_v2_alpha | False | True | 9.4 | 0.7 | No |
| ugh_v2_beta | False | True | 17.0 | 6.9 | No |
| ugh_v2_delta | False | True | 13.2 | 3.2 | No |
| ugh_v2_gamma | False | True | 9.4 | 0.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **9.4 bp**
- Baseline direction hits: 1/3
