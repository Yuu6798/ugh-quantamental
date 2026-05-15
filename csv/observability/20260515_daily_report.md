# FX Daily Report — 2026-05-15

Generated: 2026-05-15T09:47:08Z

## Run Summary

- **as_of_jst**: 2026-05-15T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260515T080000_v1_92fbd925881519de
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +32.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -40.1 | - |
| ugh_v2_alpha | UP | +3.0 | setup |
| ugh_v2_beta | UP | +7.7 | setup |
| ugh_v2_delta | UP | +5.5 | setup |
| ugh_v2_gamma | UP | +3.2 | setup |

## Previous Window Outcome

- **Window**: 2026-05-14T08:00:00+09:00 → 2026-05-15T08:00:00+09:00
- **Direction**: UP
- **Close change**: +32.9 bp
- **OHLC**: O=157.83 H=158.42 L=157.40 C=158.35
- **Range**: 1.02

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 16.4 | 16.4 | No |
| baseline_random_walk | False | - | 32.9 | 32.9 | No |
| baseline_simple_technical | False | - | 72.0 | 6.1 | No |
| ugh_v2_alpha | False | True | 33.6 | 32.3 | No |
| ugh_v2_beta | True | True | 29.0 | 29.0 | No |
| ugh_v2_delta | True | True | 31.2 | 31.2 | No |
| ugh_v2_gamma | True | True | 32.9 | 32.9 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **33.6 bp**
- Baseline direction hits: 1/3
