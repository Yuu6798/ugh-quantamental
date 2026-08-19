# FX Daily Report — 2026-08-19

Generated: 2026-08-19T05:36:20Z

## Run Summary

- **as_of_jst**: 2026-08-19T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260819T080000_v1_4156c3ab92f53e2e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +13.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.0 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | UP | +5.5 | setup |
| ugh_v2_delta | UP | +3.6 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-08-18T08:00:00+09:00 → 2026-08-19T08:00:00+09:00
- **Direction**: UP
- **Close change**: +13.8 bp
- **OHLC**: O=159.40 H=159.77 L=159.28 C=159.62
- **Range**: 0.49

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 0.0 | 0.0 | No |
| baseline_random_walk | False | - | 13.8 | 13.8 | No |
| baseline_simple_technical | False | - | 51.2 | 23.6 | No |
| ugh_v2_alpha | False | True | 13.8 | 13.8 | No |
| ugh_v2_beta | True | True | 9.3 | 9.3 | No |
| ugh_v2_delta | False | True | 13.8 | 13.8 | No |
| ugh_v2_gamma | False | True | 13.8 | 13.8 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **13.8 bp**
- Baseline direction hits: 1/3
