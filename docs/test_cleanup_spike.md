# Test Cleanup Spike — `test_models.py` Sample Labeling

A 25-test spike against the largest test file (`tests/fx_protocol/test_models.py`,
1,437 LOC, 129 tests) to validate the "Pydantic redundancy" hypothesis from
[`test_metrics.md`](./test_metrics.md) and tighten the cut estimate before
investing in a full labeling rubric.

## Method

- 25 tests sampled across the file's structural buckets (enum existence,
  validator behavior, frozen-ness / `extra="forbid"`, JST canonicalization,
  cross-field model validators, parametrized field-level checks, etc.).
- Each labeled per the 5-category rubric:
  必要 / 推奨 / 条件付き / 統合可 / 不要 (see definitions in
  [`test_metrics.md`](./test_metrics.md#next-steps)).
- "Pydantic-guaranteed" was checked against `models.py` directly: a test
  is **不要** only when it asserts behavior `frozen=True` / `extra="forbid"`
  / `Enum(value)` would already produce.

## Sampled labels

| # | Test (line) | Label | Rationale |
|--:|---|---|---|
| 1 | `test_currency_pair_usdjpy_exists` (193) | **不要** | `CurrencyPair.USDJPY == CurrencyPair("USDJPY")` is a Python StrEnum tautology. |
| 2 | `test_strategy_kind_all_values` (197) | 必要 | Asserts the exact enum value set. Public-API contract; guards rename / removal. |
| 3 | `test_event_tag_all_values` (215) | 必要 | Same rationale as #2. (Could merge with #2 + #3 + similar via parametrize → also 統合可.) |
| 4 | `test_expected_range_valid` (228) | 推奨 | Smoke happy-path. Cheap insurance, low yield. |
| 5 | `test_expected_range_equal_bounds_is_valid` (234) | 必要 | Boundary case — confirms validator allows `low == high`, not `low < high`. |
| 6 | `test_expected_range_ordering_violated` (239) | 必要 | Custom `model_validator` (low ≤ high). Not Pydantic-guaranteed. |
| 7 | `test_expected_range_non_finite_low` (245) [param ×3] | 必要 | Custom `field_validator` rejecting NaN / ±Inf. Pydantic accepts these by default. |
| 8 | `test_expected_range_negative_low_price_raises` (257) [param ×2] | 必要 | Custom `field_validator` enforcing positive prices. Not Pydantic. |
| 9 | `test_disconfirmer_rule_valid` (317) | 推奨 | Smoke happy-path. |
| 10 | `test_disconfirmer_rule_none_threshold` (324) | 統合可 | Tests `Optional` behavior; could be merged with #9 via parametrize. |
| 11 | `test_forecast_record_ugh_frozen` (359) | **不要** | Tests Pydantic's `frozen=True` mechanism. |
| 12 | `test_forecast_record_extra_field_rejected` (447) | **不要** | Tests Pydantic's `extra="forbid"`. |
| 13 | `test_outcome_record_does_not_have_realized_state_proxy` (463) | 統合可 | Schema-absence assertion via `hasattr`. Could be one parametrized test over the absent-fields list. |
| 14 | `test_outcome_record_extra_field_rejected` (473) | **不要** | Tests Pydantic's `extra="forbid"`. |
| 15 | `test_outcome_record_non_finite_price_raises` (484) | 必要 | Custom validator (NaN / Inf). |
| 16 | `test_outcome_record_negative_price_raises` (490) [param ×4 fields] | 必要 | Custom validator over 4 price fields; already parametrized; ideal shape. |
| 17 | `test_outcome_record_direction_up_requires_close_gt_open` (528) | 必要 | Cross-field `model_validator` — domain invariant. |
| 18 | `test_outcome_record_direction_flat_requires_close_eq_open` (556) | 統合可 | Same shape as #17 + the down-case at L542; could parametrize all three directions. |
| 19 | `test_forecast_record_non_canonical_time_as_of_raises` (688) | 必要 | Domain rule (08:00 JST canonical hour). |
| 20 | `test_forecast_record_weekend_as_of_raises` (710) [param ×2] | 必要 | Domain rule (business-day-only as_of). |
| 21 | `test_forecast_record_naive_jst_fields_stored_as_jst_aware` (885) | 必要 | JST canonicalization behavior — custom validator output. |
| 22 | `test_forecast_record_utc_aware_jst_fields_canonicalized_to_jst` (894) | 統合可 | Sibling of #21; could be parametrized over `(naive, utc-aware) → expected JST`. |
| 23 | `test_outcome_record_event_happened_true_with_empty_tags_raises` (1005) | 必要 | Cross-field validator. |
| 24 | `test_evaluation_record_disconfirmer_explained_without_fired_disconfirmers_raises` (1036) | 必要 | Past-bug-pinned test (referenced via review ID `r2929027374` in section comment). Documented regression coverage. |
| 25 | `test_forecast_record_ugh_numeric_feature_non_finite_raises` (1136) [param 11×3 = 33 cases] | 必要 | Already-good parametrize over 11 UGH float fields × 3 bad values. Ideal pattern. |

## Distribution

| Label | Count | % | Action |
|---|---:|---:|---|
| 必要 | 15 | **60%** | Keep verbatim |
| 推奨 | 2 | 8% | Keep, low priority for review |
| 条件付き | 0 | 0% | (no DB / external-dep tests in this file) |
| 統合可 | 4 | 16% | Parametrize-merge with siblings; preserve cases, reduce LOC ~50% |
| **不要** | 4 | **16%** | Delete after sign-off |

## Findings

### 1. The "Pydantic redundancy" hypothesis only partially fires

Of 25 sampled tests, **4 (16%)** assert behavior Pydantic itself
guarantees:
- `*_extra_field_rejected` × 2 (Pydantic's `extra="forbid"`)
- `*_frozen` × 1 (Pydantic's `frozen=True`)
- `*_usdjpy_exists` (Python StrEnum mechanics)

This is **less than my earlier upper-bound guess of 25-40%**. The file
isn't bloated with bulk validation — it's a thorough, well-targeted
contract test suite for a domain-rich frozen-data module. **The
"1,437 LOC, only 1 commit" outlier signal is consistent with `models.py`
being a stable schema, not with the file being overgrown.**

### 2. Cross-field domain validators dominate

15/25 (60%) test custom `model_validator` / `field_validator` logic
that Pydantic itself doesn't enforce:
- direction × close-vs-open consistency
- JST canonicalization on naive / UTC-aware inputs
- 08:00 JST canonical hour rule
- business-day rule (Mon-Fri, weekend rejection)
- `event_happened` ↔ `event_tags` cross-field
- `disconfirmer_explained` ↔ `disconfirmers_hit` cross-field
- low ≤ high range invariant
- finite-only float validators (NaN / Inf rejected)

These tests are **load-bearing** for catching regressions in the custom
validator logic, which is the actual project IP in this module.

### 3. Past-bug pins are explicit

Section comments reference review-comment IDs (e.g.
`(r2929027374)`, `(r2928948835)`, `(r2929100995)`) — tagging tests as
having been added in response to specific past concerns. **This is
strong "do not delete" evidence**; even if a test looks redundant in
isolation, it's documented as a regression trap.

### 4. Parametrize hygiene is already good

Existing tests like `test_forecast_record_ugh_numeric_feature_non_finite_raises`
are parametrized 11 × 3 = 33 cases in one function. **Where parametrize
isn't used (sample items #18, #22), it's an opportunity but the LOC
yield is modest** — the tests are short.

## Updated cut estimate

### test_models.py specifically

Extrapolating the spike distribution to the full file (assuming the
sample is representative):

| Action | Sample rate | LOC impact (file = 1,437) |
|---|---:|---:|
| **不要 → delete** | 16% of tests | ~150-230 LOC |
| **統合可 → parametrize-merge** | 16% of tests, ~50% LOC saved | ~75-115 LOC |
| **必要 + 推奨 → keep** | 68% | unchanged |
| **Total reduction** | — | **~225-345 LOC = 16-24%** |

So `test_models.py` realistically loses **~16-24%** of its LOC, which
is **lower than my earlier upper-bound estimate of 25-40%**.

### Full top-8 cleanup pass

Updating my earlier prediction with the spike data:

| File | LOC | Updated cut estimate | Updated LOC saved |
|---|---:|---:|---:|
| `test_models.py` | 1,437 | **16-24%** (spike-validated) | 230-345 |
| `test_csv_exports.py` | 761 | 20-30% (csv_utils-aided dedup, unverified) | 150-230 |
| `test_reporting.py` | 1,017 | 8-12% (was 10-15%, downgraded) | 80-120 |
| `test_observability.py` | 891 | 8-12% | 70-110 |
| `test_outcomes.py` | 843 | 8-12% | 65-100 |
| `test_monthly_review.py` | 746 | 8-12% | 60-90 |
| `test_automation.py` | 915 | 5-8% (high integration value) | 45-75 |
| `test_analytics_annotations.py` | 841 | 5-10% (high churn = load-bearing) | 40-85 |
| **Top 8 total** | 7,451 | **9-14%** | **~740-1,150 LOC** |

### Revised total estimate

- Top 8 contribution: ~740-1,150 LOC
- Smaller-package contribution (selective `query` / `workflows` / `replay` consolidation): ~300-500 LOC
- **Realistic total: 1,000-1,650 LOC = 4-7% of 22,619 test LOC**

This is **lower than my pre-spike estimate of 7-11%**. The spike
disconfirmed the implicit assumption that `test_models.py` was a major
bloat source — it's actually a well-built contract suite.

## Recommendation

Given the modest yield (4-7% LOC reduction) versus the labeling cost
(reading 1,000+ tests), **the cleanup workstream is borderline ROI**.
Three options:

1. **Proceed with full labeling** of top 8 files. Lock in ~1,000-1,650
   LOC reduction. Cost: ~4-6 hours of focused review per file × 8
   files = real time investment. Yield: cleaner test surface, easier
   onboarding.
2. **Cherry-pick the certain wins only.** Delete the ~16% of test_models.py
   that's Pydantic-redundant (~30-60 LOC, since each `*_frozen` /
   `*_extra_rejected` test is short), and the equivalent in
   `test_csv_exports.py`, `test_observability.py`. Skip systematic
   labeling. Yield: ~150-300 LOC, ~1 hour of work.
3. **Defer the cleanup** until a different signal appears (e.g., a
   test files refuses to run in CI, or a refactor surfaces structural
   coupling). The metrics doc and this spike are the artifact; the
   cleanup itself can wait.

My read: **option 2 is the best ROI** — capture the obvious wins
without committing to a 1,000+ test review. Option 1 yields more but
the marginal LOC there is genuinely necessary regression coverage and
costs review time that's better spent on production code.

Whichever path, the **≤200 LOC + ≤1 commit files (~30 of 62 files)
remain out of scope** — they're cheap correct as-is.

## What I'd put on the agenda next

If the user picks option 2:

- Delete the 4 Pydantic-redundant tests in `test_models.py` (#1, #11,
  #12, #14 from this spike).
- Read `test_csv_exports.py` (761 LOC, 59 tests) and apply the same
  filter — flag any `*_frozen` / `*_extra_field` / Enum-tautology
  tests for deletion. Estimated yield: ~100-150 LOC.
- Read `test_observability.py` artifact-builder tests for similar
  pattern; lower expectation (~50-100 LOC).
- One PR per file, gated on `pytest -q` staying green.

If option 1: write the labeling rubric formally in
`docs/test_cleanup_plan.md` first, then start file-by-file.
