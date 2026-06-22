# FX Daily Report — 2026-06-22

Generated: 2026-06-22T12:49:10Z

## Run Summary

- **as_of_jst**: 2026-06-22T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260622T080000_v1_9ddf0c8e31c667a7
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -5.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.5 | - |
| ugh_v2_alpha | UP | +3.6 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | UP | +3.5 | setup |

## Previous Window Outcome

- **Window**: 2026-06-19T08:00:00+09:00 → 2026-06-22T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -5.6 bp
- **OHLC**: O=161.37 H=161.45 L=160.98 C=161.28
- **Range**: 0.47

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 49.8 | 38.6 | No |
| baseline_random_walk | False | - | 5.6 | 5.6 | No |
| baseline_simple_technical | False | - | 20.5 | 9.4 | No |
| ugh_v2_alpha | False | False | 12.5 | 1.4 | No |
| ugh_v2_beta | False | False | 13.5 | 2.4 | No |
| ugh_v2_delta | False | False | 12.9 | 1.7 | No |
| ugh_v2_gamma | False | True | 12.3 | 1.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **12.5 bp**
- Baseline direction hits: 0/3
