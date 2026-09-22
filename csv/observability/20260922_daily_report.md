# FX Daily Report — 2026-09-22

Generated: 2026-09-22T15:33:30Z

## Run Summary

- **as_of_jst**: 2026-09-22T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260922T080000_v1_f014954ca4af52b0
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +42.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -49.2 | - |
| ugh_v2_alpha | UP | +4.3 | setup |
| ugh_v2_beta | UP | +11.4 | setup |
| ugh_v2_delta | UP | +8.0 | setup |
| ugh_v2_gamma | UP | +4.3 | setup |

## Previous Window Outcome

- **Window**: 2026-09-21T08:00:00+09:00 → 2026-09-22T08:00:00+09:00
- **Direction**: UP
- **Close change**: +42.1 bp
- **OHLC**: O=156.70 H=157.52 L=156.56 C=157.36
- **Range**: 0.96

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 18.2 | 18.2 | No |
| baseline_random_walk | False | - | 42.1 | 42.1 | No |
| baseline_simple_technical | False | - | 89.8 | 5.5 | No |
| ugh_v2_alpha | False | True | 42.1 | 42.1 | No |
| ugh_v2_beta | True | True | 34.6 | 34.6 | No |
| ugh_v2_delta | False | True | 42.1 | 42.1 | No |
| ugh_v2_gamma | False | True | 42.1 | 42.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **42.1 bp**
- Baseline direction hits: 1/3
