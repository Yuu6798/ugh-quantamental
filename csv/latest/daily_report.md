# FX Daily Report — 2026-07-27

Generated: 2026-07-27T13:34:19Z

## Run Summary

- **as_of_jst**: 2026-07-27T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260727T080000_v1_cae380ddcd22c16a
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +0.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +23.6 | - |
| ugh_v2_alpha | UP | +8.0 | setup |
| ugh_v2_beta | UP | +6.2 | setup |
| ugh_v2_delta | UP | +7.0 | setup |
| ugh_v2_gamma | UP | +7.6 | setup |

## Previous Window Outcome

- **Window**: 2026-07-24T08:00:00+09:00 → 2026-07-27T08:00:00+09:00
- **Direction**: UP
- **Close change**: +0.6 bp
- **OHLC**: O=163.83 H=163.93 L=163.62 C=163.84
- **Range**: 0.31

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 43.5 | 43.5 | No |
| baseline_random_walk | False | - | 0.6 | 0.6 | No |
| baseline_simple_technical | True | - | 23.1 | 23.1 | No |
| ugh_v2_alpha | True | True | 12.2 | 12.2 | No |
| ugh_v2_beta | True | True | 14.6 | 14.6 | No |
| ugh_v2_delta | True | True | 13.5 | 13.5 | No |
| ugh_v2_gamma | True | True | 11.3 | 11.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **12.2 bp**
- Baseline direction hits: 2/3
