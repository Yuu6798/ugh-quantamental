# FX Daily Report — 2026-11-11

Generated: 2026-11-11T12:50:13Z

## Run Summary

- **as_of_jst**: 2026-11-11T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261111T080000_v1_e9ab61266ee8d441
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +52.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +26.4 | - |
| ugh_v2_alpha | UP | +5.7 | setup |
| ugh_v2_beta | UP | +8.5 | setup |
| ugh_v2_delta | UP | +7.3 | setup |
| ugh_v2_gamma | UP | +5.3 | setup |

## Previous Window Outcome

- **Window**: 2026-11-10T08:00:00+09:00 → 2026-11-11T08:00:00+09:00
- **Direction**: UP
- **Close change**: +52.6 bp
- **OHLC**: O=157.90 H=158.85 L=157.85 C=158.73
- **Range**: 1.00

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 77.8 | 27.3 | No |
| baseline_random_walk | False | - | 52.6 | 52.6 | No |
| baseline_simple_technical | True | - | 27.8 | 27.8 | No |
| ugh_v2_alpha | False | True | 52.6 | 52.6 | No |
| ugh_v2_beta | False | True | 55.7 | 49.5 | No |
| ugh_v2_delta | False | True | 52.6 | 52.6 | No |
| ugh_v2_gamma | False | True | 52.6 | 52.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **52.6 bp**
- Baseline direction hits: 1/3
