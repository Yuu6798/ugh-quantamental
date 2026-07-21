# FX Daily Report — 2026-07-21

Generated: 2026-07-21T07:36:36Z

## Run Summary

- **as_of_jst**: 2026-07-21T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260721T080000_v1_7fd289b62efd1f09
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +8.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +20.4 | - |
| ugh_v2_alpha | UP | +6.0 | setup |
| ugh_v2_beta | UP | +6.7 | setup |
| ugh_v2_delta | UP | +6.4 | setup |
| ugh_v2_gamma | UP | +5.5 | setup |

## Previous Window Outcome

- **Window**: 2026-07-20T08:00:00+09:00 → 2026-07-21T08:00:00+09:00
- **Direction**: UP
- **Close change**: +8.0 bp
- **OHLC**: O=162.36 H=162.59 L=162.23 C=162.49
- **Range**: 0.36

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 7.4 | 7.4 | No |
| baseline_random_walk | False | - | 8.0 | 8.0 | No |
| baseline_simple_technical | True | - | 12.9 | 12.9 | No |
| ugh_v2_alpha | True | True | 3.1 | 3.1 | No |
| ugh_v2_beta | True | True | 3.8 | 3.8 | No |
| ugh_v2_delta | True | True | 3.5 | 3.5 | No |
| ugh_v2_gamma | True | True | 3.3 | 3.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.1 bp**
- Baseline direction hits: 2/3
