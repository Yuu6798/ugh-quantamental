# FX Weekly Annotation Resilience v1 — Specification

**Status**: Implementing
**Depends on**: FX Weekly Report v2, FX Annotation Analytics v1
**Scope**: Analytics-layer hardening — no changes to engine, protocol schemas, or persistence

---

## 1. Motivation

The weekly analytics pipeline produces useful strategy metrics but degrades
severely when manual annotation coverage is low or zero:

- Slice metrics collapse into a single "unlabeled" bucket with no breakdown.
- Event-tag analysis requires confirmed annotations even when outcome CSVs
  already carry event tags.
- The weekly report provides only a single scalar coverage number, making it
  hard to diagnose which annotation fields are missing.

This specification hardens the weekly analytics layer so that:

1. Core analysis (strategy metrics, evaluation accuracy) is always available.
2. Event-tag slicing works from auto-derived tags when manual tags are absent.
3. Field-level coverage exposes exactly which annotation dimensions are populated.
4. The report payload explicitly separates core vs annotation-dependent sections.

---

## 2. Change Boundary

### NOT changed

- Engine formulas (projection, state, review-audit)
- Protocol schemas (ForecastRecord, OutcomeRecord, EvaluationRecord)
- Persistence schema / Alembic migrations
- GitHub Actions workflows
- Monthly governance logic
- Data-source connectors
- Daily automation entrypoint

### Changed

- `analytics_annotations.py` — event-tag provenance fields, auto-tag enrichment
- `weekly_reports_v2.py` — field-level coverage, core/annotated split, effective
  event-tag slicing
- `weekly_report_exports.py` — annotation coverage CSV, updated MD/JSON
- `analytics_rebuild.py` — pass-through for new artifacts
- `scripts/run_fx_weekly_report.py` — updated summary output

### Added

- `docs/specs/fx_weekly_annotation_resilience_v1.md` (this file)
- `weekly_annotation_coverage.csv` artifact

---

## 3. Labeled Observation Event-Tag Provenance

### New fields on labeled observations

| Field | Source | Description |
|---|---|---|
| `manual_event_tags` | manual_annotations.csv `event_tags` | Exactly as entered by annotator |
| `auto_event_tags` | outcome.csv `event_tags` + calendar derivation | Deterministic auto tags |
| `effective_event_tags` | union of manual + auto, deduplicated | Used for analytics |
| `event_tag_source` | derived | `manual`, `auto`, `mixed`, or `none` |

The existing `event_tags` field is preserved for backward compatibility and
contains the same value as `effective_event_tags`.

### Auto event-tag derivation rules

Only deterministic derivations from locally available data:

1. **Outcome event tags**: if the outcome CSV for the evaluated window carries
   `event_tags`, those are included verbatim in `auto_event_tags`.
2. **`month_end`**: added when `as_of_jst` is the last protocol business day
   (Mon–Fri) of its calendar month.
3. **`quarter_end`**: added when `as_of_jst` is the last protocol business day
   of Mar, Jun, Sep, or Dec.

Tags are pipe-delimited, sorted, and deduplicated.

---

## 4. Field-Level Annotation Coverage

### Structure

For each annotation field (`regime_label`, `event_tags`, `volatility_label`,
`intervention_risk`), compute:

| Metric | Description |
|---|---|
| `total_observations` | Total observation count |
| `populated_count` | Rows where the field is non-empty |
| `populated_rate` | populated_count / total |
| `confirmed_count` | Rows with `annotation_status=confirmed` AND field non-empty |
| `confirmed_rate` | confirmed_count / total |
| `pending_count` | Rows with `annotation_status=pending` AND field non-empty |
| `pending_rate` | pending_count / total |
| `unlabeled_count` | total - confirmed_count - pending_count |
| `unlabeled_rate` | unlabeled_count / total |

### Artifact

`weekly_annotation_coverage.csv` — one row per field with the above metrics.

---

## 5. Core vs Annotated Analysis Split

### Report payload additions

| Key | Type | Description |
|---|---|---|
| `core_analysis_ready` | bool | `observation_count > 0` |
| `annotated_analysis_ready` | bool | `confirmed_annotation_count > 0` |
| `annotation_field_coverage` | dict | Per-field coverage (see §4) |
| `event_tag_slice_source_summary` | dict | Counts of manual/auto/mixed/none sources |

### Policy

- `core_analysis`: strategy_metrics, provider_health — always available.
- `annotated_analysis`: regime/volatility/intervention slices — require
  confirmed annotations.
- Event-tag slices: use `effective_event_tags`, available even without manual
  annotations when outcome data or calendar derivation provides tags.

---

## 6. Slice Metrics Behavior

| Condition | Regime/Vol/IR slices | Event-tag slices |
|---|---|---|
| Confirmed annotations exist | Use confirmed labels | Use effective_event_tags from confirmed rows |
| No confirmed annotations | Group all under `label="all"` per strategy | Use effective_event_tags from all rows |

When confirmed annotations exist, non-confirmed rows are bucketed as
`label="unlabeled"` (existing behavior).

---

## 7. Markdown Output

The weekly report markdown separates:

1. **Core Analysis** — always shown: strategy performance table
2. **Annotation Coverage** — field-level coverage table
3. **Event-Tag Analysis** — effective tag slices with source attribution
4. **Annotation-Dependent Analysis** — regime/vol/IR slices, shown only when
   confirmed annotations exist; otherwise a notice is displayed

---

## 8. Invariants

1. Weekly report generation succeeds when annotation coverage is 0%.
2. Core strategy metrics are identical whether annotations exist or not.
3. Event-tag slices use `effective_event_tags` — never empty when outcome
   event_tags or calendar derivation provides tags.
4. Existing artifact paths (`weekly_report.json`, `.md`, strategy/slice CSVs)
   are preserved.
5. `weekly_annotation_coverage.csv` is a new additive artifact.
6. No engine or protocol logic is changed.
