# FX Daily Report — 2026-10-15

Generated: 2026-10-15T15:38:49Z

## Run Summary

- **as_of_jst**: 2026-10-15T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261015T080000_v1_8d3a919ff02ec0ab
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -2.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +27.0 | - |
| ugh_v2_alpha | UP | +5.6 | setup |
| ugh_v2_beta | UP | +4.0 | setup |
| ugh_v2_delta | UP | +5.0 | setup |
| ugh_v2_gamma | UP | +5.3 | setup |

## Previous Window Outcome

- **Window**: 2026-10-14T08:00:00+09:00 → 2026-10-15T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -2.5 bp
- **OHLC**: O=158.35 H=158.94 L=158.03 C=158.31
- **Range**: 0.91

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 17.0 | 17.0 | No |
| baseline_random_walk | False | - | 2.5 | 2.5 | No |
| baseline_simple_technical | False | - | 33.1 | 28.1 | No |
| ugh_v2_alpha | False | True | 6.5 | 1.4 | No |
| ugh_v2_beta | False | True | 2.5 | 2.5 | No |
| ugh_v2_delta | False | True | 2.5 | 2.5 | No |
| ugh_v2_gamma | False | True | 6.3 | 1.3 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **6.5 bp**
- Baseline direction hits: 1/3
