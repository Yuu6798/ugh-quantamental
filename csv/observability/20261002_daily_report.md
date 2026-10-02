# FX Daily Report — 2026-10-02

Generated: 2026-10-02T13:57:16Z

## Run Summary

- **as_of_jst**: 2026-10-02T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261002T080000_v1_5ed787f2ad3d3db3
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +42.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +43.5 | - |
| ugh_v2_alpha | UP | +25.9 | fire |
| ugh_v2_beta | UP | +28.6 | fire |
| ugh_v2_delta | UP | +28.3 | fire |
| ugh_v2_gamma | UP | +24.2 | fire |

## Previous Window Outcome

- **Window**: 2026-10-01T08:00:00+09:00 → 2026-10-02T08:00:00+09:00
- **Direction**: UP
- **Close change**: +42.6 bp
- **OHLC**: O=157.40 H=158.45 L=157.31 C=158.07
- **Range**: 1.14

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 38.1 | 38.1 | No |
| baseline_random_walk | False | - | 42.6 | 42.6 | No |
| baseline_simple_technical | True | - | 7.9 | 7.9 | No |
| ugh_v2_alpha | True | True | 22.7 | 22.7 | No |
| ugh_v2_beta | True | True | 27.6 | 27.6 | No |
| ugh_v2_delta | True | True | 24.5 | 24.5 | No |
| ugh_v2_gamma | True | True | 23.9 | 23.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **22.7 bp**
- Baseline direction hits: 2/3
