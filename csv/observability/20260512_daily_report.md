# FX Daily Report — 2026-05-12

Generated: 2026-05-12T13:02:20Z

## Run Summary

- **as_of_jst**: 2026-05-12T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260512T080000_v1_cb0c329c376c65eb
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +49.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -39.3 | - |
| ugh_v2_alpha | DOWN | -2.6 | setup |
| ugh_v2_beta | UP | +3.3 | setup |
| ugh_v2_delta | UP | +0.2 | setup |
| ugh_v2_gamma | DOWN | -2.4 | setup |

## Previous Window Outcome

- **Window**: 2026-05-11T08:00:00+09:00 → 2026-05-12T08:00:00+09:00
- **Direction**: UP
- **Close change**: +49.2 bp
- **OHLC**: O=156.39 H=157.27 L=156.39 C=157.16
- **Range**: 0.88

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 64.5 | 33.9 | No |
| baseline_random_walk | False | - | 49.2 | 49.2 | No |
| baseline_simple_technical | False | - | 86.1 | 12.3 | No |
| ugh_v2_alpha | False | True | 65.6 | 32.9 | No |
| ugh_v2_beta | False | True | 62.8 | 35.6 | No |
| ugh_v2_delta | False | True | 64.8 | 33.7 | No |
| ugh_v2_gamma | False | True | 64.8 | 33.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **65.6 bp**
- Baseline direction hits: 0/3
