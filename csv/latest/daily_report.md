# FX Daily Report — 2026-08-21

Generated: 2026-08-21T07:40:29Z

## Run Summary

- **as_of_jst**: 2026-08-21T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260821T080000_v1_4daba8128144322f
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +56.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -41.0 | - |
| ugh_v2_alpha | UP | +4.3 | failure |
| ugh_v2_beta | UP | +12.0 | failure |
| ugh_v2_delta | UP | +8.2 | failure |
| ugh_v2_gamma | UP | +4.3 | failure |

## Previous Window Outcome

- **Window**: 2026-08-20T08:00:00+09:00 → 2026-08-21T08:00:00+09:00
- **Direction**: UP
- **Close change**: +56.3 bp
- **OHLC**: O=158.16 H=159.18 L=158.00 C=159.05
- **Range**: 1.18

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 146.5 | 34.0 | No |
| baseline_random_walk | False | - | 56.3 | 56.3 | No |
| baseline_simple_technical | False | - | 96.7 | 15.9 | No |
| ugh_v2_alpha | False | True | 65.5 | 47.1 | No |
| ugh_v2_beta | False | True | 70.0 | 42.6 | No |
| ugh_v2_delta | False | True | 68.3 | 44.3 | No |
| ugh_v2_gamma | False | True | 64.0 | 48.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **65.5 bp**
- Baseline direction hits: 0/3
