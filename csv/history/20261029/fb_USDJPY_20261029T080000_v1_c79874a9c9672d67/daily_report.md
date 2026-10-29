# FX Daily Report — 2026-10-29

Generated: 2026-10-29T14:29:01Z

## Run Summary

- **as_of_jst**: 2026-10-29T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261029T080000_v1_c79874a9c9672d67
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -5.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -21.8 | - |
| ugh_v2_alpha | DOWN | -3.4 | setup |
| ugh_v2_beta | DOWN | -3.3 | setup |
| ugh_v2_delta | DOWN | -3.6 | setup |
| ugh_v2_gamma | DOWN | -3.2 | setup |

## Previous Window Outcome

- **Window**: 2026-10-28T08:00:00+09:00 → 2026-10-29T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -5.7 bp
- **OHLC**: O=157.91 H=158.34 L=157.63 C=157.82
- **Range**: 0.71

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 33.0 | 21.6 | No |
| baseline_random_walk | False | - | 5.7 | 5.7 | No |
| baseline_simple_technical | True | - | 16.0 | 16.0 | No |
| ugh_v2_alpha | False | True | 5.7 | 5.7 | No |
| ugh_v2_beta | False | True | 9.6 | 1.8 | No |
| ugh_v2_delta | False | True | 5.7 | 5.7 | No |
| ugh_v2_gamma | False | True | 5.7 | 5.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **5.7 bp**
- Baseline direction hits: 1/3
