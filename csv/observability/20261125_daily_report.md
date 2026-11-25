# FX Daily Report — 2026-11-25

Generated: 2026-11-25T15:49:57Z

## Run Summary

- **as_of_jst**: 2026-11-25T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261125T080000_v1_6b6c7ef698ec9b6e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +20.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +26.4 | - |
| ugh_v2_alpha | UP | +6.0 | setup |
| ugh_v2_beta | UP | +8.1 | setup |
| ugh_v2_delta | UP | +7.3 | setup |
| ugh_v2_gamma | UP | +5.6 | setup |

## Previous Window Outcome

- **Window**: 2026-11-24T08:00:00+09:00 → 2026-11-25T08:00:00+09:00
- **Direction**: UP
- **Close change**: +20.1 bp
- **OHLC**: O=158.93 H=159.57 L=158.74 C=159.25
- **Range**: 0.83

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 7.0 | 7.0 | No |
| baseline_random_walk | False | - | 20.1 | 20.1 | No |
| baseline_simple_technical | True | - | 6.7 | 6.7 | No |
| ugh_v2_alpha | True | True | 12.4 | 12.4 | No |
| ugh_v2_beta | True | True | 9.8 | 9.8 | No |
| ugh_v2_delta | True | True | 10.9 | 10.9 | No |
| ugh_v2_gamma | True | True | 12.9 | 12.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **12.4 bp**
- Baseline direction hits: 2/3
