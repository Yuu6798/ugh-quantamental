# FX Daily Report — 2026-05-11

Generated: 2026-05-11T08:29:36Z

## Run Summary

- **as_of_jst**: 2026-05-11T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260511T080000_v1_e7757c269fc42102
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -15.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.9 | - |
| ugh_v2_alpha | DOWN | -16.3 | setup |
| ugh_v2_beta | DOWN | -13.6 | setup |
| ugh_v2_delta | DOWN | -15.5 | setup |
| ugh_v2_gamma | DOWN | -15.6 | setup |

## Previous Window Outcome

- **Window**: 2026-05-08T08:00:00+09:00 → 2026-05-11T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -15.3 bp
- **OHLC**: O=156.89 H=156.99 L=156.42 C=156.65
- **Range**: 0.57

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 49.2 | 18.6 | No |
| baseline_random_walk | False | - | 15.3 | 15.3 | No |
| baseline_simple_technical | True | - | 21.9 | 21.9 | No |
| ugh_v2_alpha | True | True | 11.1 | 11.1 | No |
| ugh_v2_beta | False | True | 17.9 | 12.7 | No |
| ugh_v2_delta | True | True | 14.9 | 14.9 | No |
| ugh_v2_gamma | True | True | 11.3 | 11.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **11.1 bp**
- Baseline direction hits: 1/3
