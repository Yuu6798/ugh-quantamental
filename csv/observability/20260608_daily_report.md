# FX Daily Report — 2026-06-08

Generated: 2026-06-08T09:27:43Z

## Run Summary

- **as_of_jst**: 2026-06-08T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260608T080000_v1_701a19d8f7bd18c3
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +17.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +17.2 | - |
| ugh_v2_alpha | UP | +9.7 | fire |
| ugh_v2_beta | UP | +10.8 | fire |
| ugh_v2_delta | UP | +10.3 | fire |
| ugh_v2_gamma | UP | +9.2 | fire |

## Previous Window Outcome

- **Window**: 2026-06-05T08:00:00+09:00 → 2026-06-08T08:00:00+09:00
- **Direction**: UP
- **Close change**: +17.5 bp
- **OHLC**: O=160.01 H=160.34 L=159.82 C=160.29
- **Range**: 0.52

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 18.7 | 16.2 | No |
| baseline_random_walk | False | - | 17.5 | 17.5 | No |
| baseline_simple_technical | True | - | 0.4 | 0.4 | No |
| ugh_v2_alpha | True | True | 11.3 | 11.3 | No |
| ugh_v2_beta | True | False | 13.1 | 13.1 | No |
| ugh_v2_delta | True | True | 12.3 | 12.3 | No |
| ugh_v2_gamma | True | True | 11.6 | 11.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **11.3 bp**
- Baseline direction hits: 1/3
