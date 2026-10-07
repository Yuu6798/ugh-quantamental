# FX Daily Report — 2026-10-07

Generated: 2026-10-07T11:52:27Z

## Run Summary

- **as_of_jst**: 2026-10-07T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261007T080000_v1_090ac5ad69110ef6
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +9.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.6 | - |
| ugh_v2_alpha | UP | +19.9 | setup |
| ugh_v2_beta | UP | +16.5 | setup |
| ugh_v2_delta | UP | +18.1 | setup |
| ugh_v2_gamma | UP | +18.8 | setup |

## Previous Window Outcome

- **Window**: 2026-10-06T08:00:00+09:00 → 2026-10-07T08:00:00+09:00
- **Direction**: UP
- **Close change**: +9.5 bp
- **OHLC**: O=157.95 H=158.24 L=157.75 C=158.10
- **Range**: 0.49

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 17.8 | 17.8 | No |
| baseline_random_walk | False | - | 9.5 | 9.5 | No |
| baseline_simple_technical | True | - | 29.9 | 29.9 | No |
| ugh_v2_alpha | True | True | 15.7 | 15.7 | No |
| ugh_v2_beta | True | True | 15.2 | 15.2 | No |
| ugh_v2_delta | True | True | 15.9 | 15.9 | No |
| ugh_v2_gamma | True | True | 13.8 | 13.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **15.7 bp**
- Baseline direction hits: 2/3
