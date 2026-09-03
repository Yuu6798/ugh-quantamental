# FX Daily Report — 2026-09-03

Generated: 2026-09-03T15:04:01Z

## Run Summary

- **as_of_jst**: 2026-09-03T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260903T080000_v1_b7e6b9dc53c117bb
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -90.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +30.2 | - |
| ugh_v2_alpha | FLAT | +0.0 | setup |
| ugh_v2_beta | DOWN | -5.4 | failure |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-09-02T08:00:00+09:00 → 2026-09-03T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -90.5 bp
- **OHLC**: O=160.15 H=160.39 L=158.29 C=158.70
- **Range**: 2.10

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 118.1 | 63.0 | No |
| baseline_random_walk | False | - | 90.5 | 90.5 | No |
| baseline_simple_technical | False | - | 116.3 | 64.8 | No |
| ugh_v2_alpha | False | False | 104.1 | 77.0 | No |
| ugh_v2_beta | False | False | 107.1 | 73.9 | No |
| ugh_v2_delta | False | False | 105.7 | 75.4 | No |
| ugh_v2_gamma | False | False | 103.0 | 78.1 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **104.1 bp**
- Baseline direction hits: 0/3
