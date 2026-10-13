# FX Daily Report — 2026-10-13

Generated: 2026-10-13T18:23:31Z

## Run Summary

- **as_of_jst**: 2026-10-13T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261013T080000_v1_9f1b7537fdebe686
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +31.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +32.0 | - |
| ugh_v2_alpha | UP | +12.7 | setup |
| ugh_v2_beta | UP | +15.5 | setup |
| ugh_v2_delta | UP | +14.4 | setup |
| ugh_v2_gamma | UP | +11.6 | setup |

## Previous Window Outcome

- **Window**: 2026-10-12T08:00:00+09:00 → 2026-10-13T08:00:00+09:00
- **Direction**: UP
- **Close change**: +31.0 bp
- **OHLC**: O=158.12 H=158.75 L=158.06 C=158.61
- **Range**: 0.69

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 2.5 | 2.5 | No |
| baseline_random_walk | False | - | 31.0 | 31.0 | No |
| baseline_simple_technical | True | - | 2.7 | 2.7 | No |
| ugh_v2_alpha | True | True | 15.8 | 15.8 | No |
| ugh_v2_beta | True | True | 13.3 | 13.3 | No |
| ugh_v2_delta | True | True | 14.2 | 14.2 | No |
| ugh_v2_gamma | True | True | 17.1 | 17.1 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **15.8 bp**
- Baseline direction hits: 2/3
