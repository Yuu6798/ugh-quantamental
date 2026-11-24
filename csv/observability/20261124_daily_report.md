# FX Daily Report — 2026-11-24

Generated: 2026-11-24T21:23:05Z

## Run Summary

- **as_of_jst**: 2026-11-24T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261124T080000_v1_437054f195c0f933
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +27.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +26.8 | - |
| ugh_v2_alpha | UP | +7.8 | setup |
| ugh_v2_beta | UP | +10.4 | setup |
| ugh_v2_delta | UP | +9.3 | setup |
| ugh_v2_gamma | UP | +7.3 | setup |

## Previous Window Outcome

- **Window**: 2026-11-23T08:00:00+09:00 → 2026-11-24T08:00:00+09:00
- **Direction**: UP
- **Close change**: +27.1 bp
- **OHLC**: O=158.57 H=159.50 L=158.52 C=159.00
- **Range**: 0.98

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 99.8 | 45.5 | No |
| baseline_random_walk | False | - | 27.1 | 27.1 | No |
| baseline_simple_technical | True | - | 0.5 | 0.5 | No |
| ugh_v2_alpha | False | True | 27.1 | 27.1 | No |
| ugh_v2_beta | False | True | 27.1 | 27.1 | No |
| ugh_v2_delta | False | True | 27.1 | 27.1 | No |
| ugh_v2_gamma | False | True | 27.1 | 27.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **27.1 bp**
- Baseline direction hits: 1/3
