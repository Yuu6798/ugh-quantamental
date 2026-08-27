# FX Daily Report — 2026-08-27

Generated: 2026-08-27T16:19:58Z

## Run Summary

- **as_of_jst**: 2026-08-27T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260827T080000_v1_136aacdb4a1cf179
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +8.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +40.8 | - |
| ugh_v2_alpha | UP | +13.0 | setup |
| ugh_v2_beta | UP | +12.9 | setup |
| ugh_v2_delta | UP | +13.0 | setup |
| ugh_v2_gamma | UP | +12.1 | setup |

## Previous Window Outcome

- **Window**: 2026-08-26T08:00:00+09:00 → 2026-08-27T08:00:00+09:00
- **Direction**: UP
- **Close change**: +8.2 bp
- **OHLC**: O=159.16 H=159.44 L=158.86 C=159.29
- **Range**: 0.58

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 0.6 | 0.6 | No |
| baseline_random_walk | False | - | 8.2 | 8.2 | No |
| baseline_simple_technical | False | - | 49.9 | 33.5 | No |
| ugh_v2_alpha | True | True | 3.6 | 3.6 | No |
| ugh_v2_beta | True | True | 2.0 | 2.0 | No |
| ugh_v2_delta | True | True | 2.8 | 2.8 | No |
| ugh_v2_gamma | True | True | 3.7 | 3.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.6 bp**
- Baseline direction hits: 1/3
