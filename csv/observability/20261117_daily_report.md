# FX Daily Report — 2026-11-17

Generated: 2026-11-17T16:57:13Z

## Run Summary

- **as_of_jst**: 2026-11-17T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261117T080000_v1_fc2ba1348d716a58
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -13.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +28.3 | - |
| ugh_v2_alpha | UP | +7.8 | setup |
| ugh_v2_beta | UP | +3.6 | setup |
| ugh_v2_delta | UP | +5.7 | setup |
| ugh_v2_gamma | UP | +7.4 | setup |

## Previous Window Outcome

- **Window**: 2026-11-16T08:00:00+09:00 → 2026-11-17T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -13.8 bp
- **OHLC**: O=159.63 H=159.88 L=159.33 C=159.41
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 3.1 | 3.1 | No |
| baseline_random_walk | False | - | 13.8 | 13.8 | No |
| baseline_simple_technical | False | - | 43.0 | 15.4 | No |
| ugh_v2_alpha | False | True | 20.6 | 6.9 | No |
| ugh_v2_beta | False | True | 17.1 | 10.5 | No |
| ugh_v2_delta | False | True | 18.7 | 8.8 | No |
| ugh_v2_gamma | False | True | 20.3 | 7.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **20.6 bp**
- Baseline direction hits: 1/3
