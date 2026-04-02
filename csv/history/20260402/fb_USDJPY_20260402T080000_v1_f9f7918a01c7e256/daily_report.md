# FX Daily Report — 2026-04-02

Generated: 2026-04-02T06:13:13Z

## Run Summary

- **as_of_jst**: 2026-04-02T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260402T080000_v1_f9f7918a01c7e256
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +5.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +38.3 | - |
| ugh | UP | +0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-01T08:00:00+09:00 → 2026-04-02T08:00:00+09:00
- **Direction**: UP
- **Close change**: +5.0 bp
- **OHLC**: O=158.70 H=159.01 L=158.25 C=158.78
- **Range**: 0.76

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 68.9 | 58.8 | No |
| baseline_random_walk | False | - | 5.0 | 5.0 | No |
| baseline_simple_technical | True | - | 34.4 | 34.4 | No |
| ugh | True | True | 4.8 | 4.8 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **4.8 bp**
- Baseline direction hits: 1/3
