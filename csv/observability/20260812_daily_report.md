# FX Daily Report — 2026-08-12

Generated: 2026-08-12T08:15:32Z

## Run Summary

- **as_of_jst**: 2026-08-12T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260812T080000_v1_c3b9a60ca41391c6
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +2.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.5 | - |
| ugh_v2_alpha | DOWN | -10.0 | fire |
| ugh_v2_beta | DOWN | -4.8 | setup |
| ugh_v2_delta | DOWN | -7.5 | setup |
| ugh_v2_gamma | DOWN | -9.1 | fire |

## Previous Window Outcome

- **Window**: 2026-08-11T08:00:00+09:00 → 2026-08-12T08:00:00+09:00
- **Direction**: UP
- **Close change**: +2.5 bp
- **OHLC**: O=159.23 H=159.38 L=158.92 C=159.27
- **Range**: 0.46

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 96.4 | 96.4 | No |
| baseline_random_walk | False | - | 2.5 | 2.5 | No |
| baseline_simple_technical | False | - | 39.5 | 34.5 | No |
| ugh_v2_alpha | False | True | 2.5 | 2.5 | No |
| ugh_v2_beta | True | True | 2.1 | 2.1 | No |
| ugh_v2_delta | False | True | 2.5 | 2.5 | No |
| ugh_v2_gamma | False | True | 2.5 | 2.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **2.5 bp**
- Baseline direction hits: 1/3
