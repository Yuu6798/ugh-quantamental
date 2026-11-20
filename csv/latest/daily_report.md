# FX Daily Report — 2026-11-20

Generated: 2026-11-20T19:09:54Z

## Run Summary

- **as_of_jst**: 2026-11-20T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261120T080000_v1_10309e251a4933e4
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +21.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.3 | - |
| ugh_v2_alpha | UP | +12.4 | setup |
| ugh_v2_beta | UP | +13.3 | setup |
| ugh_v2_delta | UP | +12.9 | setup |
| ugh_v2_gamma | UP | +11.6 | setup |

## Previous Window Outcome

- **Window**: 2026-11-19T08:00:00+09:00 → 2026-11-20T08:00:00+09:00
- **Direction**: UP
- **Close change**: +21.3 bp
- **OHLC**: O=159.33 H=159.96 L=159.26 C=159.67
- **Range**: 0.70

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 23.2 | 19.5 | No |
| baseline_random_walk | False | - | 21.3 | 21.3 | No |
| baseline_simple_technical | True | - | 6.2 | 6.2 | No |
| ugh_v2_alpha | True | True | 10.5 | 10.5 | No |
| ugh_v2_beta | True | True | 13.5 | 13.5 | No |
| ugh_v2_delta | True | True | 12.1 | 12.1 | No |
| ugh_v2_gamma | True | True | 11.3 | 11.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **10.5 bp**
- Baseline direction hits: 1/3
