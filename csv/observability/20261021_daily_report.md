# FX Daily Report — 2026-10-21

Generated: 2026-10-21T13:00:31Z

## Run Summary

- **as_of_jst**: 2026-10-21T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261021T080000_v1_daa1bbc072d4a6aa
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -19.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.1 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-10-20T08:00:00+09:00 → 2026-10-21T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -19.6 bp
- **OHLC**: O=158.47 H=158.59 L=157.81 C=158.16
- **Range**: 0.78

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 51.8 | 12.7 | No |
| baseline_random_walk | False | - | 19.6 | 19.6 | No |
| baseline_simple_technical | False | - | 43.2 | 4.1 | No |
| ugh_v2_alpha | False | True | 25.3 | 13.9 | No |
| ugh_v2_beta | False | True | 27.9 | 11.2 | No |
| ugh_v2_delta | False | True | 26.7 | 12.4 | No |
| ugh_v2_gamma | False | True | 24.8 | 14.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **25.3 bp**
- Baseline direction hits: 0/3
