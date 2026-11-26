# FX Daily Report — 2026-11-26

Generated: 2026-11-26T15:29:46Z

## Run Summary

- **as_of_jst**: 2026-11-26T08:00:00+09:00
- **forecast_batch_id**: fb_USDJPY_20261126T080000_v1_a26b9233bdeeaee2
- **forecast count**: 7
- **outcome recorded**: Yes
- **evaluation count**: 7
- **protocol_version**: v1

## Today's Forecasts

| Strategy | Direction | Expected Change (bp) | Dominant State |
|---|---|---|---|
| baseline_prev_day_direction | DOWN | -5.0 | - |
| baseline_random_walk | FLAT | +0.0 | - |
| baseline_simple_technical | UP | +26.4 | - |
| ugh_v2_alpha | UP | +2.5 | setup |
| ugh_v2_beta | FLAT | +0.0 | setup |
| ugh_v2_delta | FLAT | +0.0 | setup |
| ugh_v2_gamma | FLAT | +0.0 | setup |

## Previous Window Outcome

- **Window**: 2026-11-25T08:00:00+09:00 → 2026-11-26T08:00:00+09:00
- **Direction**: DOWN
- **Close change**: -5.0 bp
- **OHLC**: O=159.25 H=159.50 L=158.64 C=159.17
- **Range**: 0.86

## Evaluation Comparison

| Strategy | Dir Hit | Range Hit | Close Err (bp) | Magnitude Err (bp) | Disconfirmer |
|---|---|---|---|---|---|
| baseline_prev_day_direction | False | - | 25.2 | 15.1 | No |
| baseline_random_walk | False | - | 5.0 | 5.0 | No |
| baseline_simple_technical | False | - | 31.5 | 21.4 | No |
| ugh_v2_alpha | False | True | 11.1 | 1.0 | No |
| ugh_v2_beta | False | True | 13.2 | 3.1 | No |
| ugh_v2_delta | False | True | 12.3 | 2.3 | No |
| ugh_v2_gamma | False | True | 10.6 | 0.6 | No |

## Observation Notes

- UGH direction hit: **False**
- UGH range hit: **True**
- UGH close error: **11.1 bp**
- Baseline direction hits: 0/3
