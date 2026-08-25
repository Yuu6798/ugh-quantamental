# FX Daily Report — 2026-08-25

Generated: 2026-08-25T07:41:27Z

## Run Summary

- **as_of_jst**: 2026-08-25T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260825T080000_v1_518a2aa54a52a054
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +12.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -41.7 | - |
| ugh_v2_alpha | UP | +3.7 | setup |
| ugh_v2_beta | UP | +6.4 | setup |
| ugh_v2_delta | UP | +5.0 | setup |
| ugh_v2_gamma | UP | +3.8 | setup |

## Previous Window Outcome

- **Window**: 2026-08-24T08:00:00+09:00 → 2026-08-25T08:00:00+09:00
- **Direction**: UP
- **Close change**: +12.0 bp
- **OHLC**: O=158.89 H=159.28 L=158.59 C=159.08
- **Range**: 0.69

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 17.0 | 6.9 | No |
| baseline_random_walk | False | - | 12.0 | 12.0 | No |
| baseline_simple_technical | False | - | 53.2 | 29.3 | No |
| ugh_v2_alpha | False | True | 12.0 | 12.0 | No |
| ugh_v2_beta | False | True | 12.0 | 12.0 | No |
| ugh_v2_delta | False | True | 12.0 | 12.0 | No |
| ugh_v2_gamma | False | True | 12.0 | 12.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **12.0 bp**
- Baseline direction hits: 0/3
