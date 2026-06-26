# FX Daily Report — 2026-06-26

Generated: 2026-06-26T13:06:00Z

## Run Summary

- **as_of_jst**: 2026-06-26T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260626T080000_v1_b982ed18c44e221e
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +1.2 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +13.6 | - |
| ugh_v2_alpha | UP | +6.0 | setup |
| ugh_v2_beta | UP | +4.6 | setup |
| ugh_v2_delta | UP | +5.2 | setup |
| ugh_v2_gamma | UP | +5.7 | setup |

## Previous Window Outcome

- **Window**: 2026-06-25T08:00:00+09:00 → 2026-06-26T08:00:00+09:00
- **Direction**: UP
- **Close change**: +1.2 bp
- **OHLC**: O=161.76 H=161.94 L=161.54 C=161.78
- **Range**: 0.40

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 16.7 | 16.7 | No |
| baseline_random_walk | False | - | 1.2 | 1.2 | No |
| baseline_simple_technical | True | - | 13.1 | 13.1 | No |
| ugh_v2_alpha | True | False | 8.9 | 8.9 | No |
| ugh_v2_beta | True | False | 9.5 | 9.5 | No |
| ugh_v2_delta | True | False | 9.1 | 9.1 | No |
| ugh_v2_gamma | True | False | 8.6 | 8.6 | No |

## Observation Notes

- UGH direction hit: **True**
- UGH range hit: **False**
- UGH close error: **8.9 bp**
- Baseline direction hits: 2/3
