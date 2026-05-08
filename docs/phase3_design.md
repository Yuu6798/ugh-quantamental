# Phase 3 Design: Weekly / Monthly Report Builder Unification

This document is the design reference for Phase 3 of the
[`fx_protocol` refactoring plan](./refactoring_plan.md). Phase 3 was
deliberately gated on a written design — the audit identified a real
opportunity, but the previous phases' "extract obviously duplicated
helpers" pattern doesn't carry the whole way here. The two modules
diverge in load-bearing ways (output schema, caller convention) that
need to be addressed explicitly before any code moves.

## Status

| Phase | Status | PR |
|---|---|---|
| 1 | ✅ Done | #93 |
| 1.5 | ✅ Done | #95 |
| 2 | ✅ Done | #96 |
| **3a** | Proposed in this doc | — |
| 3b | Proposed in this doc | — |
| 3c | **Out of scope** for now | — |
| 3d | **Out of scope** for now | — |

Phase 3 ships as **two small sub-phases (3a, 3b)**. Two larger units
(3c, 3d) are explicitly out of scope and are documented here only so
future-me knows why they were skipped.

## Goals

- Eliminate the byte-equivalent helpers in
  `weekly_reports_v2.py` (722 LOC) and `monthly_review.py` (999 LOC).
- Preserve every public API path: `run_weekly_report_v2` and
  `run_monthly_review` signatures, output schemas of
  `weekly_strategy_metrics.csv` and `monthly_strategy_metrics.csv`,
  every JSON shape consumed downstream.
- Land each sub-phase as its own small PR with `ruff` + `pytest` +
  `semantic-ci check` green at every commit.

## Non-Goals

- **Do not unify the per-strategy metric output schema.** Weekly emits
  CSV-string fields (`"observation_count": "26"`, `"direction_hit_rate": "0.4615"`),
  monthly emits programmatic fields (`"forecast_count": 26, "direction_hit_rate": 0.4615`).
  This divergence is load-bearing: weekly's downstream is CSV export,
  monthly's downstream is JSON + governance flags.
- **Do not merge governance-only logic.** `compute_review_flags`
  (monthly, ~160 LOC) and `select_representative_cases` (monthly, ~40 LOC)
  have no weekly counterpart.
- **Do not refactor `build_slice_metrics` further.** Monthly already
  delegates to weekly's implementation; the residual divergence is a
  deliberate scoping choice (UGH-only + confirmed-annotation gate for
  monthly governance).
- **Do not change the CSV / JSON output contracts.** Any unification
  that would alter `weekly_strategy_metrics.csv` or
  `monthly_strategy_metrics.csv` field shapes is rejected.

## Audit summary

Mapped from `weekly_reports_v2.py` and `monthly_review.py` on `main`
post-Phase 2.

| Concern | Weekly | Monthly | Same? |
|---|---|---|---|
| Entry point | `run_weekly_report_v2` L609 | `run_monthly_review` L859 | Different signatures; weekly loads from disk, monthly receives pre-loaded data |
| Window resolution | `_resolve_week_window` L71 | `_resolve_month_window` L110 | **byte-equivalent** logic; only `business_day_count` default differs (5 vs 20) |
| Date check | `_is_in_week` L99 | `_is_in_window` L135 | **byte-identical** |
| Version stratification | `_stratify_by_versions` L179 | `_stratify_observations_by_versions` L820 | **byte-equivalent**; Spec §7.5 impl identical |
| Per-strategy metrics | `build_strategy_metrics` L424 | `compute_monthly_strategy_metrics` L145 | Different output schema (str vs float\|None) |
| Slice generation | `build_slice_metrics` L442 | `compute_monthly_slice_metrics` L803 | Monthly **already delegates** to weekly's |
| Annotation coverage | `build_annotation_coverage` L282 | `compute_annotation_coverage_summary` L432 | Same logic, renamed, slightly different output keys |
| Provider health | `build_provider_health_summary` L547 | `compute_provider_health_summary` L472 | Similar parsing, divergent output shapes |
| Review flags | — | `compute_review_flags` L592 | monthly-only |
| Representative cases | — | `select_representative_cases` L543 | monthly-only |
| Observation loading | `_load_labeled_observations_for_week` L161 | (caller pre-loads) | Fundamentally different |

## Phase 3a — Window resolution + version stratification

**Risk: low. Estimated net LOC: -70.**

The cleanest, safest extraction. Both functions are byte-equivalent
between the two modules and the unified API has no schema concerns.

### Module layout

New module: `fx_protocol/report_window.py`

```python
def resolve_business_day_window(
    report_date_jst: datetime,
    business_day_count: int,
) -> tuple[str, str]:
    """Return (start_yyyymmdd, end_yyyymmdd) walking back from the day
    before report_date_jst, collecting business_day_count Mon-Fri dates."""

def is_in_window(date_str: str, start_yyyymmdd: str, end_yyyymmdd: str) -> bool:
    """Inclusive YYYYMMDD range check."""

def stratify_observations_by_versions(
    rows: list[dict[str, str]],
    *,
    theory_version_filter: str | None = None,
    engine_version_filter: str | None = None,
) -> list[dict[str, str]]:
    """Spec §7.5 stratification: filter rows by theory_version /
    engine_version, with auto-detect when both filters are None and
    rows span multiple versions (latest wins, warning logged)."""
```

### Migration

| File | Change |
|---|---|
| `weekly_reports_v2.py` | Drop `_resolve_week_window`, `_is_in_week`, `_stratify_by_versions`. Import from `report_window`. Caller sites update from `_resolve_week_window(date)` → `resolve_business_day_window(date, business_day_count)` (signature already takes the param at the entry point). |
| `monthly_review.py` | Drop `_resolve_month_window`, `_is_in_window`, `_stratify_observations_by_versions`. Import from `report_window`. Caller sites update similarly. |
| `monthly_review_exports.py` | Drop the `_resolve_month_window` re-import (currently imports it from `monthly_review`). Import directly from `report_window` instead. |

### Public API impact

None. All three relocated symbols are private (leading-underscore) in
both source modules. `_resolve_month_window` is re-imported by
`monthly_review_exports.py`; that re-import path is internal and the
caller updates with the move.

### `target.yaml`

```yaml
intent: "Extract byte-equivalent window resolution and version stratification helpers from weekly_reports_v2 and monthly_review into shared fx_protocol/report_window. No behavior change, no public API change."
change:
  primary_kind: refactor
  allowed_secondary_kinds: [test_update]
  scope:
    modules:
      - ugh_quantamental.fx_protocol.report_window
      - ugh_quantamental.fx_protocol.weekly_reports_v2
      - ugh_quantamental.fx_protocol.monthly_review
      - ugh_quantamental.fx_protocol.monthly_review_exports
api_surface:
  allow_changes:
    - fqn: "fx_protocol.report_window.resolve_business_day_window"
    - fqn: "fx_protocol.report_window.is_in_window"
    - fqn: "fx_protocol.report_window.stratify_observations_by_versions"
constraints: []
```

`effects_unchanged` should be **satisfied** in 3a — these helpers don't
do file I/O, so no fs effects relocate.

## Phase 3b — Annotation coverage helper

**Risk: low. Estimated net LOC: -30.**

`build_annotation_coverage` (weekly) and `compute_annotation_coverage_summary`
(monthly) implement the same per-row counting (annotation_status =
"confirmed", source breakdown). They differ only in output dict keys
and a few derived totals.

### Module layout

New module: `fx_protocol/annotation_coverage.py`

```python
def count_annotation_sources(
    rows: list[dict[str, str]],
) -> dict[str, int]:
    """Return per-source counts: {ai_count, auto_count, manual_count,
    none_count, confirmed_count, total}."""
```

The two callers wrap this raw count into their preferred output shape:

- `weekly_reports_v2.build_annotation_coverage` becomes a thin adapter
  emitting weekly's keys.
- `monthly_review.compute_annotation_coverage_summary` becomes a thin
  adapter emitting monthly's keys.

### Migration

The existing function bodies are short (~30 LOC each); replace each
with a 5-10 LOC adapter that calls `count_annotation_sources` and maps
to the existing output keys. Output shapes are unchanged — verified by
existing tests.

### Public API impact

None. Both wrapper functions retain their existing names and shapes.

### `target.yaml`

Same `primary_kind: refactor` template. `allow_changes` declares only
the new `count_annotation_sources` fqn.

## Phase 3c — Observation loading bridge — *out of scope*

The audit identified that weekly loads from disk while monthly receives
pre-loaded observations. Bridging this would require:

1. Extracting `load_labeled_observations_for_window(csv_output_dir, start, end)`
   to a shared module.
2. Updating monthly's caller(s) to use the loader OR keeping monthly's
   "pre-loaded" entry signature and adding a thin wrapper.
3. Surveying every caller of `run_monthly_review` to confirm none
   relies on bypassing the loader.

This is a **caller-side architecture question**, not a duplication
problem. The shared loader's duplicate code surface is small (~15 LOC).
**Defer until there's a concrete reason** to centralize observation
loading — e.g. if a third pipeline appears that also needs this.

## Phase 3d — Metric row unification — *out of scope*

The audit noted that the per-strategy metric aggregators emit different
schemas (str vs `float | None`). A unification would look like:

- A shared core `compute_strategy_metric_row_core(rows) -> StrategyMetricRow`
  returning a frozen dataclass with `float | None` fields.
- Two output adapters: `to_weekly_csv_dict(row)` and `to_monthly_dict(row)`.

This is technically clean but **trades duplication for a new abstraction
layer** that has to be understood by every reader of either pipeline.
The current state — two divergent output shapes for two divergent
downstreams — is not actually obscure once you accept the schema split
as load-bearing.

**Defer indefinitely** unless a third report consumer materializes
that needs a third output shape. At that point, an adapter pattern
becomes load-bearing for real.

## Validation strategy (per sub-phase)

1. Branch off `main`: `claude/refactor-report-window` (3a),
   `claude/refactor-annotation-coverage` (3b).
2. Make the move.
3. `ruff check . && pytest -q` — must pass at every commit.
4. `semantic-ci check --baseline-rev main --candidate-rev HEAD --target .semantic-ci/target.yaml --package-root src/ugh_quantamental --format human --allow-dirty`.
   - For 3a: expect **all 4 satisfied** (helpers are pure, no fs effects).
   - For 3b: same.
5. PR description states which `target.yaml` constraints satisfied vs
   flagged-as-expected (cf. PR #93 / #96).
6. Merge before starting the next sub-phase.

## Out of scope (recap, with reasons)

| Item | Why deferred |
|---|---|
| Observation loading bridge (3c) | Architecture question, not a duplication problem; ~15 LOC duplicate code |
| Metric row schema unification (3d) | Adds an abstraction layer; current divergence is load-bearing not accidental |
| `build_slice_metrics` further unification | Monthly already delegates to weekly; residual divergence is intentional governance scoping |
| Provider health unification | Similar but divergent output shapes; would need adapter; ROI low |
| `compute_review_flags` / `select_representative_cases` | Monthly-only governance; no weekly counterpart |

## Acceptance criteria for Phase 3 complete

- 3a + 3b shipped, both PRs merged.
- `run_weekly_report_v2` and `run_monthly_review` signatures unchanged.
- `weekly_strategy_metrics.csv` and `monthly_strategy_metrics.csv` byte-
  identical to their pre-Phase-3 outputs (verified by existing fixture
  tests).
- All 1344+ tests pass throughout.
- Net LOC reduction: ~100 across `weekly_reports_v2.py` and `monthly_review.py`.
- 3c and 3d documented as deferred (this doc satisfies that).

## Default execution order after this PR merges

1. Phase 3a in its own PR (window + stratification)
2. Phase 3b in its own PR (annotation coverage)
3. Update `docs/refactoring_plan.md`'s status table (3a / 3b → ✅, 3c / 3d → "deferred per phase3_design.md")
4. Phase 3 closed; consider Phase 4 themes (TBD — no audit findings beyond what's covered above)
