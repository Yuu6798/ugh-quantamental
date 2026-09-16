# FX Daily Report — 2026-09-16

Generated: 2026-09-16T12:39:38Z

## Run Summary

- **as_of_jst**: 2026-09-16T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260916T080000_v1_bc9bf6c6dec3e149
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +47.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -47.6 | - |
| ugh_v2_alpha | DOWN | -6.9 | fire |
| ugh_v2_beta | UP | +5.3 | fire |
| ugh_v2_delta | FLAT | +0.0 | fire |
| ugh_v2_gamma | DOWN | -6.3 | fire |

## Previous Window Outcome

- **Window**: 2026-09-15T08:00:00+09:00 → 2026-09-16T08:00:00+09:00
- **Direction**: UP
- **Close change**: +47.3 bp
- **OHLC**: O=154.35 H=155.23 L=154.19 C=155.08
- **Range**: 1.04

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 16.6 | 16.6 | No |
| baseline_random_walk | False | - | 47.3 | 47.3 | No |
| baseline_simple_technical | False | - | 93.2 | 1.4 | No |
| ugh_v2_alpha | False | True | 54.5 | 40.1 | No |
| ugh_v2_beta | True | True | 42.2 | 42.2 | No |
| ugh_v2_delta | False | True | 47.3 | 47.3 | No |
| ugh_v2_gamma | False | True | 54.0 | 40.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **54.5 bp**
- Baseline direction hits: 1/3
