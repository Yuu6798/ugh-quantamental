# FX Daily Report — 2026-11-02

Generated: 2026-11-02T17:14:02Z

## Run Summary

- **as_of_jst**: 2026-11-02T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261102T080000_v1_f8a9bb26724b7317
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -8.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -19.5 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-10-30T08:00:00+09:00 → 2026-11-02T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -8.2 bp
- **OHLC**: O=157.66 H=157.89 L=156.94 C=157.53
- **Range**: 0.95

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 1.3 | 1.3 | No |
| baseline_random_walk | False | - | 8.2 | 8.2 | No |
| baseline_simple_technical | True | - | 11.8 | 11.8 | No |
| ugh_v2_alpha | False | True | 8.2 | 8.2 | No |
| ugh_v2_beta | False | True | 8.2 | 8.2 | No |
| ugh_v2_delta | False | True | 8.2 | 8.2 | No |
| ugh_v2_gamma | False | True | 8.2 | 8.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **8.2 bp**
- Baseline direction hits: 2/3
