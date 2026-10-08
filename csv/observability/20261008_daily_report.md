# FX Daily Report — 2026-10-08

Generated: 2026-10-08T12:07:34Z

## Run Summary

- **as_of_jst**: 2026-10-08T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261008T080000_v1_c420fe32dcbcb3fd
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -1.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +37.2 | - |
| ugh_v2_alpha | UP | +14.2 | setup |
| ugh_v2_beta | UP | +10.4 | setup |
| ugh_v2_delta | UP | +12.4 | setup |
| ugh_v2_gamma | UP | +13.3 | setup |

## Previous Window Outcome

- **Window**: 2026-10-07T08:00:00+09:00 → 2026-10-08T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -1.9 bp
- **OHLC**: O=158.09 H=158.50 L=157.83 C=158.06
- **Range**: 0.67

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 11.4 | 7.6 | No |
| baseline_random_walk | False | - | 1.9 | 1.9 | No |
| baseline_simple_technical | False | - | 40.5 | 36.7 | No |
| ugh_v2_alpha | False | True | 21.8 | 18.0 | No |
| ugh_v2_beta | False | True | 18.4 | 14.6 | No |
| ugh_v2_delta | False | True | 20.0 | 16.2 | No |
| ugh_v2_gamma | False | True | 20.6 | 16.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **21.8 bp**
- Baseline direction hits: 0/3
