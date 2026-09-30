# FX Daily Report — 2026-09-30

Generated: 2026-09-30T13:54:15Z

## Run Summary

- **as_of_jst**: 2026-09-30T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260930T080000_v1_510ea2a7b17440a3
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -7.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +54.8 | - |
| ugh_v2_alpha | UP | +16.9 | setup |
| ugh_v2_beta | UP | +11.1 | setup |
| ugh_v2_delta | UP | +14.6 | setup |
| ugh_v2_gamma | UP | +15.9 | setup |

## Previous Window Outcome

- **Window**: 2026-09-29T08:00:00+09:00 → 2026-09-30T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -7.6 bp
- **OHLC**: O=157.40 H=157.71 L=156.96 C=157.28
- **Range**: 0.75

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 8.8 | 6.5 | No |
| baseline_random_walk | False | - | 7.6 | 7.6 | No |
| baseline_simple_technical | False | - | 8.8 | 6.4 | No |
| ugh_v2_alpha | False | True | 7.6 | 7.6 | No |
| ugh_v2_beta | False | True | 7.6 | 7.6 | No |
| ugh_v2_delta | False | True | 7.6 | 7.6 | No |
| ugh_v2_gamma | False | True | 7.6 | 7.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **7.6 bp**
- Baseline direction hits: 0/3
