# FX Daily Report — 2026-09-04

Generated: 2026-09-04T12:10:33Z

## Run Summary

- **as_of_jst**: 2026-09-04T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260904T080000_v1_55c5bfc1b8a88670
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -181.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.1 | - |
| ugh_v2_alpha | DOWN | -7.7 | setup |
| ugh_v2_beta | DOWN | -12.7 | setup |
| ugh_v2_delta | DOWN | -10.0 | setup |
| ugh_v2_gamma | DOWN | -7.3 | setup |

## Previous Window Outcome

- **Window**: 2026-09-03T08:00:00+09:00 → 2026-09-04T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -181.5 bp
- **OHLC**: O=158.67 H=158.96 L=155.28 C=155.79
- **Range**: 3.68

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 91.0 | 91.0 | No |
| baseline_random_walk | False | - | 181.5 | 181.5 | No |
| baseline_simple_technical | False | - | 211.7 | 151.3 | No |
| ugh_v2_alpha | False | False | 181.5 | 181.5 | No |
| ugh_v2_beta | True | False | 176.1 | 176.1 | No |
| ugh_v2_delta | False | False | 181.5 | 181.5 | No |
| ugh_v2_gamma | False | False | 181.5 | 181.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **181.5 bp**
- Baseline direction hits: 1/3
