# FX Daily Report — 2026-10-06

Generated: 2026-10-06T17:18:11Z

## Run Summary

- **as_of_jst**: 2026-10-06T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261006T080000_v1_69899624622335fa
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +27.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +39.4 | - |
| ugh_v2_alpha | UP | +25.2 | setup |
| ugh_v2_beta | UP | +24.7 | setup |
| ugh_v2_delta | UP | +25.4 | setup |
| ugh_v2_gamma | UP | +23.3 | setup |

## Previous Window Outcome

- **Window**: 2026-10-05T08:00:00+09:00 → 2026-10-06T08:00:00+09:00
- **Direction**: UP
- **Close change**: +27.3 bp
- **OHLC**: O=157.47 H=158.29 L=157.41 C=157.90
- **Range**: 0.88

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 45.0 | 9.6 | No |
| baseline_random_walk | False | - | 27.3 | 27.3 | No |
| baseline_simple_technical | True | - | 15.8 | 15.8 | No |
| ugh_v2_alpha | True | True | 14.9 | 14.9 | No |
| ugh_v2_beta | True | True | 20.5 | 20.5 | No |
| ugh_v2_delta | True | True | 17.7 | 17.7 | No |
| ugh_v2_gamma | True | True | 15.6 | 15.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **14.9 bp**
- Baseline direction hits: 1/3
