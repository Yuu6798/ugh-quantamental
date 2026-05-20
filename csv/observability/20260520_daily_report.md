# FX Daily Report — 2026-05-20

Generated: 2026-05-20T13:35:17Z

## Run Summary

- **as_of_jst**: 2026-05-20T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260520T080000_v1_94ca197cb30be132
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +15.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +39.0 | - |
| ugh_v2_alpha | UP | +13.9 | setup |
| ugh_v2_beta | UP | +14.6 | setup |
| ugh_v2_delta | UP | +14.2 | setup |
| ugh_v2_gamma | UP | +12.8 | setup |

## Previous Window Outcome

- **Window**: 2026-05-19T08:00:00+09:00 → 2026-05-20T08:00:00+09:00
- **Direction**: UP
- **Close change**: +15.7 bp
- **OHLC**: O=158.79 H=159.25 L=158.70 C=159.04
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 4.4 | 4.4 | No |
| baseline_random_walk | False | - | 15.7 | 15.7 | No |
| baseline_simple_technical | True | - | 24.4 | 24.4 | No |
| ugh_v2_alpha | True | True | 6.2 | 6.2 | No |
| ugh_v2_beta | True | True | 3.7 | 3.7 | No |
| ugh_v2_delta | True | True | 4.8 | 4.8 | No |
| ugh_v2_gamma | True | True | 6.7 | 6.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **6.2 bp**
- Baseline direction hits: 2/3
