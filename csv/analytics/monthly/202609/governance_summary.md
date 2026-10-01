# FX Monthly Governance Summary v1

**Review month**: 202609
**Overall judgment**: `logic_audit`

## Review Flags

- `inspect_magnitude_mapping`
- `inspect_state_mapping`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.42 | -7.41 bp | +12.61 bp |
| baseline_prev_day_direction | +0.05 | +14.23 bp | +6.64 bp |
| baseline_simple_technical | 0.00 | +9.74 bp | -10.63 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20260831-20260904 | 28 | - |  | 5 | 0 | 3 | 100.0% |
| 20260903-20260909 | 35 | - |  | 5 | 0 | 4 | 100.0% |
| 20260907-20260911 | 28 | - |  | 5 | 0 | 4 | 100.0% |
| 20260910-20260916 | 35 | - |  | 5 | 0 | 4 | 100.0% |
| 20260914-20260918 | 28 | - |  | 5 | 0 | 4 | 100.0% |
| 20260917-20260923 | 35 | - |  | 5 | 0 | 4 | 100.0% |
| 20260921-20260925 | 28 | - |  | 5 | 0 | 4 | 100.0% |
| 20260924-20260930 | 28 | - |  | 5 | 0 | 5 | 100.0% |

## Logic Audit Candidates

- magnitude/close-error mapping
- state-to-magnitude mapping

## Change Candidates

| ID | Category | Rationale | Status |
|---|---|---|---|
| CC-001 | logic_audit | UGH mean abs close error is 7.4 bp worse than baseline_random_walk (threshold... | proposed |
| CC-002 | logic_audit | State proxy hit rate (73.7%) is high but magnitude error (39.7 bp) exceeds th... | proposed |

## Version Decision

- **Update performed**: False
- **Unchanged**: theory_version, engine_version, schema_version, protocol_version
- **Note**: Version updates require human decision after logic audit investigation. This record is auto-generated; update fields manually if a version promotion is approved.

## Final Recommendation

> Review magnitude/close-error mapping in UGH engine. Review state-to-magnitude mapping — state hits are good but errors high.

---

*This governance summary is auto-generated from monthly review and weekly report artifacts. Logic modifications require human decision.*
