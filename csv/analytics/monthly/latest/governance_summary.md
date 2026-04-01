# FX Monthly Governance Summary v1

**Review month**: 202603
**Overall judgment**: `data_provider_remediation`

## Review Flags

- `inspect_state_mapping`
- `missing_windows`

## Baseline Comparison Summary

| Baseline | Dir Delta | Close Err Delta | Mag Err Delta |
|---|---|---|---|
| baseline_random_walk | -0.71 | +0.11 bp | +0.24 bp |
| baseline_prev_day_direction | -0.29 | +41.44 bp | -8.05 bp |
| baseline_simple_technical | 0.00 | -3.57 bp | -18.10 bp |

## Weekly Trends

| Week | Obs | UGH Dir Rate | UGH Mean Err | Prov OK | Prov Fail | Fallback | Ann Cov |
|---|---|---|---|---|---|---|---|
| 20260304-20260310 | 0 | - |  | 0 | 0 | 0 | 0.0% |
| 20260311-20260317 | 0 | - |  | 0 | 0 | 0 | 0.0% |
| 20260318-20260324 | 12 | 66.7% | 54.27 | 0 | 0 | 0 | 100.0% |
| 20260323-20260327 | 20 | 80.0% | 35.18 | 2 | 0 | 0 | 100.0% |
| 20260325-20260331 | 16 | 75.0% | 30.02 | 4 | 0 | 1 | 100.0% |

## Logic Audit Candidates

- state-to-magnitude mapping

## Provider / Annotation Concerns

- Missing window rate (65.0%) exceeds threshold (25%). Missing: 13/20.

## Change Candidates

| ID | Category | Rationale | Status |
|---|---|---|---|
| CC-001 | logic_audit | State proxy hit rate (100.0%) is high but magnitude error (40.3 bp) exceeds t... | proposed |
| CC-002 | data_provider_remediation | Missing window rate (65.0%) exceeds threshold (25%). Missing: 13/20. | proposed |

## Version Decision

- **Update performed**: False
- **Unchanged**: theory_version, engine_version, schema_version, protocol_version
- **Note**: Version updates require human decision after logic audit investigation. This record is auto-generated; update fields manually if a version promotion is approved.

## Final Recommendation

> Review state-to-magnitude mapping — state hits are good but errors high. Investigate missing protocol windows.

---

*This governance summary is auto-generated from monthly review and weekly report artifacts. Logic modifications require human decision.*
