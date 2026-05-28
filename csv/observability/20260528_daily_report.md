# FX Daily Report — 2026-05-28

Generated: 2026-05-28T08:49:31Z

## Run Summary

- **as_of_jst**: 2026-05-28T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260528T080000_v1_0195a5d23dc7f6d6
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +14.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +36.9 | - |
| ugh_v2_alpha | UP | +19.8 | setup |
| ugh_v2_beta | UP | +18.2 | dormant |
| ugh_v2_delta | UP | +19.0 | dormant |
| ugh_v2_gamma | UP | +18.2 | dormant |

## Previous Window Outcome

- **Window**: 2026-05-27T08:00:00+09:00 → 2026-05-28T08:00:00+09:00
- **Direction**: UP
- **Close change**: +14.4 bp
- **OHLC**: O=159.28 H=159.58 L=159.16 C=159.51
- **Range**: 0.42

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 10.7 | 10.7 | No |
| baseline_random_walk | False | - | 14.4 | 14.4 | No |
| baseline_simple_technical | True | - | 24.3 | 24.3 | No |
| ugh_v2_alpha | True | True | 6.7 | 6.7 | No |
| ugh_v2_beta | True | True | 7.7 | 7.7 | No |
| ugh_v2_delta | True | True | 7.7 | 7.7 | No |
| ugh_v2_gamma | True | True | 4.7 | 4.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **6.7 bp**
- Baseline direction hits: 2/3
