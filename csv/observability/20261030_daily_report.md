# FX Daily Report — 2026-10-30

Generated: 2026-10-30T17:03:32Z

## Run Summary

- **as_of_jst**: 2026-10-30T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261030T080000_v1_4f41403798fb9fc2
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -7.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -20.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-10-29T08:00:00+09:00 → 2026-10-30T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -7.0 bp
- **OHLC**: O=157.80 H=158.12 L=157.58 C=157.69
- **Range**: 0.54

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 1.3 | 1.3 | No |
| baseline_random_walk | False | - | 7.0 | 7.0 | No |
| baseline_simple_technical | True | - | 14.8 | 14.8 | No |
| ugh_v2_alpha | True | True | 3.6 | 3.6 | No |
| ugh_v2_beta | True | True | 3.6 | 3.6 | No |
| ugh_v2_delta | True | True | 3.4 | 3.4 | No |
| ugh_v2_gamma | True | True | 3.8 | 3.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.6 bp**
- Baseline direction hits: 2/3
