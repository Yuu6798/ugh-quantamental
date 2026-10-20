# FX Daily Report — 2026-10-20

Generated: 2026-10-20T10:12:30Z

## Run Summary

- **as_of_jst**: 2026-10-20T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261020T080000_v1_283301e934bba6d4
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +32.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +23.7 | - |
| ugh_v2_alpha | UP | +5.7 | setup |
| ugh_v2_beta | UP | +8.3 | setup |
| ugh_v2_delta | UP | +7.2 | setup |
| ugh_v2_gamma | UP | +5.2 | setup |

## Previous Window Outcome

- **Window**: 2026-10-19T08:00:00+09:00 → 2026-10-20T08:00:00+09:00
- **Direction**: UP
- **Close change**: +32.3 bp
- **OHLC**: O=157.97 H=158.54 L=157.68 C=158.48
- **Range**: 0.86

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 31.7 | 31.7 | No |
| baseline_random_walk | False | - | 32.3 | 32.3 | No |
| baseline_simple_technical | True | - | 8.1 | 8.1 | No |
| ugh_v2_alpha | True | True | 27.5 | 27.5 | No |
| ugh_v2_beta | True | True | 28.1 | 28.1 | No |
| ugh_v2_delta | True | True | 27.7 | 27.7 | No |
| ugh_v2_gamma | True | True | 27.8 | 27.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **27.5 bp**
- Baseline direction hits: 2/3
