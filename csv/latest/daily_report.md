# FX Daily Report — 2026-06-09

Generated: 2026-06-09T13:41:02Z

## Run Summary

- **as_of_jst**: 2026-06-09T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260609T080000_v1_c7e4b9ce509e89aa
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +1.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.8 | - |
| ugh_v2_alpha | UP | +6.5 | setup |
| ugh_v2_beta | UP | +5.2 | setup |
| ugh_v2_delta | UP | +5.8 | setup |
| ugh_v2_gamma | UP | +6.2 | setup |

## Previous Window Outcome

- **Window**: 2026-06-08T08:00:00+09:00 → 2026-06-09T08:00:00+09:00
- **Direction**: UP
- **Close change**: +1.9 bp
- **OHLC**: O=160.14 H=160.39 L=159.87 C=160.17
- **Range**: 0.52

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 15.6 | 15.6 | No |
| baseline_random_walk | False | - | 1.9 | 1.9 | No |
| baseline_simple_technical | True | - | 15.3 | 15.3 | No |
| ugh_v2_alpha | True | False | 7.9 | 7.9 | No |
| ugh_v2_beta | True | False | 9.0 | 9.0 | No |
| ugh_v2_delta | True | False | 8.4 | 8.4 | No |
| ugh_v2_gamma | True | False | 7.3 | 7.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **7.9 bp**
- Baseline direction hits: 2/3
