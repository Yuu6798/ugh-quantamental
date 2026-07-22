# FX Daily Report — 2026-07-22

Generated: 2026-07-22T09:25:00Z

## Run Summary

- **as_of_jst**: 2026-07-22T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260722T080000_v1_c963dcd6443dc6a0
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +42.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +22.4 | - |
| ugh_v2_alpha | UP | +9.4 | setup |
| ugh_v2_beta | UP | +12.0 | setup |
| ugh_v2_delta | UP | +10.7 | setup |
| ugh_v2_gamma | UP | +8.7 | setup |

## Previous Window Outcome

- **Window**: 2026-07-21T08:00:00+09:00 → 2026-07-22T08:00:00+09:00
- **Direction**: UP
- **Close change**: +42.5 bp
- **OHLC**: O=162.47 H=163.23 L=162.41 C=163.16
- **Range**: 0.82

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 34.5 | 34.5 | No |
| baseline_random_walk | False | - | 42.5 | 42.5 | No |
| baseline_simple_technical | True | - | 22.1 | 22.1 | No |
| ugh_v2_alpha | True | False | 36.5 | 36.5 | No |
| ugh_v2_beta | True | False | 35.7 | 35.7 | No |
| ugh_v2_delta | True | False | 36.1 | 36.1 | No |
| ugh_v2_gamma | True | False | 37.0 | 37.0 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **36.5 bp**
- Baseline direction hits: 2/3
