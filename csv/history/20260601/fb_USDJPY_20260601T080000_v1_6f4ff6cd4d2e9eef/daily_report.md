# FX Daily Report — 2026-06-01

Generated: 2026-06-01T10:27:56Z

## Run Summary

- **as_of_jst**: 2026-06-01T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260601T080000_v1_6f4ff6cd4d2e9eef
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +3.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +24.6 | - |
| ugh_v2_alpha | UP | +10.3 | setup |
| ugh_v2_beta | UP | +8.8 | setup |
| ugh_v2_delta | UP | +9.7 | setup |
| ugh_v2_gamma | UP | +9.6 | setup |

## Previous Window Outcome

- **Window**: 2026-05-29T08:00:00+09:00 → 2026-06-01T08:00:00+09:00
- **Direction**: UP
- **Close change**: +3.1 bp
- **OHLC**: O=159.21 H=159.37 L=159.08 C=159.26
- **Range**: 0.29

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 20.7 | 14.4 | No |
| baseline_random_walk | False | - | 3.1 | 3.1 | No |
| baseline_simple_technical | True | - | 22.8 | 22.8 | No |
| ugh_v2_alpha | True | True | 3.3 | 3.3 | No |
| ugh_v2_beta | True | True | 0.0 | 0.0 | No |
| ugh_v2_delta | True | True | 1.6 | 1.6 | No |
| ugh_v2_gamma | True | True | 2.9 | 2.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.3 bp**
- Baseline direction hits: 1/3
