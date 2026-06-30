# FX Daily Report — 2026-06-30

Generated: 2026-06-30T08:33:20Z

## Run Summary

- **as_of_jst**: 2026-06-30T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260630T080000_v1_5a7cb65e0af7a655
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +14.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.2 | - |
| ugh_v2_alpha | UP | +10.5 | setup |
| ugh_v2_beta | UP | +11.7 | setup |
| ugh_v2_delta | UP | +11.2 | setup |
| ugh_v2_gamma | UP | +9.6 | fire |

## Previous Window Outcome

- **Window**: 2026-06-29T08:00:00+09:00 → 2026-06-30T08:00:00+09:00
- **Direction**: UP
- **Close change**: +14.2 bp
- **OHLC**: O=161.71 H=161.97 L=161.68 C=161.94
- **Range**: 0.29

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 17.3 | 11.1 | No |
| baseline_random_walk | False | - | 14.2 | 14.2 | No |
| baseline_simple_technical | True | - | 0.7 | 0.7 | No |
| ugh_v2_alpha | True | True | 9.3 | 9.3 | No |
| ugh_v2_beta | True | False | 11.1 | 11.1 | No |
| ugh_v2_delta | True | True | 10.3 | 10.3 | No |
| ugh_v2_gamma | True | True | 9.6 | 9.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **9.3 bp**
- Baseline direction hits: 1/3
