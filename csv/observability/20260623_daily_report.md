# FX Daily Report — 2026-06-23

Generated: 2026-06-23T08:32:52Z

## Run Summary

- **as_of_jst**: 2026-06-23T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260623T080000_v1_971a08ea9152e71b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +17.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +15.3 | - |
| ugh_v2_alpha | UP | +8.6 | fire |
| ugh_v2_beta | UP | +9.6 | fire |
| ugh_v2_delta | UP | +9.1 | fire |
| ugh_v2_gamma | UP | +8.5 | fire |

## Previous Window Outcome

- **Window**: 2026-06-22T08:00:00+09:00 → 2026-06-23T08:00:00+09:00
- **Direction**: UP
- **Close change**: +17.4 bp
- **OHLC**: O=161.26 H=161.92 L=161.06 C=161.54
- **Range**: 0.86

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 22.9 | 11.8 | No |
| baseline_random_walk | False | - | 17.4 | 17.4 | No |
| baseline_simple_technical | True | - | 2.9 | 2.9 | No |
| ugh_v2_alpha | True | True | 13.8 | 13.8 | No |
| ugh_v2_beta | False | False | 17.4 | 17.4 | No |
| ugh_v2_delta | False | False | 17.4 | 17.4 | No |
| ugh_v2_gamma | True | True | 13.8 | 13.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **13.8 bp**
- Baseline direction hits: 1/3
