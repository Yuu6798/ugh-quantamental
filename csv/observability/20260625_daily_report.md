# FX Daily Report — 2026-06-25

Generated: 2026-06-25T08:27:41Z

## Run Summary

- **as_of_jst**: 2026-06-25T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260625T080000_v1_1cd3741d55a51f4b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +18.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.4 | - |
| ugh_v2_alpha | UP | +10.1 | fire |
| ugh_v2_beta | UP | +10.7 | fire |
| ugh_v2_delta | UP | +10.4 | fire |
| ugh_v2_gamma | UP | +9.8 | fire |

## Previous Window Outcome

- **Window**: 2026-06-24T08:00:00+09:00 → 2026-06-25T08:00:00+09:00
- **Direction**: UP
- **Close change**: +18.0 bp
- **OHLC**: O=161.48 H=161.83 L=161.46 C=161.77
- **Range**: 0.37

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 14.9 | 14.9 | No |
| baseline_random_walk | False | - | 18.0 | 18.0 | No |
| baseline_simple_technical | True | - | 3.8 | 3.8 | No |
| ugh_v2_alpha | True | True | 10.8 | 10.8 | No |
| ugh_v2_beta | True | True | 12.2 | 12.2 | No |
| ugh_v2_delta | True | True | 11.7 | 11.7 | No |
| ugh_v2_gamma | True | True | 10.9 | 10.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **10.8 bp**
- Baseline direction hits: 2/3
