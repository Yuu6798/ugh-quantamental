# FX Daily Report — 2026-07-15

Generated: 2026-07-15T12:10:42Z

## Run Summary

- **as_of_jst**: 2026-07-15T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260715T080000_v1_60104c4db3180b16
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -11.7 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +23.4 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-07-14T08:00:00+09:00 → 2026-07-15T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -11.7 bp
- **OHLC**: O=162.42 H=162.46 L=161.62 C=162.23
- **Range**: 0.84

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 64.9 | 41.5 | No |
| baseline_random_walk | False | - | 11.7 | 11.7 | No |
| baseline_simple_technical | False | - | 35.0 | 11.6 | No |
| ugh_v2_alpha | False | False | 22.2 | 1.2 | No |
| ugh_v2_beta | False | False | 25.9 | 2.5 | No |
| ugh_v2_delta | False | False | 24.3 | 0.9 | No |
| ugh_v2_gamma | False | False | 21.4 | 1.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **22.2 bp**
- Baseline direction hits: 0/3
