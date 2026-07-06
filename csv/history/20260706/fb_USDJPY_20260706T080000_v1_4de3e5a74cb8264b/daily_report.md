# FX Daily Report — 2026-07-06

Generated: 2026-07-06T11:26:08Z

## Run Summary

- **as_of_jst**: 2026-07-06T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260706T080000_v1_4de3e5a74cb8264b
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +17.4 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +18.6 | - |
| ugh_v2_alpha | UP | +8.6 | setup |
| ugh_v2_beta | UP | +11.9 | setup |
| ugh_v2_delta | UP | +10.9 | setup |
| ugh_v2_gamma | UP | +8.5 | setup |

## Previous Window Outcome

- **Window**: 2026-07-03T08:00:00+09:00 → 2026-07-06T08:00:00+09:00
- **Direction**: UP
- **Close change**: +17.4 bp
- **OHLC**: O=161.09 H=161.51 L=160.51 C=161.37
- **Range**: 1.00

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 110.2 | 75.5 | No |
| baseline_random_walk | False | - | 17.4 | 17.4 | No |
| baseline_simple_technical | True | - | 1.2 | 1.2 | No |
| ugh_v2_alpha | False | True | 17.4 | 17.4 | No |
| ugh_v2_beta | False | True | 17.4 | 17.4 | No |
| ugh_v2_delta | False | True | 17.4 | 17.4 | No |
| ugh_v2_gamma | False | True | 17.4 | 17.4 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **17.4 bp**
- Baseline direction hits: 1/3
