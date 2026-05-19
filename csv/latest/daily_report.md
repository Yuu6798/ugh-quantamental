# FX Daily Report — 2026-05-19

Generated: 2026-05-19T10:36:54Z

## Run Summary

- **as_of_jst**: 2026-05-19T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260519T080000_v1_a0ab85008363a828
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +20.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +40.1 | - |
| ugh_v2_alpha | UP | +9.6 | setup |
| ugh_v2_beta | UP | +12.0 | setup |
| ugh_v2_delta | UP | +10.9 | setup |
| ugh_v2_gamma | UP | +9.0 | setup |

## Previous Window Outcome

- **Window**: 2026-05-18T08:00:00+09:00 → 2026-05-19T08:00:00+09:00
- **Direction**: UP
- **Close change**: +20.2 bp
- **OHLC**: O=158.51 H=159.08 L=158.50 C=158.83
- **Range**: 0.58

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 5.1 | 5.1 | No |
| baseline_random_walk | False | - | 20.2 | 20.2 | No |
| baseline_simple_technical | False | - | 59.9 | 19.6 | No |
| ugh_v2_alpha | True | True | 14.2 | 14.2 | No |
| ugh_v2_beta | True | True | 10.7 | 10.7 | No |
| ugh_v2_delta | True | True | 12.3 | 12.3 | No |
| ugh_v2_gamma | True | True | 14.3 | 14.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **14.2 bp**
- Baseline direction hits: 1/3
