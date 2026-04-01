# FX Daily Report — 2026-04-01

Generated: 2026-04-01T06:27:03Z

## Run Summary

- **as_of_jst**: 2026-04-01T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260401T080000_v1_7bd536eef16ba5bb
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -63.9 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +39.4 | - |
| ugh | UP | +0.2 | setup |

## Previous Window Outcome

- **Window**: 2026-03-31T08:00:00+09:00 → 2026-04-01T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -63.9 bp
- **OHLC**: O=159.73 H=159.97 L=158.64 C=158.71
- **Range**: 1.33

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 53.2 | 53.2 | No |
| baseline_random_walk | False | - | 63.9 | 63.9 | No |
| baseline_simple_technical | False | - | 101.1 | 26.6 | No |
| ugh | False | False | 64.3 | 63.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **False**
- UGH close error: **64.3 bp**
- Baseline direction hits: 1/3
