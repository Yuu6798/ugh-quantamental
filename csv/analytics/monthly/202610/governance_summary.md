# FX Monthly Governance Summary v1

**Review month**: 202610
**Overall judgment**: `logic_audit`

## Review Flags

- `regime_direction_collapse`
- `volatility_direction_collapse`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.33 | -1.44 bp | +3.29 bp |
| baseline_prev_day_direction | +0.28 | +5.88 bp | +2.19 bp |
| baseline_simple_technical | +0.11 | +12.59 bp | +2.04 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20261005-20261009 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20261012-20261016 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20261019-20261023 | 28 | - |  | 4 | 0 | 2 | 100.0% |
| 20261026-20261030 | 28 | - |  | 5 | 0 | 0 | 100.0% |

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
