# FX Daily Report — 2026-10-05

Generated: 2026-10-05T19:50:14Z

## Run Summary

- **as_of_jst**: 2026-10-05T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261005T080000_v1_e97625a75109e25b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -17.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +43.1 | - |
| ugh_v2_alpha | UP | +12.4 | setup |
| ugh_v2_beta | UP | +6.8 | setup |
| ugh_v2_delta | UP | +9.6 | setup |
| ugh_v2_gamma | UP | +11.7 | setup |

## Previous Window Outcome

- **Window**: 2026-10-02T08:00:00+09:00 → 2026-10-05T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -17.7 bp
- **OHLC**: O=158.11 H=158.21 L=156.94 C=157.83
- **Range**: 1.27

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 60.3 | 24.9 | No |
| baseline_random_walk | False | - | 17.7 | 17.7 | No |
| baseline_simple_technical | False | - | 61.2 | 25.8 | No |
| ugh_v2_alpha | False | True | 43.6 | 8.2 | No |
| ugh_v2_beta | False | True | 46.3 | 10.9 | No |
| ugh_v2_delta | False | True | 46.0 | 10.6 | No |
| ugh_v2_gamma | False | True | 42.0 | 6.5 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **43.6 bp**
- Baseline direction hits: 0/3
