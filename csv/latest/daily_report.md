# FX Daily Report — 2026-10-14

Generated: 2026-10-14T12:56:00Z

## Run Summary

- **as_of_jst**: 2026-10-14T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261014T080000_v1_36928e664e56e44a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -19.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +30.6 | - |
| ugh_v2_alpha | UP | +3.9 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | UP | +3.8 | setup |

## Previous Window Outcome

- **Window**: 2026-10-13T08:00:00+09:00 → 2026-10-14T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -19.5 bp
- **OHLC**: O=158.60 H=158.66 L=157.81 C=158.29
- **Range**: 0.85

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 50.5 | 11.4 | No |
| baseline_random_walk | False | - | 19.5 | 19.5 | No |
| baseline_simple_technical | False | - | 51.5 | 12.5 | No |
| ugh_v2_alpha | False | True | 32.3 | 6.8 | No |
| ugh_v2_beta | False | True | 35.1 | 4.0 | No |
| ugh_v2_delta | False | True | 33.9 | 5.2 | No |
| ugh_v2_gamma | False | True | 31.1 | 8.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **32.3 bp**
- Baseline direction hits: 0/3
