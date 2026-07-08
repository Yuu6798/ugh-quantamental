# FX Daily Report — 2026-07-08

Generated: 2026-07-08T12:16:04Z

## Run Summary

- **as_of_jst**: 2026-07-08T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260708T080000_v1_e41ba89ebd4393c1
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +0.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +20.0 | - |
| ugh_v2_alpha | UP | +3.6 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | UP | +3.2 | setup |
| ugh_v2_gamma | UP | +3.5 | setup |

## Previous Window Outcome

- **Window**: 2026-07-07T08:00:00+09:00 → 2026-07-08T08:00:00+09:00
- **Direction**: UP
- **Close change**: +0.6 bp
- **OHLC**: O=162.08 H=162.18 L=161.66 C=162.09
- **Range**: 0.52

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 44.6 | 44.6 | No |
| baseline_random_walk | False | - | 0.6 | 0.6 | No |
| baseline_simple_technical | True | - | 20.1 | 20.1 | No |
| ugh_v2_alpha | True | False | 18.3 | 18.3 | No |
| ugh_v2_beta | True | False | 21.8 | 21.8 | No |
| ugh_v2_delta | True | False | 20.0 | 20.0 | No |
| ugh_v2_gamma | True | False | 18.2 | 18.2 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **18.3 bp**
- Baseline direction hits: 2/3
