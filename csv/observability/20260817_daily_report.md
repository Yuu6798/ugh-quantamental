# FX Daily Report — 2026-08-17

Generated: 2026-08-17T05:40:08Z

## Run Summary

- **as_of_jst**: 2026-08-17T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260817T080000_v1_75c1d50eb8c448af
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -11.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -37.1 | - |
| ugh_v2_alpha | DOWN | -10.1 | setup |
| ugh_v2_beta | DOWN | -7.0 | setup |
| ugh_v2_delta | DOWN | -8.5 | setup |
| ugh_v2_gamma | DOWN | -8.6 | setup |

## Previous Window Outcome

- **Window**: 2026-08-14T08:00:00+09:00 → 2026-08-17T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -11.9 bp
- **OHLC**: O=159.49 H=159.53 L=158.58 C=159.30
- **Range**: 0.95

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 16.3 | 7.5 | No |
| baseline_random_walk | False | - | 11.9 | 11.9 | No |
| baseline_simple_technical | True | - | 24.7 | 24.7 | No |
| ugh_v2_alpha | True | True | 3.4 | 3.4 | No |
| ugh_v2_beta | True | True | 8.5 | 8.5 | No |
| ugh_v2_delta | True | True | 6.1 | 6.1 | No |
| ugh_v2_gamma | True | True | 4.3 | 4.3 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **3.4 bp**
- Baseline direction hits: 1/3
