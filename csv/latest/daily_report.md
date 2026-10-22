# FX Daily Report — 2026-10-22

Generated: 2026-10-22T13:02:15Z

## Run Summary

- **as_of_jst**: 2026-10-22T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261022T080000_v1_5182871dd92a86c0
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -1.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +21.2 | - |
| ugh_v2_alpha | UP | +3.3 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | UP | +3.1 | setup |
| ugh_v2_gamma | UP | +3.2 | setup |

## Previous Window Outcome

- **Window**: 2026-10-21T08:00:00+09:00 → 2026-10-22T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -1.3 bp
- **OHLC**: O=158.15 H=158.39 L=157.82 C=158.13
- **Range**: 0.57

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 18.3 | 18.3 | No |
| baseline_random_walk | False | - | 1.3 | 1.3 | No |
| baseline_simple_technical | False | - | 25.4 | 22.9 | No |
| ugh_v2_alpha | False | True | 1.3 | 1.3 | No |
| ugh_v2_beta | False | True | 1.3 | 1.3 | No |
| ugh_v2_delta | False | True | 1.3 | 1.3 | No |
| ugh_v2_gamma | False | True | 1.3 | 1.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **1.3 bp**
- Baseline direction hits: 1/3
