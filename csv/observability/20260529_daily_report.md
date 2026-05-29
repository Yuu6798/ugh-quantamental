# FX Daily Report — 2026-05-29

Generated: 2026-05-29T10:45:01Z

## Run Summary

- **as_of_jst**: 2026-05-29T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260529T080000_v1_9d785188fdd31da5
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -17.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +25.9 | - |
| ugh_v2_alpha | UP | +6.4 | dormant |
| ugh_v2_beta | UP | +3.1 | dormant |
| ugh_v2_delta | UP | +4.8 | dormant |
| ugh_v2_gamma | UP | +6.1 | dormant |

## Previous Window Outcome

- **Window**: 2026-05-28T08:00:00+09:00 → 2026-05-29T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -17.6 bp
- **OHLC**: O=159.51 H=159.65 L=159.11 C=159.23
- **Range**: 0.54

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 32.0 | 3.1 | No |
| baseline_random_walk | False | - | 17.6 | 17.6 | No |
| baseline_simple_technical | False | - | 54.5 | 19.4 | No |
| ugh_v2_alpha | False | True | 37.4 | 2.3 | No |
| ugh_v2_beta | False | True | 35.7 | 0.6 | No |
| ugh_v2_delta | False | True | 36.6 | 1.5 | No |
| ugh_v2_gamma | False | True | 35.8 | 0.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **37.4 bp**
- Baseline direction hits: 0/3
