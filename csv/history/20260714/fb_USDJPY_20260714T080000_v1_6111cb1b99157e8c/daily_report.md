# FX Daily Report — 2026-07-14

Generated: 2026-07-14T07:14:38Z

## Run Summary

- **as_of_jst**: 2026-07-14T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260714T080000_v1_6111cb1b99157e8c
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +53.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +23.3 | - |
| ugh_v2_alpha | UP | +10.5 | setup |
| ugh_v2_beta | UP | +14.2 | setup |
| ugh_v2_delta | UP | +12.6 | setup |
| ugh_v2_gamma | UP | +9.7 | setup |

## Previous Window Outcome

- **Window**: 2026-07-13T08:00:00+09:00 → 2026-07-14T08:00:00+09:00
- **Direction**: UP
- **Close change**: +53.2 bp
- **OHLC**: O=161.56 H=162.48 L=161.55 C=162.42
- **Range**: 0.93

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 95.1 | 11.4 | No |
| baseline_random_walk | False | - | 53.2 | 53.2 | No |
| baseline_simple_technical | True | - | 32.3 | 32.3 | No |
| ugh_v2_alpha | False | False | 53.2 | 53.2 | No |
| ugh_v2_beta | False | False | 53.2 | 53.2 | No |
| ugh_v2_delta | False | False | 53.2 | 53.2 | No |
| ugh_v2_gamma | False | False | 53.2 | 53.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **53.2 bp**
- Baseline direction hits: 1/3
