# FX Monthly Governance Summary v1

**Review month**: 202608
**Overall judgment**: `logic_audit`

## Review Flags

- `regime_direction_collapse`
- `volatility_direction_collapse`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.39 | -3.89 bp | +5.96 bp |
| baseline_prev_day_direction | +0.04 | +13.95 bp | +7.02 bp |
| baseline_simple_technical | -0.04 | +25.18 bp | +13.82 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20260803-20260807 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260804-20260810 | 35 | - |  | 5 | 0 | 0 | 100.0% |
| 20260810-20260814 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260811-20260817 | 35 | - |  | 5 | 0 | 0 | 100.0% |
| 20260817-20260821 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260818-20260824 | 49 | - |  | 5 | 0 | 0 | 100.0% |
| 20260824-20260828 | 21 | - |  | 4 | 0 | 3 | 100.0% |
| 20260825-20260831 | 42 | - |  | 4 | 0 | 4 | 100.0% |

## Logic Audit Candidates

- regime-stratified direction logic
- volatility-stratified direction logic

## Change Candidates

| ID | Category | Rationale | Status |
|---|---|---|---|
| CC-001 | logic_audit | UGH direction rate collapsed below 40% in confirmed regime slice(s): trending... | proposed |
| CC-002 | logic_audit | UGH direction rate collapsed below 40% in confirmed volatility slice(s): norm... | proposed |

## Version Decision

- **Update performed**: False
- **Unchanged**: theory_version, engine_version, schema_version, protocol_version
- **Note**: Version updates require human decision after logic audit investigation. This record is auto-generated; update fields manually if a version promotion is approved.

## Final Recommendation

> Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

---

*This governance summary is auto-generated from monthly review and weekly report artifacts. Logic modifications require human decision.*
