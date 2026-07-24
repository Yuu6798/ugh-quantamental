# FX Daily Report — 2026-07-24

Generated: 2026-07-24T09:20:22Z

## Run Summary

- **as_of_jst**: 2026-07-24T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260724T080000_v1_824eaec06cc785dc
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +44.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +23.7 | - |
| ugh_v2_alpha | UP | +12.8 | setup |
| ugh_v2_beta | UP | +15.2 | setup |
| ugh_v2_delta | UP | +14.1 | setup |
| ugh_v2_gamma | UP | +11.9 | setup |

## Previous Window Outcome

- **Window**: 2026-07-23T08:00:00+09:00 → 2026-07-24T08:00:00+09:00
- **Direction**: UP
- **Close change**: +44.1 bp
- **OHLC**: O=163.13 H=163.98 L=162.98 C=163.85
- **Range**: 1.00

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 46.0 | 42.3 | No |
| baseline_random_walk | False | - | 44.1 | 44.1 | No |
| baseline_simple_technical | True | - | 22.6 | 22.6 | No |
| ugh_v2_alpha | True | False | 38.7 | 38.7 | No |
| ugh_v2_beta | True | False | 40.0 | 40.0 | No |
| ugh_v2_delta | True | False | 39.4 | 39.4 | No |
| ugh_v2_gamma | True | False | 39.0 | 39.0 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **38.7 bp**
- Baseline direction hits: 1/3
