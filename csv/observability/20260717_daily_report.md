# FX Daily Report — 2026-07-17

Generated: 2026-07-17T07:22:44Z

## Run Summary

- **as_of_jst**: 2026-07-17T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260717T080000_v1_75b83f23d32a969e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +12.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +21.1 | - |
| ugh_v2_alpha | UP | +5.3 | setup |
| ugh_v2_beta | UP | +7.1 | setup |
| ugh_v2_delta | UP | +6.3 | setup |
| ugh_v2_gamma | UP | +5.0 | setup |

## Previous Window Outcome

- **Window**: 2026-07-16T08:00:00+09:00 → 2026-07-17T08:00:00+09:00
- **Direction**: UP
- **Close change**: +12.3 bp
- **OHLC**: O=162.18 H=162.54 L=161.96 C=162.38
- **Range**: 0.58

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 11.1 | 11.1 | No |
| baseline_random_walk | False | - | 12.3 | 12.3 | No |
| baseline_simple_technical | True | - | 10.4 | 10.4 | No |
| ugh_v2_alpha | True | True | 8.1 | 8.1 | No |
| ugh_v2_beta | True | True | 8.6 | 8.6 | No |
| ugh_v2_delta | True | True | 8.3 | 8.3 | No |
| ugh_v2_gamma | True | True | 8.3 | 8.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **8.1 bp**
- Baseline direction hits: 2/3
