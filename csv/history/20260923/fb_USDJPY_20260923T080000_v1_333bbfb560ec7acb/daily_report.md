# FX Daily Report — 2026-09-23

Generated: 2026-09-23T10:08:11Z

## Run Summary

- **as_of_jst**: 2026-09-23T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260923T080000_v1_333bbfb560ec7acb
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +10.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +49.2 | - |
| ugh_v2_alpha | UP | +8.6 | setup |
| ugh_v2_beta | UP | +9.1 | setup |
| ugh_v2_delta | UP | +8.7 | setup |
| ugh_v2_gamma | UP | +8.1 | setup |

## Previous Window Outcome

- **Window**: 2026-09-22T08:00:00+09:00 → 2026-09-23T08:00:00+09:00
- **Direction**: UP
- **Close change**: +10.2 bp
- **OHLC**: O=157.21 H=157.77 L=156.80 C=157.37
- **Range**: 0.97

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 31.9 | 31.9 | No |
| baseline_random_walk | False | - | 10.2 | 10.2 | No |
| baseline_simple_technical | False | - | 59.3 | 39.0 | No |
| ugh_v2_alpha | True | True | 5.9 | 5.9 | No |
| ugh_v2_beta | True | True | 1.2 | 1.2 | No |
| ugh_v2_delta | True | True | 2.2 | 2.2 | No |
| ugh_v2_gamma | True | True | 5.9 | 5.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **5.9 bp**
- Baseline direction hits: 1/3
