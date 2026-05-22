# FX Daily Report — 2026-05-22

Generated: 2026-05-22T08:27:12Z

## Run Summary

- **as_of_jst**: 2026-05-22T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260522T080000_v1_bba5474b634b9928
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +5.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.6 | - |
| ugh_v2_alpha | UP | +16.8 | setup |
| ugh_v2_beta | UP | +14.6 | setup |
| ugh_v2_delta | UP | +15.7 | setup |
| ugh_v2_gamma | UP | +15.6 | setup |

## Previous Window Outcome

- **Window**: 2026-05-21T08:00:00+09:00 → 2026-05-22T08:00:00+09:00
- **Direction**: UP
- **Close change**: +5.0 bp
- **OHLC**: O=158.88 H=159.34 L=158.77 C=158.96
- **Range**: 0.57

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 13.8 | 3.8 | No |
| baseline_random_walk | False | - | 5.0 | 5.0 | No |
| baseline_simple_technical | True | - | 34.0 | 34.0 | No |
| ugh_v2_alpha | True | True | 6.3 | 6.3 | No |
| ugh_v2_beta | True | True | 3.0 | 3.0 | No |
| ugh_v2_delta | True | True | 4.5 | 4.5 | No |
| ugh_v2_gamma | True | True | 5.6 | 5.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **6.3 bp**
- Baseline direction hits: 1/3
