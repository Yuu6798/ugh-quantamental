# FX Daily Report — 2026-09-08

Generated: 2026-09-08T12:11:46Z

## Run Summary

- **as_of_jst**: 2026-09-08T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260908T080000_v1_64baba35396ab847
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -102.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.6 | - |
| ugh_v2_alpha | DOWN | -57.1 | fire |
| ugh_v2_beta | DOWN | -57.1 | fire |
| ugh_v2_delta | DOWN | -57.1 | fire |
| ugh_v2_gamma | DOWN | -57.1 | fire |

## Previous Window Outcome

- **Window**: 2026-09-07T08:00:00+09:00 → 2026-09-08T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -102.0 bp
- **OHLC**: O=155.94 H=156.27 L=154.04 C=154.35
- **Range**: 2.23

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 128.3 | 75.7 | No |
| baseline_random_walk | False | - | 102.0 | 102.0 | No |
| baseline_simple_technical | True | - | 65.5 | 65.5 | No |
| ugh_v2_alpha | False | False | 102.0 | 102.0 | No |
| ugh_v2_beta | False | False | 102.0 | 102.0 | No |
| ugh_v2_delta | False | False | 102.0 | 102.0 | No |
| ugh_v2_gamma | False | False | 102.0 | 102.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **102.0 bp**
- Baseline direction hits: 1/3
