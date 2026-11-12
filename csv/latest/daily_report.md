# FX Daily Report — 2026-11-12

Generated: 2026-11-12T13:53:15Z

## Run Summary

- **as_of_jst**: 2026-11-12T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261112T080000_v1_fdbf24f5cd42f766
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +64.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +29.5 | - |
| ugh_v2_alpha | UP | +8.8 | setup |
| ugh_v2_beta | UP | +11.3 | setup |
| ugh_v2_delta | UP | +10.0 | setup |
| ugh_v2_gamma | UP | +8.3 | setup |

## Previous Window Outcome

- **Window**: 2026-11-11T08:00:00+09:00 → 2026-11-12T08:00:00+09:00
- **Direction**: UP
- **Close change**: +64.3 bp
- **OHLC**: O=158.75 H=159.93 L=158.64 C=159.77
- **Range**: 1.29

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 11.7 | 11.7 | No |
| baseline_random_walk | False | - | 64.3 | 64.3 | No |
| baseline_simple_technical | True | - | 37.8 | 37.8 | No |
| ugh_v2_alpha | True | True | 58.6 | 58.6 | No |
| ugh_v2_beta | True | True | 55.7 | 55.7 | No |
| ugh_v2_delta | True | True | 57.0 | 57.0 | No |
| ugh_v2_gamma | True | True | 58.9 | 58.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **58.6 bp**
- Baseline direction hits: 2/3
