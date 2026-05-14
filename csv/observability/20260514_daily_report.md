# FX Daily Report — 2026-05-14

Generated: 2026-05-14T12:22:56Z

## Run Summary

- **as_of_jst**: 2026-05-14T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260514T080000_v1_1b4346bf172c6fb7
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +16.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -39.0 | - |
| ugh_v2_alpha | DOWN | -0.7 | setup |
| ugh_v2_beta | UP | +3.9 | setup |
| ugh_v2_delta | UP | +1.7 | setup |
| ugh_v2_gamma | UP | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-05-13T08:00:00+09:00 → 2026-05-14T08:00:00+09:00
- **Direction**: UP
- **Close change**: +16.5 bp
- **OHLC**: O=157.59 H=157.92 L=157.51 C=157.85
- **Range**: 0.41

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 12.8 | 12.8 | No |
| baseline_random_walk | False | - | 16.5 | 16.5 | No |
| baseline_simple_technical | False | - | 55.2 | 22.2 | No |
| ugh_v2_alpha | False | True | 19.9 | 13.1 | No |
| ugh_v2_beta | True | True | 14.9 | 14.9 | No |
| ugh_v2_delta | False | True | 17.6 | 15.4 | No |
| ugh_v2_gamma | False | True | 19.7 | 13.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **19.9 bp**
- Baseline direction hits: 1/3
