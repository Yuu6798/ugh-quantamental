# FX Daily Report — 2026-06-02

Generated: 2026-06-02T11:16:53Z

## Run Summary

- **as_of_jst**: 2026-06-02T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260602T080000_v1_1ca5fcd522d531cb
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +22.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.3 | - |
| ugh_v2_alpha | UP | +14.5 | setup |
| ugh_v2_beta | UP | +15.7 | setup |
| ugh_v2_delta | UP | +15.2 | setup |
| ugh_v2_gamma | UP | +13.3 | setup |

## Previous Window Outcome

- **Window**: 2026-06-01T08:00:00+09:00 → 2026-06-02T08:00:00+09:00
- **Direction**: UP
- **Close change**: +22.0 bp
- **OHLC**: O=159.30 H=159.76 L=159.21 C=159.65
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 18.8 | 18.8 | No |
| baseline_random_walk | False | - | 22.0 | 22.0 | No |
| baseline_simple_technical | True | - | 2.6 | 2.6 | No |
| ugh_v2_alpha | True | False | 11.7 | 11.7 | No |
| ugh_v2_beta | True | False | 13.2 | 13.2 | No |
| ugh_v2_delta | True | False | 12.3 | 12.3 | No |
| ugh_v2_gamma | True | False | 12.4 | 12.4 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **11.7 bp**
- Baseline direction hits: 2/3
