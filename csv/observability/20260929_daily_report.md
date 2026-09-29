# FX Daily Report — 2026-09-29

Generated: 2026-09-29T14:09:01Z

## Run Summary

- **as_of_jst**: 2026-09-29T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260929T080000_v1_3d2ef0ae6c2d1dc2
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +1.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +1.2 | - |
| ugh_v2_alpha | FLAT | +0.0 | fire |
| ugh_v2_beta | FLAT | +0.0 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | FLAT | +0.0 | fire |

## Previous Window Outcome

- **Window**: 2026-09-28T08:00:00+09:00 → 2026-09-29T08:00:00+09:00
- **Direction**: UP
- **Close change**: +1.1 bp
- **OHLC**: O=157.45 H=157.85 L=156.53 C=157.46
- **Range**: 1.32

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 100.6 | 98.3 | No |
| baseline_random_walk | False | - | 1.1 | 1.1 | No |
| baseline_simple_technical | True | - | 55.0 | 55.0 | No |
| ugh_v2_alpha | True | True | 16.0 | 16.0 | No |
| ugh_v2_beta | True | True | 4.7 | 4.7 | No |
| ugh_v2_delta | True | True | 10.0 | 10.0 | No |
| ugh_v2_gamma | True | True | 15.2 | 15.2 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **16.0 bp**
- Baseline direction hits: 1/3
