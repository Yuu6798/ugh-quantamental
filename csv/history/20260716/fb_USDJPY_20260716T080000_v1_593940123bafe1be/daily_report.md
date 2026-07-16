# FX Daily Report — 2026-07-16

Generated: 2026-07-16T07:26:44Z

## Run Summary

- **as_of_jst**: 2026-07-16T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260716T080000_v1_593940123bafe1be
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +1.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +22.7 | - |
| ugh_v2_alpha | UP | +4.3 | setup |
| ugh_v2_beta | UP | +3.8 | setup |
| ugh_v2_delta | UP | +4.0 | setup |
| ugh_v2_gamma | UP | +4.0 | setup |

## Previous Window Outcome

- **Window**: 2026-07-15T08:00:00+09:00 → 2026-07-16T08:00:00+09:00
- **Direction**: UP
- **Close change**: +1.2 bp
- **OHLC**: O=162.16 H=162.42 L=161.87 C=162.18
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 12.9 | 10.5 | No |
| baseline_random_walk | False | - | 1.2 | 1.2 | No |
| baseline_simple_technical | True | - | 22.2 | 22.2 | No |
| ugh_v2_alpha | False | True | 1.2 | 1.2 | No |
| ugh_v2_beta | False | True | 1.2 | 1.2 | No |
| ugh_v2_delta | False | True | 1.2 | 1.2 | No |
| ugh_v2_gamma | False | True | 1.2 | 1.2 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **1.2 bp**
- Baseline direction hits: 1/3
