# FX AI Weekly Annotation v1 — Specification

**Status**: Implementing
**Depends on**: FX Weekly Report v2, FX Annotation Analytics v1, Annotation Resilience v1
**Scope**: Analytics-layer AI-first shift — no changes to engine, protocol schemas, or persistence

---

## 1. Motivation

The weekly analytics pipeline currently treats manual annotations as the primary
source for annotation-dependent analysis (regime, volatility, intervention, event-tag
slicing).  This creates a bottleneck: useful analysis is unavailable until a human
confirms annotations, which may never happen for many weeks.

This specification shifts the weekly analytics layer to be **AI-first**:

- AI-generated annotations become the primary source for slice analysis.
- Manual annotations are optional compatibility inputs only.
- The default weekly path requires no human annotation.
- Core metrics remain always available with zero annotation dependency.

---

## 2. Change Boundary

### NOT changed

- Engine formulas (projection, state, review-audit)
- Protocol schemas (ForecastRecord, OutcomeRecord, EvaluationRecord)
- Persistence schema / Alembic migrations
- GitHub Actions workflows
- Monthly governance logic
- Daily automation logic
- Data-source connectors

### Added

- `annotation_models.py` — typed Pydantic v2 models for evidence and AI annotations
- `annotation_sources.py` — source precedence constants and resolution logic
- `ai_annotations.py` — AI annotation execution boundary and adapter abstraction

### Changed

- `analytics_annotations.py` — AI-first labeled observation fields
- `weekly_reports_v2.py` — AI-first coverage and readiness
- `weekly_report_exports.py` — new AI annotation summary artifact, updated MD/CSV
- `analytics_rebuild.py` — AI annotation pass-through
- `scripts/run_fx_weekly_report.py` — updated summary output

---

## 3. Architectural Separation

### A) Core weekly metrics
- Always computable from forecast/outcome/evaluation records
- No annotation dependency whatsoever

### B) AI-derived analysis layer
- Uses external evidence + AI-generated structured annotations
- Primary source for regime/volatility/intervention/event-tag analysis
- Operates via injected adapter (no hard vendor dependency)

### C) Optional manual overrides
- Backward compatibility only
- Never required for report generation
- Lowest precedence in label resolution

---

## 4. Effective Label Precedence

```
AI annotation > Auto-derived > Manual compatibility
```

For event tags, AI and auto tags are merged (union).  Manual tags are used
only when neither AI nor auto provides any.

`annotation_source` values: `ai`, `ai_plus_auto`, `auto_only`, `manual_compat`, `none`

---

## 5. External Evidence Model

`ExternalEvidenceItem` captures a single piece of evidence (news, calendar, etc.)
with `source_kind`, `content_hash`, optional temporal window, and URL.

`ExternalEvidenceBundle` collects items for an annotation pass.

---

## 6. AI Annotation Model

`AiAnnotationRecord` carries per-forecast annotation labels with:
- `regime_label`, `volatility_label`, `intervention_risk`
- `event_tags` (sorted tuple)
- `failure_reason`
- `annotation_confidence` (0.0–1.0)
- `annotation_model_version`, `annotation_prompt_version`
- `evidence_refs` (sorted tuple of source_ids)

`AiAnnotationBatch` groups records from a single annotation run.

---

## 7. Readiness Policy

- `core_analysis_ready = observation_count > 0`
- `annotated_analysis_ready = ai_annotated_count + auto_annotated_count > 0`

Manual annotations are NOT required for `annotated_analysis_ready`.

---

## 8. New Artifacts

- `weekly_ai_annotation_summary.csv` — per-metric summary of AI annotation coverage
- Updated `weekly_annotation_coverage.csv` — now shows AI/auto/manual/effective/missing

---

## 9. Invariants

1. Weekly report generation succeeds when manual annotation coverage is 0%.
2. AI annotations are the primary source for slice analysis.
3. Core strategy metrics are identical regardless of annotation state.
4. No vendor SDK is hard-coded; adapter pattern enables testing with deterministic fakes.
5. Existing artifact paths are preserved.
6. No engine or protocol logic is changed.
