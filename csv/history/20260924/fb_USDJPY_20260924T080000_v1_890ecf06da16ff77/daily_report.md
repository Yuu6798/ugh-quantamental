# FX Daily Report — 2026-09-24

Generated: 2026-09-24T15:51:36Z

## Run Summary

- **as_of_jst**: 2026-09-24T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260924T080000_v1_890ecf06da16ff77
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +59.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +51.8 | - |
| ugh_v2_alpha | UP | +25.2 | setup |
| ugh_v2_beta | UP | +30.5 | setup |
| ugh_v2_delta | UP | +27.8 | setup |
| ugh_v2_gamma | UP | +23.4 | setup |

## Previous Window Outcome

- **Window**: 2026-09-23T08:00:00+09:00 → 2026-09-24T08:00:00+09:00
- **Direction**: UP
- **Close change**: +59.7 bp
- **OHLC**: O=157.35 H=158.39 L=157.31 C=158.29
- **Range**: 1.08

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 49.6 | 49.6 | No |
| baseline_random_walk | False | - | 59.7 | 59.7 | No |
| baseline_simple_technical | True | - | 10.5 | 10.5 | No |
| ugh_v2_alpha | True | True | 51.1 | 51.1 | No |
| ugh_v2_beta | True | True | 50.6 | 50.6 | No |
| ugh_v2_delta | True | True | 51.0 | 51.0 | No |
| ugh_v2_gamma | True | True | 51.7 | 51.7 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **51.1 bp**
- Baseline direction hits: 2/3
