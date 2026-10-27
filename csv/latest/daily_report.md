# FX Daily Report — 2026-10-27

Generated: 2026-10-27T13:22:11Z

## Run Summary

- **as_of_jst**: 2026-10-27T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261027T080000_v1_43f3d6c3cd139ded
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +44.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -20.7 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | UP | +5.0 | setup |
| ugh_v2_delta | UP | +3.4 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-10-26T08:00:00+09:00 → 2026-10-27T08:00:00+09:00
- **Direction**: UP
- **Close change**: +44.0 bp
- **OHLC**: O=156.81 H=157.64 L=156.63 C=157.50
- **Range**: 1.01

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 37.6 | 37.6 | No |
| baseline_random_walk | False | - | 44.0 | 44.0 | No |
| baseline_simple_technical | False | - | 63.2 | 24.8 | No |
| ugh_v2_alpha | False | True | 44.0 | 44.0 | No |
| ugh_v2_beta | False | True | 44.0 | 44.0 | No |
| ugh_v2_delta | False | True | 44.0 | 44.0 | No |
| ugh_v2_gamma | False | True | 44.0 | 44.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **44.0 bp**
- Baseline direction hits: 1/3
