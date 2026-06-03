# FX Daily Report — 2026-06-03

Generated: 2026-06-03T09:59:55Z

## Run Summary

- **as_of_jst**: 2026-06-03T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260603T080000_v1_afb263d640fe6f2a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +15.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +22.9 | - |
| ugh_v2_alpha | UP | +13.4 | setup |
| ugh_v2_beta | UP | +13.4 | setup |
| ugh_v2_delta | UP | +13.4 | setup |
| ugh_v2_gamma | UP | +12.3 | setup |

## Previous Window Outcome

- **Window**: 2026-06-02T08:00:00+09:00 → 2026-06-03T08:00:00+09:00
- **Direction**: UP
- **Close change**: +15.0 bp
- **OHLC**: O=159.65 H=159.98 L=159.55 C=159.89
- **Range**: 0.43

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 6.9 | 6.9 | No |
| baseline_random_walk | False | - | 15.0 | 15.0 | No |
| baseline_simple_technical | True | - | 9.2 | 9.2 | No |
| ugh_v2_alpha | True | True | 0.5 | 0.5 | No |
| ugh_v2_beta | True | True | 0.7 | 0.7 | No |
| ugh_v2_delta | True | True | 0.2 | 0.2 | No |
| ugh_v2_gamma | True | True | 1.7 | 1.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **0.5 bp**
- Baseline direction hits: 2/3
