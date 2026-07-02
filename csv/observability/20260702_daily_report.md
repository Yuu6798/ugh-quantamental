# FX Daily Report — 2026-07-02

Generated: 2026-07-02T08:15:49Z

## Run Summary

- **as_of_jst**: 2026-07-02T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260702T080000_v1_153a509ebcd0811b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +2.5 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.0 | - |
| ugh_v2_alpha | UP | +6.0 | setup |
| ugh_v2_beta | UP | +4.9 | setup |
| ugh_v2_delta | UP | +5.4 | setup |
| ugh_v2_gamma | UP | +5.7 | setup |

## Previous Window Outcome

- **Window**: 2026-07-01T08:00:00+09:00 → 2026-07-02T08:00:00+09:00
- **Direction**: UP
- **Close change**: +2.5 bp
- **OHLC**: O=162.52 H=162.83 L=162.28 C=162.56
- **Range**: 0.55

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 35.2 | 35.2 | No |
| baseline_random_walk | False | - | 2.5 | 2.5 | No |
| baseline_simple_technical | True | - | 11.8 | 11.8 | No |
| ugh_v2_alpha | True | True | 8.8 | 8.8 | No |
| ugh_v2_beta | True | False | 9.8 | 9.8 | No |
| ugh_v2_delta | True | False | 9.3 | 9.3 | No |
| ugh_v2_gamma | True | True | 7.9 | 7.9 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **8.8 bp**
- Baseline direction hits: 2/3
