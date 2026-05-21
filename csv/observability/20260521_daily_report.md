# FX Daily Report — 2026-05-21

Generated: 2026-05-21T08:39:18Z

## Run Summary

- **as_of_jst**: 2026-05-21T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260521T080000_v1_965fd2aab4f56ff2
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -8.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +39.1 | - |
| ugh_v2_alpha | UP | +11.3 | setup |
| ugh_v2_beta | UP | +8.0 | setup |
| ugh_v2_delta | UP | +9.6 | setup |
| ugh_v2_gamma | UP | +10.7 | setup |

## Previous Window Outcome

- **Window**: 2026-05-20T08:00:00+09:00 → 2026-05-21T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -8.8 bp
- **OHLC**: O=159.05 H=159.16 L=158.57 C=158.91
- **Range**: 0.59

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 24.5 | 6.9 | No |
| baseline_random_walk | False | - | 8.8 | 8.8 | No |
| baseline_simple_technical | False | - | 47.8 | 30.2 | No |
| ugh_v2_alpha | False | True | 22.7 | 5.1 | No |
| ugh_v2_beta | False | True | 23.4 | 5.8 | No |
| ugh_v2_delta | False | True | 23.0 | 5.4 | No |
| ugh_v2_gamma | False | True | 21.6 | 3.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **22.7 bp**
- Baseline direction hits: 0/3
