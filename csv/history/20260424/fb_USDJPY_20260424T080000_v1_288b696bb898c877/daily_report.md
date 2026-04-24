# FX Daily Report — 2026-04-24

Generated: 2026-04-24T07:04:45Z

## Run Summary

- **as_of_jst**: 2026-04-24T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20260424T080000_v1_288b696bb898c877
- **forecast count**: 4
- **outcome recorded**: Yes
- **evaluation count**: 4
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | UP | +13.8 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | DOWN | -23.2 | - |
| ugh | DOWN | -0.1 | setup |

## Previous Window Outcome

- **Window**: 2026-04-23T08:00:00+09:00 → 2026-04-24T08:00:00+09:00
- **Direction**: UP
- **Close change**: +13.8 bp
- **OHLC**: O=159.49 H=159.84 L=159.28 C=159.71
- **Range**: 0.56

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | True | - | 6.3 | 6.3 | No |
| baseline_random_walk | False | - | 13.8 | 13.8 | No |
| baseline_simple_technical | False | - | 37.3 | 9.8 | No |
| ugh | False | True | 13.9 | 13.7 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **13.9 bp**
- Baseline direction hits: 1/3
