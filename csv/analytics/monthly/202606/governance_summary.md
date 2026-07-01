# FX Monthly Governance Summary v1

**Review month**: 202606
**Overall judgment**: `keep`

## Review Flags

- `keep_current_logic`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.74 | +0.87 bp | +2.68 bp |
| baseline_prev_day_direction | -0.16 | +6.71 bp | +3.47 bp |
| baseline_simple_technical | +0.05 | -0.55 bp | -1.24 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20260601-20260605 | 28 | - |  | 5 | 0 | 2 | 0.0% |
| 20260603-20260609 | 35 | - |  | 5 | 0 | 1 | 100.0% |
| 20260608-20260612 | 28 | - |  | 5 | 0 | 0 | 0.0% |
| 20260610-20260616 | 35 | - |  | 5 | 0 | 2 | 100.0% |
| 20260615-20260619 | 28 | - |  | 5 | 0 | 2 | 0.0% |
| 20260617-20260623 | 35 | - |  | 5 | 0 | 1 | 100.0% |
| 20260622-20260626 | 28 | - |  | 5 | 0 | 1 | 0.0% |
| 20260624-20260630 | 28 | - |  | 5 | 0 | 0 | 100.0% |

## Version Decision

- **Update performed**: False
- **Unchanged**: theory_version, engine_version, schema_version, protocol_version
- **Note**: Version updates require human decision after logic audit investigation. This record is auto-generated; update fields manually if a version promotion is approved.

## Final Recommendation

> All monthly metrics are within acceptable thresholds. Recommend keeping current logic unchanged for next period.

---

*This governance summary is auto-generated from monthly review and weekly report artifacts. Logic modifications require human decision.*
