# FX Daily Report — 2026-09-07

Generated: 2026-09-07T13:33:58Z

## Run Summary

- **as_of_jst**: 2026-09-07T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260907T080000_v1_763ab433efcbf98b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +26.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -36.4 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-09-04T08:00:00+09:00 → 2026-09-07T08:00:00+09:00
- **Direction**: UP
- **Close change**: +26.3 bp
- **OHLC**: O=155.83 H=156.74 L=155.27 C=156.24
- **Range**: 1.47

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 207.8 | 155.2 | No |
| baseline_random_walk | False | - | 26.3 | 26.3 | No |
| baseline_simple_technical | False | - | 63.4 | 10.8 | No |
| ugh_v2_alpha | False | True | 34.0 | 18.6 | No |
| ugh_v2_beta | False | True | 39.0 | 13.6 | No |
| ugh_v2_delta | False | True | 36.4 | 16.3 | No |
| ugh_v2_gamma | False | True | 33.6 | 19.0 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **34.0 bp**
- Baseline direction hits: 0/3
