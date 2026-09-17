# FX Daily Report — 2026-09-17

Generated: 2026-09-17T15:35:12Z

## Run Summary

- **as_of_jst**: 2026-09-17T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260917T080000_v1_71a7d2e658eb9f93
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +75.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -46.8 | - |
| ugh_v2_alpha | DOWN | -6.1 | fire |
| ugh_v2_beta | FLAT | +0.0 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | DOWN | -5.7 | fire |

## Previous Window Outcome

- **Window**: 2026-09-16T08:00:00+09:00 → 2026-09-17T08:00:00+09:00
- **Direction**: UP
- **Close change**: +75.4 bp
- **OHLC**: O=155.10 H=156.41 L=154.86 C=156.27
- **Range**: 1.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 28.1 | 28.1 | No |
| baseline_random_walk | False | - | 75.4 | 75.4 | No |
| baseline_simple_technical | False | - | 123.0 | 27.9 | No |
| ugh_v2_alpha | False | True | 82.3 | 68.6 | No |
| ugh_v2_beta | True | True | 70.1 | 70.1 | No |
| ugh_v2_delta | False | True | 75.4 | 75.4 | No |
| ugh_v2_gamma | False | True | 81.7 | 69.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **82.3 bp**
- Baseline direction hits: 1/3
