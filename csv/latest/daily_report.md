# FX Daily Report — 2026-10-28

Generated: 2026-10-28T17:13:09Z

## Run Summary

- **as_of_jst**: 2026-10-28T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261028T080000_v1_ec192d9f2699613d
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +27.3 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -21.7 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | UP | +3.9 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-10-27T08:00:00+09:00 → 2026-10-28T08:00:00+09:00
- **Direction**: UP
- **Close change**: +27.3 bp
- **OHLC**: O=157.51 H=157.97 L=157.40 C=157.94
- **Range**: 0.57

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 16.7 | 16.7 | No |
| baseline_random_walk | False | - | 27.3 | 27.3 | No |
| baseline_simple_technical | False | - | 48.0 | 6.6 | No |
| ugh_v2_alpha | False | True | 27.3 | 27.3 | No |
| ugh_v2_beta | True | True | 22.3 | 22.3 | No |
| ugh_v2_delta | True | True | 23.8 | 23.8 | No |
| ugh_v2_gamma | False | True | 27.3 | 27.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **27.3 bp**
- Baseline direction hits: 1/3
