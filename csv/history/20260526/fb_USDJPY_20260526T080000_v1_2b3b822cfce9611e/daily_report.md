# FX Daily Report — 2026-05-26

Generated: 2026-05-26T08:37:31Z

## Run Summary

- **as_of_jst**: 2026-05-26T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260526T080000_v1_2b3b822cfce9611e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -0.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.1 | - |
| ugh_v2_alpha | UP | +14.2 | setup |
| ugh_v2_beta | UP | +11.5 | setup |
| ugh_v2_delta | UP | +13.0 | setup |
| ugh_v2_gamma | UP | +13.2 | setup |

## Previous Window Outcome

- **Window**: 2026-05-25T08:00:00+09:00 → 2026-05-26T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -0.6 bp
- **OHLC**: O=158.90 H=159.04 L=158.74 C=158.89
- **Range**: 0.30

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 15.7 | 14.5 | No |
| baseline_random_walk | False | - | 0.6 | 0.6 | No |
| baseline_simple_technical | False | - | 39.3 | 38.0 | No |
| ugh_v2_alpha | False | True | 20.5 | 19.2 | No |
| ugh_v2_beta | False | True | 19.6 | 18.3 | No |
| ugh_v2_delta | False | True | 20.1 | 18.8 | No |
| ugh_v2_gamma | False | True | 19.0 | 17.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **20.5 bp**
- Baseline direction hits: 0/3
