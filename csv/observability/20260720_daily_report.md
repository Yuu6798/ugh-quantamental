# FX Daily Report — 2026-07-20

Generated: 2026-07-20T08:11:38Z

## Run Summary

- **as_of_jst**: 2026-07-20T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260720T080000_v1_40c893c75e145950
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +0.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +20.9 | - |
| ugh_v2_alpha | UP | +4.9 | setup |
| ugh_v2_beta | UP | +4.2 | setup |
| ugh_v2_delta | UP | +4.6 | setup |
| ugh_v2_gamma | UP | +4.7 | setup |

## Previous Window Outcome

- **Window**: 2026-07-17T08:00:00+09:00 → 2026-07-20T08:00:00+09:00
- **Direction**: UP
- **Close change**: +0.6 bp
- **OHLC**: O=162.38 H=162.51 L=162.12 C=162.39
- **Range**: 0.39

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 11.7 | 11.7 | No |
| baseline_random_walk | False | - | 0.6 | 0.6 | No |
| baseline_simple_technical | True | - | 20.5 | 20.5 | No |
| ugh_v2_alpha | True | True | 4.7 | 4.7 | No |
| ugh_v2_beta | True | True | 6.5 | 6.5 | No |
| ugh_v2_delta | True | True | 5.7 | 5.7 | No |
| ugh_v2_gamma | True | True | 4.3 | 4.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **4.7 bp**
- Baseline direction hits: 2/3
