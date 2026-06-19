# FX Daily Report — 2026-06-19

Generated: 2026-06-19T11:21:09Z

## Run Summary

- **as_of_jst**: 2026-06-19T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260619T080000_v1_930a7f7166e3c0b3
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +44.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.9 | - |
| ugh_v2_alpha | UP | +6.9 | setup |
| ugh_v2_beta | UP | +8.0 | setup |
| ugh_v2_delta | UP | +7.3 | setup |
| ugh_v2_gamma | UP | +6.8 | setup |

## Previous Window Outcome

- **Window**: 2026-06-18T08:00:00+09:00 → 2026-06-19T08:00:00+09:00
- **Direction**: UP
- **Close change**: +44.2 bp
- **OHLC**: O=160.66 H=161.80 L=160.46 C=161.37
- **Range**: 1.34

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 28.6 | 28.6 | No |
| baseline_random_walk | False | - | 44.2 | 44.2 | No |
| baseline_simple_technical | True | - | 31.2 | 31.2 | No |
| ugh_v2_alpha | True | False | 39.4 | 39.4 | No |
| ugh_v2_beta | True | False | 38.0 | 38.0 | No |
| ugh_v2_delta | True | False | 38.6 | 38.6 | No |
| ugh_v2_gamma | True | False | 39.5 | 39.5 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **39.4 bp**
- Baseline direction hits: 2/3
