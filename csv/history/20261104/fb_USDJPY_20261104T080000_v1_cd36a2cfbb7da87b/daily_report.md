# FX Daily Report — 2026-11-04

Generated: 2026-11-04T15:32:27Z

## Run Summary

- **as_of_jst**: 2026-11-04T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261104T080000_v1_cd36a2cfbb7da87b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +46.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -21.6 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | UP | +4.9 | setup |
| ugh_v2_delta | UP | +3.9 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-11-03T08:00:00+09:00 → 2026-11-04T08:00:00+09:00
- **Direction**: UP
- **Close change**: +46.2 bp
- **OHLC**: O=157.93 H=158.76 L=157.73 C=158.66
- **Range**: 1.03

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 15.1 | 15.1 | No |
| baseline_random_walk | False | - | 46.2 | 46.2 | No |
| baseline_simple_technical | False | - | 66.0 | 26.5 | No |
| ugh_v2_alpha | False | True | 46.2 | 46.2 | No |
| ugh_v2_beta | True | True | 41.1 | 41.1 | No |
| ugh_v2_delta | True | True | 42.2 | 42.2 | No |
| ugh_v2_gamma | False | True | 46.2 | 46.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **46.2 bp**
- Baseline direction hits: 1/3
