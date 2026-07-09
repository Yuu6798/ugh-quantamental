# FX Daily Report — 2026-07-09

Generated: 2026-07-09T08:38:33Z

## Run Summary

- **as_of_jst**: 2026-07-09T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260709T080000_v1_b4787a47a121c67f
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +30.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +20.9 | - |
| ugh_v2_alpha | UP | +7.7 | setup |
| ugh_v2_beta | UP | +11.5 | setup |
| ugh_v2_delta | UP | +9.8 | setup |
| ugh_v2_gamma | UP | +7.5 | setup |

## Previous Window Outcome

- **Window**: 2026-07-08T08:00:00+09:00 → 2026-07-09T08:00:00+09:00
- **Direction**: UP
- **Close change**: +30.2 bp
- **OHLC**: O=162.09 H=162.70 L=162.05 C=162.58
- **Range**: 0.65

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 29.6 | 29.6 | No |
| baseline_random_walk | False | - | 30.2 | 30.2 | No |
| baseline_simple_technical | True | - | 10.2 | 10.2 | No |
| ugh_v2_alpha | True | False | 26.6 | 26.6 | No |
| ugh_v2_beta | False | False | 30.2 | 30.2 | No |
| ugh_v2_delta | True | False | 27.0 | 27.0 | No |
| ugh_v2_gamma | True | False | 26.7 | 26.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **26.6 bp**
- Baseline direction hits: 2/3
