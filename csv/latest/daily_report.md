# FX Daily Report — 2026-06-29

Generated: 2026-06-29T11:57:42Z

## Run Summary

- **as_of_jst**: 2026-06-29T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260629T080000_v1_76f7c3732f1b4ab8
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -3.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.6 | - |
| ugh_v2_alpha | UP | +4.9 | setup |
| ugh_v2_beta | UP | +3.1 | setup |
| ugh_v2_delta | UP | +4.0 | setup |
| ugh_v2_gamma | UP | +4.7 | setup |

## Previous Window Outcome

- **Window**: 2026-06-26T08:00:00+09:00 → 2026-06-29T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -3.1 bp
- **OHLC**: O=161.78 H=161.84 L=161.51 C=161.73
- **Range**: 0.33

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 4.3 | 1.9 | No |
| baseline_random_walk | False | - | 3.1 | 3.1 | No |
| baseline_simple_technical | False | - | 16.7 | 10.5 | No |
| ugh_v2_alpha | False | True | 9.1 | 2.9 | No |
| ugh_v2_beta | False | True | 7.7 | 1.5 | No |
| ugh_v2_delta | False | True | 8.3 | 2.1 | No |
| ugh_v2_gamma | False | True | 8.8 | 2.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **9.1 bp**
- Baseline direction hits: 0/3
