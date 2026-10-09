# FX Daily Report — 2026-10-09

Generated: 2026-10-09T11:59:06Z

## Run Summary

- **as_of_jst**: 2026-10-09T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261009T080000_v1_d6a0ab019252135d
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -10.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +34.9 | - |
| ugh_v2_alpha | UP | +9.9 | setup |
| ugh_v2_beta | UP | +6.0 | setup |
| ugh_v2_delta | UP | +8.0 | setup |
| ugh_v2_gamma | UP | +9.4 | setup |

## Previous Window Outcome

- **Window**: 2026-10-08T08:00:00+09:00 → 2026-10-09T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -10.8 bp
- **OHLC**: O=158.03 H=158.36 L=157.51 C=157.86
- **Range**: 0.85

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 8.9 | 8.9 | No |
| baseline_random_walk | False | - | 10.8 | 10.8 | No |
| baseline_simple_technical | False | - | 48.0 | 26.4 | No |
| ugh_v2_alpha | False | True | 25.0 | 3.4 | No |
| ugh_v2_beta | False | True | 21.2 | 0.3 | No |
| ugh_v2_delta | False | True | 23.2 | 1.7 | No |
| ugh_v2_gamma | False | True | 24.1 | 2.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **25.0 bp**
- Baseline direction hits: 1/3
