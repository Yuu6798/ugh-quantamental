# `fx_protocol` Refactoring Plan

This document captures the prioritized refactor backlog for `src/ugh_quantamental/fx_protocol/`.
It exists so that future sessions can pick up without re-investigating: each phase has scope,
expected public-API impact, and the `target.yaml` shape required to gate it under semantic-ci.

> **Out of scope**: feature work (tracked in `PLANS.md` / milestones), formal v1 specs
> (live in `docs/specs/`), and changes to `engine/`, `persistence/`, frozen Pydantic
> schemas, or the `naive-UTC` persistence boundary — see [Do not touch](#do-not-touch).

## Status

| Phase | Title | Status | PR |
|---|---|---|---|
| 1 | Extract `csv_utils` + `metrics_utils` | ✅ Done | #93 |
| 1.5 | Consolidate `monthly_review` `_safe_*` helpers into `metrics_utils` | ✅ Done | #95 |
| 2 | Split `analytics_annotations.py` (1028 LOC) | ✅ Done | #96 |
| 3a | Extract `report_window` (window + version stratification) | Designed, see [`phase3_design.md`](./phase3_design.md) | — |
| 3b | Extract `annotation_coverage` shared core | Designed, see [`phase3_design.md`](./phase3_design.md) | — |
| 3c | Observation-loading bridge | Deferred — see design doc | — |
| 3d | Metric row schema unification | Deferred — see design doc | — |

Picking the next phase: see [Picking what to do next](#picking-what-to-do-next).

## Original audit findings

From an Explore-agent audit of `src/ugh_quantamental/fx_protocol/` (~17 K LOC across 30+
modules). Findings are ranked by **impact × low-risk**, with file citations as of `main`
post-#93.

### High impact

- **`_write_csv` / `write_csv_artifact` / `write_csv_rows` triplication** — 6 call sites
  with the same `csv.DictWriter(..., extrasaction=...)` body (`csv_exports`,
  `observability`, `analytics_annotations`, `monthly_review_exports`,
  `weekly_report_exports`). **→ Phase 1 ✅**
- **`_count_bool` / `_collect_floats` triplication** — byte-identical bodies in
  `analytics_annotations`, `weekly_reports_v2`, `monthly_review`. **→ Phase 1 ✅**
- **`_safe_rate` / `_safe_mean` / `_safe_median` divergent triplication** —
  `monthly_review.py:135-150` returns `float | None` (rounded), `weekly_reports_v2.py:104-119`
  returns `str` (rounded, empty for None), `reporting.py:109` returns `float | None`
  (unrounded). Same intent, three return-type conventions. **→ Phase 1.5**
- **`analytics_annotations.py` (1028 LOC)** mixes four concerns: AI draft generation
  (≈L130-300), labeled observations build (≈L451-700), slice analytics (≈L701-917),
  and CSV I/O. **→ Phase 2**

### Medium impact

- **`weekly_reports_v2.py` (738 LOC) + `monthly_review.py` (1027 LOC) parallel
  pipelines** — both load labeled observations, slice by version, compute strategy
  metrics, derive review flags. Window arithmetic is duplicated. **→ Phase 3**
- **`save_run` boilerplate in `persistence/repositories.py`** — three `save_run`
  methods (`ProjectionRunRepository`, `ReviewAuditRunRepository`, `StateRunRepository`)
  follow identical structure. Outside `fx_protocol/` so deferred; touches DB code.

### Low / skip

- **Long single-purpose functions** (`_build_ai_annotation_row`,
  `_collect_labeled_observation_rows`) — 80+ LOC each but tightly scoped; extraction
  cost > benefit.
- **Repository payload variance** (`ProjectionRunRepository` vs
  `StateRunRepository`) — structural symmetry is intentional, payloads differ.
- **Frozen-model `ConfigDict` repetition** — Pydantic best practice, not duplication.

## Phased plan

### Phase 1 ✅ — Extract `csv_utils` + `metrics_utils`

Done in PR #93. New canonical modules: `fx_protocol/csv_utils.py` (`write_csv_rows`,
`append_csv_row`), `fx_protocol/metrics_utils.py` (`count_bool_rows`, `collect_floats`).
Public re-exports preserve `csv_exports.write_csv_rows`, `observability.write_csv_artifact`,
`observability.append_csv_row`. Net `-39 LOC`.

### Phase 1.5 — Migrate `_safe_rate` / `_safe_mean` / `_safe_median`

**Goal**: Move the `float | None` versions from `monthly_review.py` and `reporting.py`
into `metrics_utils`. Keep the **`str`-returning versions in `weekly_reports_v2.py`
local** — they're CSV-format helpers, not pure stats.

**Scope**:

- Add to `fx_protocol/metrics_utils.py`:
  - `safe_rate(numerator: int, denominator: int, *, ndigits: int | None = 4) -> float | None`
  - `safe_mean(values: list[float], *, ndigits: int | None = 2) -> float | None`
  - `safe_median(values: list[float], *, ndigits: int | None = 2) -> float | None`
  - `ndigits=None` skips rounding (matches `reporting._safe_mean`); positive int rounds.
- Update `monthly_review.py` callers (≈ L192-447) to import from `metrics_utils`,
  drop local `_safe_rate` / `_safe_mean` / `_safe_median`.
- Update `reporting.py:_safe_mean` callers to use `safe_mean(values, ndigits=None)`,
  drop local helper.
- Leave `weekly_reports_v2._safe_rate` / `_safe_mean` / `_safe_median` (str-returning
  CSV formatters) **untouched** — different return type, different responsibility.

**Public API impact**: zero. All affected names are private (`_`-prefix).

**`target.yaml`**:

```yaml
intent: "Move float|None safe_rate/safe_mean/safe_median into metrics_utils. Behavior preserved."
change:
  primary_kind: refactor
  allowed_secondary_kinds: [test_update]
  scope:
    modules:
      - ugh_quantamental.fx_protocol.metrics_utils
      - ugh_quantamental.fx_protocol.monthly_review
      - ugh_quantamental.fx_protocol.reporting
api_surface:
  allow_changes:
    - fqn: "fx_protocol.metrics_utils.safe_rate"
    - fqn: "fx_protocol.metrics_utils.safe_mean"
    - fqn: "fx_protocol.metrics_utils.safe_median"
constraints: []
```

**Validation**: `ruff check . && pytest -q`. Expected size: ~80 LOC removed across
2 files, ~30 added in `metrics_utils`.

### Phase 2 — Split `analytics_annotations.py`

**Goal**: Split the 1028-LOC module into responsibility-aligned files. The
**labeled observations builder is the obvious extraction**: it is the input
substrate for `weekly_reports_v2`, `monthly_review`, and `analytics_annotations`'s
own slice analytics — but its construction logic accidentally sits inside
analytics. Pulling it out makes the dependency graph explicit.

**Proposed split**:

| New module | Source range | Concern |
|---|---|---|
| `fx_protocol/labeled_observations.py` | `analytics_annotations.py:451-700` (approx) | Build `labeled_observations.csv` from forecast + outcome + annotation history |
| `fx_protocol/analytics_annotations.py` (slimmer) | remainder | AI draft generation + slice / tag scoreboard analytics |

**Public re-export contract**:

`analytics_annotations.py` continues to expose every previously-public name via
re-import (for callers in `automation.py`, `analytics_rebuild.py`, tests). Use
`__all__` to make the re-export intent explicit (matches Phase 1's `observability`
treatment, see PR #93 review thread on the pattern).

**Caveats**:

- `LABELED_OBSERVATION_FIELDNAMES` is a public tuple — must continue to be
  importable from both new and old paths.
- The labeled-obs builder reads many CSVs; mock-heavy tests may have explicit
  `analytics_annotations.<fn>` patches. Search for `mock.patch` /
  `monkeypatch.setattr` references and update path strings — this is the most
  common breakage in this kind of split.

**`target.yaml`**: declare `primary_kind: refactor` with `allow_changes` for the
new `labeled_observations.*` fqns and the relocated fqns. Mention in the comment
that `analytics_annotations` re-exports will look "moved" to semantic-ci even
though import paths are preserved (same pattern as Phase 1).

**Sizing**: ~250 LOC moves out of `analytics_annotations.py`. Net LOC ≈ 0
(plus the new file's module docstring). The win is **comprehensibility**, not
line count.

### Phase 3 — Unify weekly / monthly report builder

**Design pinned in [`docs/phase3_design.md`](./phase3_design.md).**

After audit (see the design doc), Phase 3 splits into:

- **Phase 3a** — Extract byte-equivalent window resolution + version
  stratification helpers (`_resolve_*_window`, `_is_in_*`,
  `_stratify_*_by_versions`) into a new `fx_protocol/report_window.py`.
  Net ~70 LOC saved, low risk, no public API change.
- **Phase 3b** — Extract the duplicated annotation-coverage counting
  logic into `fx_protocol/annotation_coverage.py`; both modules keep
  their existing wrapper signatures and call into the shared core.
  Net ~30 LOC saved, low risk, no public API change.
- **Phase 3c (deferred)** — Observation-loading bridge. Asymmetric
  loader contract between weekly (loads from disk) and monthly
  (receives pre-loaded data) is an architecture question, not a
  duplication problem. Tiny LOC saved, large blast radius.
- **Phase 3d (deferred)** — Per-strategy metric row unification across
  the str ↔ `float | None` schema split. Trades duplication for an
  adapter abstraction layer; not worth it without a third consumer.

The earlier sketch under this heading (window + observation loading +
metric computation as one bundle) was rejected during audit — it
conflated low-risk byte-identical extraction (Phase 3a) with
load-bearing schema divergence (would-be Phase 3d).
spec under `docs/specs/`. The audit identified the opportunity; the design
is not yet pinned down.

## semantic-ci convention

For every phase the workflow is:

1. **Discovery** — `git checkout main && semantic-ci observe ...` if needed,
   or read the audit section above.
2. **Declare** — write `.semantic-ci/target.yaml` for the phase: `primary_kind: refactor`,
   `allowed_secondary_kinds: [test_update]`, list scoped modules, declare `allow_changes`
   for all fqns intentionally added or relocated.
3. **Implement** — make the change on a feature branch.
4. **Validate** — `ruff check . && pytest -q`.
5. **Gate** — `semantic-ci check --baseline-rev main --candidate-rev HEAD --target .semantic-ci/target.yaml --package-root src/ugh_quantamental --format human --allow-dirty`.

### Known: `template:refactor:effects_unchanged` violation

Any refactor that **moves code with `fs` side effects** (CSV writes, JSON dumps)
between modules will violate `template:refactor:effects_unchanged`. semantic-ci
tracks effects per-fqn, so relocating an `os.makedirs` / `open` call from
`old_module._helper` to `new_module._helper` counts as an effect delta even
though runtime behavior is unchanged.

**Mitigation**: document the violation in the PR body as expected for the phase.
Do **not** flip `primary_kind` to `feature` to suppress it — the intent is
refactor, and labeling otherwise loses information.

## Validation checklist (every phase)

- [ ] `ruff check .` passes
- [ ] `pytest -q` passes (currently 1344 tests)
- [ ] `.semantic-ci/target.yaml` updated; `semantic-ci check ...` shows
      `api_surface_unchanged` and `imports_unchanged` satisfied
- [ ] PR description states which `target.yaml` constraints are satisfied vs
      flagged-as-expected
- [ ] Star-import contract preserved (when adding `__all__` to a previously
      no-`__all__` module, populate it with **all** pre-existing public names —
      see PR #93 review thread on `observability.__all__`)
- [ ] No public symbol is removed without a re-export at the original path
- [ ] CLAUDE.md invariants hold:
  - frozen Pydantic models untouched
  - engine purity preserved
  - persistence remains naive-UTC
  - `workflows.models` / `query.__init__` / `replay.__init__` still importable
    without SQLAlchemy
  - replay paths remain read-only

## Picking what to do next

**Default order**: 1.5 → 2 → 3.

- Phase 1.5 first because it tightens the metrics_utils API and unblocks Phase 3
  (which needs a single canonical `safe_*` API).
- Phase 2 next because it has the largest impact-per-risk ratio and is independent
  of the others.
- Phase 3 last and only after a written design.

If the user redirects (e.g. "skip 1.5, go to 2"), follow the redirect — this
order is a default, not a contract.

## Do not touch

The following areas are **architecturally guarded** in CLAUDE.md and should not
be modified by refactor work without an explicit design discussion:

- `engine/` pure-function boundary (no I/O, no globals, no mutation)
- Frozen Pydantic schemas (`extra="forbid"`, `frozen=True`)
- Persistence ORM column types and `naive-UTC` `created_at` normalization
- Alembic migration history (no schema redesign without a new migration)
- Workflow flush-only convention (caller owns the transaction)
- Import isolation: `workflows.models`, `query.__init__`, `replay.__init__` must
  remain importable without SQLAlchemy
- Read-only replay paths (no writes / flushes / commits in `replay/`)
- Review-audit boundary (raw text → extractor → engine, never bypassed)

## Branch / PR conventions

- Branch: `claude/refactor-<short-description>` (e.g. `claude/refactor-safe-stats-helpers`)
- Commit messages: imperative mood, summarize the move + the why; reference review
  threads in follow-up commits
- PR title: `<Verb> <thing> in <where>` (e.g. `Migrate safe_rate/mean/median into metrics_utils`)
- PR body: link this doc; state the phase; restate `target.yaml` constraints
  satisfied vs flagged-as-expected
