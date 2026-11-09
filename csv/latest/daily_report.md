# FX Daily Report — 2026-11-09

Generated: 2026-11-09T14:05:59Z

## Run Summary

- **as_of_jst**: 2026-11-09T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261109T080000_v1_a893771d332cd12e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +49.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +25.0 | - |
| ugh_v2_alpha | UP | +6.3 | setup |
| ugh_v2_beta | UP | +9.4 | setup |
| ugh_v2_delta | UP | +8.0 | setup |
| ugh_v2_gamma | UP | +6.0 | setup |

## Previous Window Outcome

- **Window**: 2026-11-06T08:00:00+09:00 → 2026-11-09T08:00:00+09:00
- **Direction**: UP
- **Close change**: +49.5 bp
- **OHLC**: O=157.67 H=158.56 L=157.21 C=158.45
- **Range**: 1.35

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 95.6 | 3.4 | No |
| baseline_random_walk | False | - | 49.5 | 49.5 | No |
| baseline_simple_technical | True | - | 25.5 | 25.5 | No |
| ugh_v2_alpha | False | True | 49.5 | 49.5 | No |
| ugh_v2_beta | False | True | 53.3 | 45.7 | No |
| ugh_v2_delta | False | True | 49.5 | 49.5 | No |
| ugh_v2_gamma | False | True | 49.5 | 49.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **49.5 bp**
- Baseline direction hits: 1/3
