# FX Daily Report — 2026-07-07

Generated: 2026-07-07T08:28:33Z

## Run Summary

- **as_of_jst**: 2026-07-07T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260707T080000_v1_905788c74d94aec6
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +45.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +20.7 | - |
| ugh_v2_alpha | UP | +19.0 | fire |
| ugh_v2_beta | UP | +22.4 | setup |
| ugh_v2_delta | UP | +20.7 | setup |
| ugh_v2_gamma | UP | +18.8 | fire |

## Previous Window Outcome

- **Window**: 2026-07-06T08:00:00+09:00 → 2026-07-07T08:00:00+09:00
- **Direction**: UP
- **Close change**: +45.2 bp
- **OHLC**: O=161.35 H=162.42 L=161.22 C=162.08
- **Range**: 1.20

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 27.9 | 27.9 | No |
| baseline_random_walk | False | - | 45.2 | 45.2 | No |
| baseline_simple_technical | True | - | 26.7 | 26.7 | No |
| ugh_v2_alpha | True | False | 36.6 | 36.6 | No |
| ugh_v2_beta | True | False | 33.4 | 33.4 | No |
| ugh_v2_delta | True | False | 34.3 | 34.3 | No |
| ugh_v2_gamma | True | False | 36.8 | 36.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **36.6 bp**
- Baseline direction hits: 2/3
