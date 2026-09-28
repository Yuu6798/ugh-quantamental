# FX Daily Report — 2026-09-28

Generated: 2026-09-28T11:49:25Z

## Run Summary

- **as_of_jst**: 2026-09-28T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260928T080000_v1_4610bf7341d18e06
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -99.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +56.2 | - |
| ugh_v2_alpha | UP | +17.2 | failure |
| ugh_v2_beta | UP | +5.9 | failure |
| ugh_v2_delta | UP | +11.1 | failure |
| ugh_v2_gamma | UP | +16.4 | failure |

## Previous Window Outcome

- **Window**: 2026-09-25T08:00:00+09:00 → 2026-09-28T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -99.5 bp
- **OHLC**: O=158.84 H=158.91 L=156.93 C=157.26
- **Range**: 1.98

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 134.2 | 64.7 | No |
| baseline_random_walk | False | - | 99.5 | 99.5 | No |
| baseline_simple_technical | False | - | 152.7 | 46.2 | No |
| ugh_v2_alpha | False | True | 145.9 | 53.0 | No |
| ugh_v2_beta | False | True | 142.5 | 56.4 | No |
| ugh_v2_delta | False | True | 143.4 | 55.5 | No |
| ugh_v2_gamma | False | True | 143.5 | 55.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **145.9 bp**
- Baseline direction hits: 0/3
