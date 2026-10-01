# FX Daily Report — 2026-10-01

Generated: 2026-10-01T11:42:13Z

## Run Summary

- **as_of_jst**: 2026-10-01T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261001T080000_v1_cf6f4291ffeae3b7
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +4.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +50.5 | - |
| ugh_v2_alpha | UP | +19.8 | setup |
| ugh_v2_beta | UP | +15.0 | setup |
| ugh_v2_delta | UP | +18.1 | setup |
| ugh_v2_gamma | UP | +18.7 | setup |

## Previous Window Outcome

- **Window**: 2026-09-30T08:00:00+09:00 → 2026-10-01T08:00:00+09:00
- **Direction**: UP
- **Close change**: +4.4 bp
- **OHLC**: O=157.32 H=157.52 L=156.35 C=157.39
- **Range**: 1.17

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 12.1 | 3.2 | No |
| baseline_random_walk | False | - | 4.4 | 4.4 | No |
| baseline_simple_technical | True | - | 50.3 | 50.3 | No |
| ugh_v2_alpha | True | True | 12.4 | 12.4 | No |
| ugh_v2_beta | True | True | 6.6 | 6.6 | No |
| ugh_v2_delta | True | True | 10.2 | 10.2 | No |
| ugh_v2_gamma | True | True | 11.4 | 11.4 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **12.4 bp**
- Baseline direction hits: 1/3
