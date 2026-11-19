# FX Daily Report — 2026-11-19

Generated: 2026-11-19T16:39:01Z

## Run Summary

- **as_of_jst**: 2026-11-19T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261119T080000_v1_a150b6605f471095
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -1.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +27.6 | - |
| ugh_v2_alpha | UP | +10.8 | setup |
| ugh_v2_beta | UP | +7.9 | setup |
| ugh_v2_delta | UP | +9.2 | setup |
| ugh_v2_gamma | UP | +10.1 | setup |

## Previous Window Outcome

- **Window**: 2026-11-18T08:00:00+09:00 → 2026-11-19T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -1.9 bp
- **OHLC**: O=159.36 H=159.65 L=159.11 C=159.33
- **Range**: 0.54

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 3.1 | 3.1 | No |
| baseline_random_walk | False | - | 1.9 | 1.9 | No |
| baseline_simple_technical | False | - | 29.4 | 25.7 | No |
| ugh_v2_alpha | False | True | 9.5 | 5.7 | No |
| ugh_v2_beta | False | True | 6.6 | 2.8 | No |
| ugh_v2_delta | False | True | 8.3 | 4.5 | No |
| ugh_v2_gamma | False | True | 9.0 | 5.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **9.5 bp**
- Baseline direction hits: 1/3
