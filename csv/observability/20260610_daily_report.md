# FX Daily Report — 2026-06-10

Generated: 2026-06-10T10:55:18Z

## Run Summary

- **as_of_jst**: 2026-06-10T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260610T080000_v1_665a2eea6c4b0043
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +15.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.1 | - |
| ugh_v2_alpha | UP | +7.6 | fire |
| ugh_v2_beta | UP | +8.7 | fire |
| ugh_v2_delta | UP | +8.2 | fire |
| ugh_v2_gamma | UP | +7.2 | fire |

## Previous Window Outcome

- **Window**: 2026-06-09T08:00:00+09:00 → 2026-06-10T08:00:00+09:00
- **Direction**: UP
- **Close change**: +15.0 bp
- **OHLC**: O=160.12 H=160.44 L=160.03 C=160.36
- **Range**: 0.41

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 13.1 | 13.1 | No |
| baseline_random_walk | False | - | 15.0 | 15.0 | No |
| baseline_simple_technical | True | - | 0.2 | 0.2 | No |
| ugh_v2_alpha | True | True | 8.5 | 8.5 | No |
| ugh_v2_beta | True | True | 9.8 | 9.8 | No |
| ugh_v2_delta | True | True | 9.2 | 9.2 | No |
| ugh_v2_gamma | True | True | 8.8 | 8.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **8.5 bp**
- Baseline direction hits: 2/3
