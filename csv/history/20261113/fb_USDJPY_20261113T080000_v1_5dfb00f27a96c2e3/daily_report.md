# FX Daily Report — 2026-11-13

Generated: 2026-11-13T13:15:29Z

## Run Summary

- **as_of_jst**: 2026-11-13T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261113T080000_v1_5dfb00f27a96c2e3
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +5.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +28.7 | - |
| ugh_v2_alpha | UP | +10.0 | setup |
| ugh_v2_beta | UP | +7.9 | setup |
| ugh_v2_delta | UP | +8.7 | setup |
| ugh_v2_gamma | UP | +9.6 | setup |

## Previous Window Outcome

- **Window**: 2026-11-12T08:00:00+09:00 → 2026-11-13T08:00:00+09:00
- **Direction**: UP
- **Close change**: +5.0 bp
- **OHLC**: O=159.77 H=160.04 L=159.46 C=159.85
- **Range**: 0.58

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 59.2 | 59.2 | No |
| baseline_random_walk | False | - | 5.0 | 5.0 | No |
| baseline_simple_technical | True | - | 24.5 | 24.5 | No |
| ugh_v2_alpha | True | True | 3.8 | 3.8 | No |
| ugh_v2_beta | True | True | 6.2 | 6.2 | No |
| ugh_v2_delta | True | True | 5.0 | 5.0 | No |
| ugh_v2_gamma | True | True | 3.3 | 3.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.8 bp**
- Baseline direction hits: 2/3
