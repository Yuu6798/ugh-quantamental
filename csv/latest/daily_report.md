# FX Daily Report — 2026-06-17

Generated: 2026-06-17T14:23:30Z

## Run Summary

- **as_of_jst**: 2026-06-17T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260617T080000_v1_9724a46d3615eefe
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +9.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +12.6 | - |
| ugh_v2_alpha | UP | +5.2 | setup |
| ugh_v2_beta | UP | +6.1 | setup |
| ugh_v2_delta | UP | +5.7 | setup |
| ugh_v2_gamma | UP | +5.0 | setup |

## Previous Window Outcome

- **Window**: 2026-06-16T08:00:00+09:00 → 2026-06-17T08:00:00+09:00
- **Direction**: UP
- **Close change**: +9.4 bp
- **OHLC**: O=160.30 H=160.48 L=160.03 C=160.45
- **Range**: 0.45

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 3.1 | 3.1 | No |
| baseline_random_walk | False | - | 9.4 | 9.4 | No |
| baseline_simple_technical | True | - | 3.6 | 3.6 | No |
| ugh_v2_alpha | True | True | 3.4 | 3.4 | No |
| ugh_v2_beta | True | True | 3.2 | 3.2 | No |
| ugh_v2_delta | True | True | 3.3 | 3.3 | No |
| ugh_v2_gamma | True | True | 3.7 | 3.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.4 bp**
- Baseline direction hits: 2/3
