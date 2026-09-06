# FX Monthly Governance Summary v1

**Review month**: 202608
**Overall judgment**: `logic_audit`

## Review Flags

- `inspect_magnitude_mapping`
- `regime_direction_collapse`
- `volatility_direction_collapse`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.32 | -5.53 bp | +7.23 bp |
| baseline_prev_day_direction | +0.05 | +15.90 bp | +7.30 bp |
| baseline_simple_technical | 0.00 | +21.31 bp | +9.33 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20260803-20260807 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260804-20260810 | 35 | - |  | 5 | 0 | 0 | 100.0% |
| 20260810-20260814 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260811-20260817 | 35 | - |  | 5 | 0 | 0 | 100.0% |
| 20260817-20260821 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260818-20260824 | 35 | - |  | 5 | 0 | 0 | 100.0% |
| 20260824-20260828 | 21 | - |  | 4 | 0 | 3 | 100.0% |
| 20260825-20260831 | 28 | - |  | 4 | 0 | 4 | 100.0% |

## Logic Audit Candidates

- magnitude/close-error mapping
- regime-stratified direction logic
- volatility-stratified direction logic

## Change Candidates

| ID | Category | Rationale | Status |
|---|---|---|---|
| CC-001 | logic_audit | UGH mean abs close error is 5.5 bp worse than baseline_random_walk (threshold... | proposed |
| CC-002 | logic_audit | UGH direction rate collapsed below 40% in confirmed regime slice(s): trending... | proposed |
| CC-003 | logic_audit | UGH direction rate collapsed below 40% in confirmed volatility slice(s): norm... | proposed |

## Version Decision

- **Update performed**: False
- **Unchanged**: theory_version, engine_version, schema_version, protocol_version
- **Note**: Version updates require human decision after logic audit investigation. This record is auto-generated; update fields manually if a version promotion is approved.

## Final Recommendation

> Review magnitude/close-error mapping in UGH engine. Review direction logic per regime — a confirmed regime slice collapsed despite an acceptable blended metric. Review direction logic per volatility regime — a confirmed volatility slice collapsed despite an acceptable blended metric.

---

*This governance summary is auto-generated from monthly review and weekly report artifacts. Logic modifications require human decision.*
