# FX Daily Report — 2026-11-18

Generated: 2026-11-18T16:33:17Z

## Run Summary

- **as_of_jst**: 2026-11-18T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261118T080000_v1_d2612e16d082dc9e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -5.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +27.6 | - |
| ugh_v2_alpha | UP | +7.6 | setup |
| ugh_v2_beta | UP | +4.7 | setup |
| ugh_v2_delta | UP | +6.4 | setup |
| ugh_v2_gamma | UP | +7.1 | setup |

## Previous Window Outcome

- **Window**: 2026-11-17T08:00:00+09:00 → 2026-11-18T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -5.0 bp
- **OHLC**: O=159.43 H=159.61 L=158.85 C=159.35
- **Range**: 0.76

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 8.8 | 8.8 | No |
| baseline_random_walk | False | - | 5.0 | 5.0 | No |
| baseline_simple_technical | False | - | 33.3 | 23.3 | No |
| ugh_v2_alpha | False | True | 12.8 | 2.8 | No |
| ugh_v2_beta | False | True | 8.7 | 1.4 | No |
| ugh_v2_delta | False | True | 10.7 | 0.7 | No |
| ugh_v2_gamma | False | True | 12.5 | 2.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **12.8 bp**
- Baseline direction hits: 1/3
