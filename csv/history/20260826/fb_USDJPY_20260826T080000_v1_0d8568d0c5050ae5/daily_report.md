# FX Daily Report — 2026-08-26

Generated: 2026-08-26T07:43:28Z

## Run Summary

- **as_of_jst**: 2026-08-26T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260826T080000_v1_0d8568d0c5050ae5
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +8.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -41.7 | - |
| ugh_v2_alpha | UP | +4.5 | setup |
| ugh_v2_beta | UP | +6.2 | setup |
| ugh_v2_delta | UP | +5.4 | setup |
| ugh_v2_gamma | UP | +4.5 | setup |

## Previous Window Outcome

- **Window**: 2026-08-25T08:00:00+09:00 → 2026-08-26T08:00:00+09:00
- **Direction**: UP
- **Close change**: +8.8 bp
- **OHLC**: O=159.02 H=159.48 L=158.99 C=159.16
- **Range**: 0.49

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 3.2 | 3.2 | No |
| baseline_random_walk | False | - | 8.8 | 8.8 | No |
| baseline_simple_technical | False | - | 50.5 | 32.9 | No |
| ugh_v2_alpha | True | True | 5.1 | 5.1 | No |
| ugh_v2_beta | True | True | 2.4 | 2.4 | No |
| ugh_v2_delta | True | True | 3.8 | 3.8 | No |
| ugh_v2_gamma | True | True | 5.0 | 5.0 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **5.1 bp**
- Baseline direction hits: 1/3
