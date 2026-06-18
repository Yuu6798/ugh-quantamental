# FX Daily Report — 2026-06-18

Generated: 2026-06-18T13:59:40Z

## Run Summary

- **as_of_jst**: 2026-06-18T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260618T080000_v1_1257b591ba5bde1b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +15.6 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.0 | - |
| ugh_v2_alpha | UP | +4.8 | setup |
| ugh_v2_beta | UP | +6.2 | setup |
| ugh_v2_delta | UP | +5.5 | setup |
| ugh_v2_gamma | UP | +4.6 | setup |

## Previous Window Outcome

- **Window**: 2026-06-17T08:00:00+09:00 → 2026-06-18T08:00:00+09:00
- **Direction**: UP
- **Close change**: +15.6 bp
- **OHLC**: O=160.38 H=160.79 L=160.10 C=160.63
- **Range**: 0.69

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 6.2 | 6.2 | No |
| baseline_random_walk | False | - | 15.6 | 15.6 | No |
| baseline_simple_technical | True | - | 2.9 | 2.9 | No |
| ugh_v2_alpha | True | True | 10.3 | 10.3 | No |
| ugh_v2_beta | True | True | 9.5 | 9.5 | No |
| ugh_v2_delta | True | True | 9.9 | 9.9 | No |
| ugh_v2_gamma | True | True | 10.6 | 10.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **True**
- UGH close error: **10.3 bp**
- Baseline direction hits: 2/3
