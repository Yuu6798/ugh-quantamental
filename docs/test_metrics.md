# Test Suite Metrics

Discovery pass for the planned test-cleanup workstream. Captures per-file
size, test count, runtime, churn, and per-package test-to-source LOC ratios
on `main` as of this commit. The next step is to write a labeling rubric
(`必要 / 推奨 / 条件付き / 統合可 / 不要`) and apply it to the top of these
rankings — see [Next steps](#next-steps).

> **Method.** `find tests -name "*.py" -not -name "__init__.py"
> -not -name "conftest.py"` → 62 files, then per-file `wc -l`,
> `grep -cE '^[[:space:]]*def test_'` for test count, `git log --oneline
> -- <file> | wc -l` for churn, `pytest --durations=0` for runtime.

## Headline numbers

| Metric | Value |
|---|---:|
| Test files | 62 |
| Test functions (def test_…) | 1,152 |
| Pytest collected (incl. parametrize) | 1,344 |
| Total test LOC | 22,619 |
| Total source LOC | 16,719 |
| **Test:source LOC ratio** | **1.35 : 1** |
| Wall-clock for full suite | ~4–5 s |
| Slowest single test | 0.28 s (alembic migration) |

**Runtime is not a problem.** 4-5 seconds for the full suite on a single
core. The maintenance-burden complaint is structural (LOC per file +
churn), not throughput.

## Test:source ratio per package

| Package | Source LOC | Test LOC | Ratio | Comment |
|---|---:|---:|---:|---|
| `query` | 465 | 1,306 | **2.81 : 1** | Smallest package; tests dominate. Read-only inspection layer — low risk surface, plausibly over-tested. |
| `workflows` | 353 | 805 | **2.28 : 1** | Thin synchronous orchestration; tests likely include scenario coverage that overlaps engine + persistence layers. |
| `replay` | 1,493 | 3,025 | **2.03 : 1** | Replay layer has dedicated batch / suites / baselines test files. Some overlap likely between batch and single-run. |
| `persistence` | 822 | 1,439 | 1.75 : 1 | ORM + Alembic; ratio reasonable for DB-touching code. |
| `schemas` | 265 | 367 | 1.39 : 1 | Frozen Pydantic models; ratio low because Pydantic itself does most validation. |
| `engine` | 1,537 | 1,897 | 1.23 : 1 | Pure functions; reasonable. |
| `fx_protocol` | 11,784 | 13,767 | 1.17 : 1 | The bulk of the code. Lowest ratio — but largest absolute test LOC. |

**Hot candidates by ratio:** `query`, `workflows`, `replay`. These are
small packages where the test suite outweighs the production code. Worth
a focused review of whether the tests duplicate framework guarantees
(SQLAlchemy session lifecycle, Pydantic validation) or genuinely catch
behavior bugs.

## Top 15 test files by LOC

| LOC | Tests | File | Notes |
|---:|---:|---|---|
| 1,437 | 129 | `tests/fx_protocol/test_models.py` | Frozen Pydantic models. 129 tests on 660 LOC of `models.py` ⇒ likely heavy schema-validation coverage that Pydantic itself enforces. **Strong dedup candidate.** |
| 1,017 | 36 | `tests/fx_protocol/test_reporting.py` | Weekly report (V1). High churn-adjacent. |
| 915 | 46 | `tests/fx_protocol/test_automation.py` | Daily protocol orchestrator. Integration; many real-flow scenarios. |
| 891 | 32 | `tests/fx_protocol/test_observability.py` | Artifact builders. |
| 843 | 42 | `tests/fx_protocol/test_outcomes.py` | Outcome / evaluation logic. |
| 841 | 42 | `tests/fx_protocol/test_analytics_annotations.py` | Highest churn (7 commits). |
| 761 | 59 | `tests/fx_protocol/test_csv_exports.py` | 59 tests on a CSV writer — possibly over-asserting format. |
| 746 | 36 | `tests/fx_protocol/test_monthly_review.py` | Monthly review. |
| 713 | 23 | `tests/query/test_readers.py` | Query layer dominates the package's ratio. |
| 682 | 18 | `tests/replay/test_batch.py` | Largest replay test; overlap with `test_runners` and `test_suites` plausible. |
| 578 | 29 | `tests/fx_protocol/test_weekly_report_v2.py` | 6 commits. |
| 534 | 16 | `tests/replay/test_suites.py` | |
| 500 | 14 | `tests/engine/test_state.py` | Pure-engine tests. |
| 485 | 18 | `tests/replay/test_baselines.py` | |
| 480 | 21 | `tests/fx_protocol/test_automation_csv_exports.py` | |

**80/20 read.** The top 8 files (≥700 LOC each) account for ~7,400 LOC,
roughly **a third of the entire test suite**. The top 13 files (≥500 LOC)
account for ~50%. Labeling effort should start here.

## Top 15 by git churn (commits touching the file)

| Commits | File |
|---:|---|
| 7 | `tests/fx_protocol/test_analytics_annotations.py` |
| 6 | `tests/fx_protocol/test_weekly_report_v2.py` |
| 4 | `tests/persistence/test_review_audit_repositories.py` |
| 4 | `tests/fx_protocol/test_data_sources_alphavantage.py` |
| 4 | `tests/fx_protocol/test_automation.py` |
| 3 | `tests/fx_protocol/test_weekly_report_exports.py` |
| 3 | `tests/fx_protocol/test_reporting.py` |
| 3 | `tests/fx_protocol/test_monthly_review_exports.py` |
| 3 | `tests/fx_protocol/test_market_ugh_builder.py` |
| 3 | `tests/fx_protocol/test_forecasting.py` |
| 3 | `tests/fx_protocol/test_automation_csv_exports.py` |
| 3 | `tests/fx_protocol/test_analytics_rebuild.py` |
| 2 | (multiple files) |

**Churn observation.** The top 5 by churn live in `fx_protocol/` and
overlap with the top-LOC list (`test_analytics_annotations`,
`test_weekly_report_v2`, `test_automation`). High churn × high LOC =
high ongoing maintenance cost — these files pay the most ROI from
consolidation work.

## Aggregate runtime per file (top 20)

| Time | File |
|---:|---|
| 0.300 s | `tests/persistence/test_baseline_repositories.py` |
| 0.290 s | `tests/fx_protocol/test_automation_csv_exports.py` |
| 0.230 s | `tests/query/test_readers.py` |
| 0.180 s | `tests/query/test_review_audit_readers.py` |
| 0.170 s | `tests/persistence/test_db.py` |
| 0.170 s | `tests/fx_protocol/test_automation.py` |
| 0.160 s | `tests/fx_protocol/test_observability.py` |
| 0.110 s | `tests/replay/test_review_audit_replay.py` |
| 0.080 s | `tests/fx_protocol/test_outcomes.py` |
| 0.070 s | `tests/fx_protocol/test_reporting.py` |
| 0.060 s | `tests/replay/test_batch.py` |
| ≤ 0.05 s | (all remaining files) |

**Runtime tail is essentially flat.** No single file is a wall-clock
problem. Cuts will be motivated by *understandability* and
*maintainability*, not speed.

## Cross-cut: combining the signals

Files that score high on both **LOC** and **churn** are the highest-ROI
targets for the labeling pass:

| File | LOC | Tests | Churn | Notes |
|---|---:|---:|---:|---|
| `tests/fx_protocol/test_analytics_annotations.py` | 841 | 42 | 7 | After Phase 2 split, may have overlap with `test_labeled_observations` (none yet). |
| `tests/fx_protocol/test_weekly_report_v2.py` | 578 | 29 | 6 | Mostly v2 engine + slice metrics. |
| `tests/fx_protocol/test_automation.py` | 915 | 46 | 4 | Integration scenarios. |
| `tests/fx_protocol/test_models.py` | 1,437 | 129 | 1 | Highest LOC, only 1 commit since written. **Bulk-validation suspect** — many tests may duplicate `extra="forbid"` / `frozen=True` Pydantic guarantees. |
| `tests/fx_protocol/test_csv_exports.py` | 761 | 59 | 1 | Many tests for a CSV writer that's now backed by `csv_utils`. Format-assertion redundancy likely. |

`test_models.py` and `test_csv_exports.py` look most like "1 file =
many years of accreted assertions" — those are where the consolidation
yield will be highest.

## Cross-cut: low-LOC, low-churn files (likely OK)

These are small, stable, single-concern files. Probably stay
untouched in the labeling pass; flag here only so we don't waste cycles
re-classifying them.

| File | LOC | Tests |
|---|---:|---:|
| `tests/schemas/test_market_svp.py` | < 100 | a handful |
| `tests/fx_protocol/test_calendar.py` | small | small |
| `tests/fx_protocol/test_request_builders.py` | small | small |
| (most files under 200 LOC) | | |

A clear rule of thumb: **anything ≤ 200 LOC and ≤ 1 commit of churn is
out of scope for the cleanup pass.** ~30 of the 62 files fit this
profile; doing nothing to them is the cheap correct answer.

## Next steps

1. **Write labeling rubric** in `docs/test_cleanup_plan.md`. Five
   categories (per the conversation that produced this doc):

   | Label | Definition |
   |---|---|
   | 必要 | Public API contract / production regression caught / spec-mandated numerical reproduction. **Never delete.** |
   | 推奨 | Internal behavior hard to verify by other means; covers boundary conditions. **Keep, possibly merge.** |
   | 条件付き | Platform / DB / external dependency / OS-specific. **Keep but tag with marker so opt-in.** |
   | 統合可 | Behaves identically to a sibling test; a single parametrize / shared fixture would cover both. **Merge first, then drop.** |
   | 不要 | Asserts a Pydantic / type-checker / SQLAlchemy guarantee, or fully duplicates another `必要 / 推奨` test. **Delete after sign-off.** |

   The criteria definitions need to be settled in writing **before**
   any test gets a label, so labels are reproducible across reviewers.

2. **Apply rubric to the top 8 files** (~33% of test LOC):
   `test_models.py`, `test_reporting.py`, `test_automation.py`,
   `test_observability.py`, `test_outcomes.py`,
   `test_analytics_annotations.py`, `test_csv_exports.py`,
   `test_monthly_review.py`. One audit pass per file, output a
   labeled list per test.

3. **Cull or consolidate** in small PRs, one file at a time, gated on
   `pytest -q` staying green.

4. **Re-measure** after each PR to track progress (LOC delta, test
   count delta).

The remaining 54 files (mostly < 200 LOC) are out of scope unless the
top-8 audit surfaces a structural problem that propagates downward.
