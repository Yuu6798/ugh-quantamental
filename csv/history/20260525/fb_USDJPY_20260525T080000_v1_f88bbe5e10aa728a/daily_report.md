# FX Daily Report — 2026-05-25

Generated: 2026-05-25T11:09:38Z

## Run Summary

- **as_of_jst**: 2026-05-25T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260525T080000_v1_f88bbe5e10aa728a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +15.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.7 | - |
| ugh_v2_alpha | UP | +19.8 | setup |
| ugh_v2_beta | UP | +18.9 | setup |
| ugh_v2_delta | UP | +19.4 | setup |
| ugh_v2_gamma | UP | +18.3 | setup |

## Previous Window Outcome

- **Window**: 2026-05-22T08:00:00+09:00 → 2026-05-25T08:00:00+09:00
- **Direction**: UP
- **Close change**: +15.1 bp
- **OHLC**: O=158.95 H=159.23 L=158.87 C=159.19
- **Range**: 0.36

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 10.1 | 10.1 | No |
| baseline_random_walk | False | - | 15.1 | 15.1 | No |
| baseline_simple_technical | True | - | 23.5 | 23.5 | No |
| ugh_v2_alpha | True | True | 1.7 | 1.7 | No |
| ugh_v2_beta | True | True | 0.5 | 0.5 | No |
| ugh_v2_delta | True | True | 0.6 | 0.6 | No |
| ugh_v2_gamma | True | True | 0.5 | 0.5 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **1.7 bp**
- Baseline direction hits: 2/3
