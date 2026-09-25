# FX Daily Report — 2026-09-25

Generated: 2026-09-25T12:49:47Z

## Run Summary

- **as_of_jst**: 2026-09-25T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260925T080000_v1_1e1fee1afff866e4
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +34.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +53.2 | - |
| ugh_v2_alpha | UP | +46.5 | setup |
| ugh_v2_beta | UP | +43.0 | setup |
| ugh_v2_delta | UP | +43.9 | setup |
| ugh_v2_gamma | UP | +44.0 | setup |

## Previous Window Outcome

- **Window**: 2026-09-24T08:00:00+09:00 → 2026-09-25T08:00:00+09:00
- **Direction**: UP
- **Close change**: +34.7 bp
- **OHLC**: O=158.28 H=159.03 L=157.77 C=158.83
- **Range**: 1.26

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 25.0 | 25.0 | No |
| baseline_random_walk | False | - | 34.7 | 34.7 | No |
| baseline_simple_technical | True | - | 17.1 | 17.1 | No |
| ugh_v2_alpha | True | True | 9.5 | 9.5 | No |
| ugh_v2_beta | True | True | 4.3 | 4.3 | No |
| ugh_v2_delta | True | True | 6.9 | 6.9 | No |
| ugh_v2_gamma | True | True | 11.3 | 11.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **9.5 bp**
- Baseline direction hits: 2/3
