# FX Daily Report — 2026-09-01

Generated: 2026-09-01T07:31:57Z

## Run Summary

- **as_of_jst**: 2026-09-01T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260901T080000_v1_bc868e3f192c223c
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -20.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +26.1 | - |
| ugh_v2_alpha | UP | +4.8 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | UP | +4.6 | setup |

## Previous Window Outcome

- **Window**: 2026-08-31T08:00:00+09:00 → 2026-09-01T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -20.0 bp
- **OHLC**: O=160.05 H=160.20 L=159.45 C=159.73
- **Range**: 0.75

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 60.8 | 20.8 | No |
| baseline_random_walk | False | - | 20.0 | 20.0 | No |
| baseline_simple_technical | False | - | 45.3 | 5.3 | No |
| ugh_v2_alpha | False | True | 32.3 | 7.7 | No |
| ugh_v2_beta | False | True | 34.8 | 5.2 | No |
| ugh_v2_delta | False | True | 33.6 | 6.4 | No |
| ugh_v2_gamma | False | True | 31.2 | 8.8 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **32.3 bp**
- Baseline direction hits: 0/3
