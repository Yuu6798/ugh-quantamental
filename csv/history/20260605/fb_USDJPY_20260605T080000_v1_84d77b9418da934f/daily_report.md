# FX Daily Report — 2026-06-05

Generated: 2026-06-05T08:48:44Z

## Run Summary

- **as_of_jst**: 2026-06-05T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260605T080000_v1_84d77b9418da934f
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -1.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +17.1 | - |
| ugh_v2_alpha | UP | +6.2 | setup |
| ugh_v2_beta | UP | +4.4 | setup |
| ugh_v2_delta | UP | +5.2 | setup |
| ugh_v2_gamma | UP | +5.9 | setup |

## Previous Window Outcome

- **Window**: 2026-06-04T08:00:00+09:00 → 2026-06-05T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -1.2 bp
- **OHLC**: O=160.03 H=160.07 L=159.70 C=160.01
- **Range**: 0.37

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 10.0 | 7.5 | No |
| baseline_random_walk | False | - | 1.2 | 1.2 | No |
| baseline_simple_technical | False | - | 19.9 | 17.4 | No |
| ugh_v2_alpha | False | True | 10.7 | 8.2 | No |
| ugh_v2_beta | False | True | 10.1 | 7.6 | No |
| ugh_v2_delta | False | True | 10.3 | 7.8 | No |
| ugh_v2_gamma | False | True | 10.2 | 7.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **10.7 bp**
- Baseline direction hits: 0/3
