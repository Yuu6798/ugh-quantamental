# FX Daily Report — 2026-11-05

Generated: 2026-11-05T15:36:42Z

## Run Summary

- **as_of_jst**: 2026-11-05T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261105T080000_v1_15f7f017a62fc1ea
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -15.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +22.2 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-11-04T08:00:00+09:00 → 2026-11-05T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -15.1 bp
- **OHLC**: O=158.66 H=158.74 L=157.39 C=158.42
- **Range**: 1.35

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 61.3 | 31.1 | No |
| baseline_random_walk | False | - | 15.1 | 15.1 | No |
| baseline_simple_technical | True | - | 6.4 | 6.4 | No |
| ugh_v2_alpha | False | True | 15.1 | 15.1 | No |
| ugh_v2_beta | False | True | 20.0 | 10.2 | No |
| ugh_v2_delta | False | True | 19.0 | 11.3 | No |
| ugh_v2_gamma | False | True | 15.1 | 15.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **15.1 bp**
- Baseline direction hits: 1/3
