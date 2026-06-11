# FX Daily Report — 2026-06-11

Generated: 2026-06-11T14:33:23Z

## Run Summary

- **as_of_jst**: 2026-06-11T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260611T080000_v1_deee92cef0e158c8
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +11.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.9 | - |
| ugh_v2_alpha | UP | +7.3 | setup |
| ugh_v2_beta | UP | +8.1 | setup |
| ugh_v2_delta | UP | +7.8 | setup |
| ugh_v2_gamma | UP | +6.9 | setup |

## Previous Window Outcome

- **Window**: 2026-06-10T08:00:00+09:00 → 2026-06-11T08:00:00+09:00
- **Direction**: UP
- **Close change**: +11.8 bp
- **OHLC**: O=160.34 H=160.57 L=160.21 C=160.53
- **Range**: 0.36

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 3.1 | 3.1 | No |
| baseline_random_walk | False | - | 11.8 | 11.8 | No |
| baseline_simple_technical | True | - | 2.2 | 2.2 | No |
| ugh_v2_alpha | True | True | 4.2 | 4.2 | No |
| ugh_v2_beta | True | True | 3.1 | 3.1 | No |
| ugh_v2_delta | True | True | 3.6 | 3.6 | No |
| ugh_v2_gamma | True | True | 4.6 | 4.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **4.2 bp**
- Baseline direction hits: 2/3
