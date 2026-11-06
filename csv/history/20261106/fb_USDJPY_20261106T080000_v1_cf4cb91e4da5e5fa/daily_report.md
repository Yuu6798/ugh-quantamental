# FX Daily Report — 2026-11-06

Generated: 2026-11-06T18:07:49Z

## Run Summary

- **as_of_jst**: 2026-11-06T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261106T080000_v1_cf4cb91e4da5e5fa
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -46.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | DOWN | -3.8 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-11-05T08:00:00+09:00 → 2026-11-06T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -46.1 bp
- **OHLC**: O=158.39 H=158.49 L=157.52 C=157.66
- **Range**: 0.97

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 31.0 | 31.0 | No |
| baseline_random_walk | False | - | 46.1 | 46.1 | No |
| baseline_simple_technical | False | - | 68.3 | 23.9 | No |
| ugh_v2_alpha | False | True | 46.1 | 46.1 | No |
| ugh_v2_beta | False | True | 46.1 | 46.1 | No |
| ugh_v2_delta | False | True | 46.1 | 46.1 | No |
| ugh_v2_gamma | False | True | 46.1 | 46.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **46.1 bp**
- Baseline direction hits: 1/3
