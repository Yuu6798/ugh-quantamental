# FX Monthly Governance Summary v1

**Review month**: 202607
**Overall judgment**: `logic_audit`

## Review Flags

- `inspect_direction_logic`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.58 | -2.22 bp | +1.88 bp |
| baseline_prev_day_direction | +0.05 | +9.25 bp | +4.87 bp |
| baseline_simple_technical | +0.11 | +5.06 bp | -0.37 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20260706-20260710 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260713-20260717 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260720-20260724 | 28 | - |  | 5 | 0 | 0 | 100.0% |
| 20260727-20260731 | 28 | - |  | 5 | 0 | 0 | 100.0% |

## Logic Audit Candidates

- direction prediction logic

## Change Candidates

| ID | Category | Rationale | Status |
|---|---|---|---|
| CC-001 | logic_audit | UGH direction accuracy is 10.5 pct points below baseline_simple_technical (th... | proposed |

## Version Decision

- **Update performed**: False
- **Unchanged**: theory_version, engine_version, schema_version, protocol_version
- **Note**: Version updates require human decision after logic audit investigation. This record is auto-generated; update fields manually if a version promotion is approved.

## Final Recommendation

> Review direction prediction logic — baseline outperforming.

---

*This governance summary is auto-generated from monthly review and weekly report artifacts. Logic modifications require human decision.*
