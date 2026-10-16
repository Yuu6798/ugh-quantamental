# FX Daily Report — 2026-10-16

Generated: 2026-10-16T09:57:34Z

## Run Summary

- **as_of_jst**: 2026-10-16T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261016T080000_v1_74868d2d2f3a33fb
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -20.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +27.1 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-10-15T08:00:00+09:00 → 2026-10-16T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -20.8 bp
- **OHLC**: O=158.31 H=158.33 L=157.53 C=157.98
- **Range**: 0.80

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 18.3 | 18.3 | No |
| baseline_random_walk | False | - | 20.8 | 20.8 | No |
| baseline_simple_technical | False | - | 47.8 | 6.1 | No |
| ugh_v2_alpha | False | True | 26.5 | 15.2 | No |
| ugh_v2_beta | False | True | 24.9 | 16.8 | No |
| ugh_v2_delta | False | True | 25.8 | 15.9 | No |
| ugh_v2_gamma | False | True | 26.1 | 15.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **26.5 bp**
- Baseline direction hits: 1/3
