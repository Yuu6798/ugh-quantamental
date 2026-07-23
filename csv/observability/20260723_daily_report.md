# FX Daily Report — 2026-07-23

Generated: 2026-07-23T09:24:56Z

## Run Summary

- **as_of_jst**: 2026-07-23T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260723T080000_v1_cc7a6c949ff21cbd
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -1.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +21.6 | - |
| ugh_v2_alpha | UP | +5.5 | setup |
| ugh_v2_beta | UP | +4.2 | setup |
| ugh_v2_delta | UP | +4.7 | setup |
| ugh_v2_gamma | UP | +5.2 | setup |

## Previous Window Outcome

- **Window**: 2026-07-22T08:00:00+09:00 → 2026-07-23T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -1.8 bp
- **OHLC**: O=163.16 H=163.22 L=162.77 C=163.13
- **Range**: 0.45

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 44.3 | 40.6 | No |
| baseline_random_walk | False | - | 1.8 | 1.8 | No |
| baseline_simple_technical | False | - | 24.2 | 20.5 | No |
| ugh_v2_alpha | False | True | 11.3 | 7.6 | No |
| ugh_v2_beta | False | True | 13.8 | 10.1 | No |
| ugh_v2_delta | False | True | 12.6 | 8.9 | No |
| ugh_v2_gamma | False | True | 10.5 | 6.8 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **11.3 bp**
- Baseline direction hits: 0/3
