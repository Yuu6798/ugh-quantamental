# FX Daily Report — 2026-06-24

Generated: 2026-06-24T13:14:08Z

## Run Summary

- **as_of_jst**: 2026-06-24T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260624T080000_v1_54973e6654fcfe12
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +3.1 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +14.2 | - |
| ugh_v2_alpha | UP | +7.1 | setup |
| ugh_v2_beta | UP | +5.7 | setup |
| ugh_v2_delta | UP | +6.3 | setup |
| ugh_v2_gamma | UP | +7.0 | setup |

## Previous Window Outcome

- **Window**: 2026-06-23T08:00:00+09:00 → 2026-06-24T08:00:00+09:00
- **Direction**: UP
- **Close change**: +3.1 bp
- **OHLC**: O=161.52 H=161.73 L=161.25 C=161.57
- **Range**: 0.48

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 14.3 | 14.3 | No |
| baseline_random_walk | False | - | 3.1 | 3.1 | No |
| baseline_simple_technical | True | - | 12.2 | 12.2 | No |
| ugh_v2_alpha | True | True | 5.5 | 5.5 | No |
| ugh_v2_beta | True | True | 6.5 | 6.5 | No |
| ugh_v2_delta | True | True | 6.0 | 6.0 | No |
| ugh_v2_gamma | True | True | 5.4 | 5.4 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **5.5 bp**
- Baseline direction hits: 2/3
