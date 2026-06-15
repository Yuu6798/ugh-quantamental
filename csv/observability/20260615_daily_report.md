# FX Daily Report — 2026-06-15

Generated: 2026-06-15T11:19:19Z

## Run Summary

- **as_of_jst**: 2026-06-15T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260615T080000_v1_921dbde4625d4898
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +18.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.7 | - |
| ugh_v2_alpha | UP | +6.2 | setup |
| ugh_v2_beta | UP | +7.6 | setup |
| ugh_v2_delta | UP | +7.0 | setup |
| ugh_v2_gamma | UP | +5.9 | setup |

## Previous Window Outcome

- **Window**: 2026-06-12T08:00:00+09:00 → 2026-06-15T08:00:00+09:00
- **Direction**: UP
- **Close change**: +18.1 bp
- **OHLC**: O=159.92 H=160.37 L=159.87 C=160.21
- **Range**: 0.50

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 54.3 | 18.0 | No |
| baseline_random_walk | False | - | 18.1 | 18.1 | No |
| baseline_simple_technical | True | - | 4.1 | 4.1 | No |
| ugh_v2_alpha | False | False | 18.1 | 18.1 | No |
| ugh_v2_beta | False | False | 18.1 | 18.1 | No |
| ugh_v2_delta | False | False | 18.1 | 18.1 | No |
| ugh_v2_gamma | False | False | 18.1 | 18.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **18.1 bp**
- Baseline direction hits: 1/3
