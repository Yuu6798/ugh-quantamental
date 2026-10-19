# FX Daily Report — 2026-10-19

Generated: 2026-10-19T10:59:02Z

## Run Summary

- **as_of_jst**: 2026-10-19T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261019T080000_v1_aed9d86581ac0804
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +0.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.2 | - |
| ugh_v2_alpha | UP | +4.8 | setup |
| ugh_v2_beta | UP | +4.2 | setup |
| ugh_v2_delta | UP | +4.5 | setup |
| ugh_v2_gamma | UP | +4.5 | setup |

## Previous Window Outcome

- **Window**: 2026-10-16T08:00:00+09:00 → 2026-10-19T08:00:00+09:00
- **Direction**: UP
- **Close change**: +0.6 bp
- **OHLC**: O=157.98 H=158.33 L=157.67 C=157.99
- **Range**: 0.66

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 21.5 | 20.2 | No |
| baseline_random_walk | False | - | 0.6 | 0.6 | No |
| baseline_simple_technical | True | - | 26.5 | 26.5 | No |
| ugh_v2_alpha | False | True | 0.6 | 0.6 | No |
| ugh_v2_beta | False | True | 0.6 | 0.6 | No |
| ugh_v2_delta | False | True | 0.6 | 0.6 | No |
| ugh_v2_gamma | False | True | 0.6 | 0.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **0.6 bp**
- Baseline direction hits: 1/3
