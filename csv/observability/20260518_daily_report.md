# FX Daily Report — 2026-05-18

Generated: 2026-05-18T11:06:30Z

## Run Summary

- **as_of_jst**: 2026-05-18T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260518T080000_v1_53324ea5f8bf85ef
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +25.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -39.8 | - |
| ugh_v2_alpha | UP | +5.9 | setup |
| ugh_v2_beta | UP | +9.5 | setup |
| ugh_v2_delta | UP | +7.9 | setup |
| ugh_v2_gamma | UP | +5.9 | setup |

## Previous Window Outcome

- **Window**: 2026-05-15T08:00:00+09:00 → 2026-05-18T08:00:00+09:00
- **Direction**: UP
- **Close change**: +25.3 bp
- **OHLC**: O=158.36 H=158.84 L=158.27 C=158.76
- **Range**: 0.57

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 7.7 | 7.7 | No |
| baseline_random_walk | False | - | 25.3 | 25.3 | No |
| baseline_simple_technical | False | - | 65.4 | 14.8 | No |
| ugh_v2_alpha | True | True | 22.3 | 22.3 | No |
| ugh_v2_beta | True | True | 17.6 | 17.6 | No |
| ugh_v2_delta | True | True | 19.8 | 19.8 | No |
| ugh_v2_gamma | True | True | 22.0 | 22.0 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **22.3 bp**
- Baseline direction hits: 1/3
