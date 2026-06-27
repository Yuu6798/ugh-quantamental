# FX AI Weekly Annotation v1 — Specification

**Status**: Implementing (live wiring + deterministic OHLC fallback landed — FX-ANNOT-LIVE)
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
- `annotation_fallback.py` — deterministic OHLC-derived regime / volatility
  fallback (pure functions); shared by the default adapter and the fallback tier

### Changed

- `analytics_annotations.py` — AI-first labeled observation fields; daily path
  (`run_annotation_analytics`) now wires AI + OHLC fallback into labeled
  observations; `generate_ai_annotations` heuristic is OHLC-derived (no leakage,
  shared vocabulary)
- `weekly_reports_v2.py` — AI-first coverage and readiness
- `weekly_report_exports.py` — new AI annotation summary artifact, updated MD/CSV
- `analytics_rebuild.py` — AI + OHLC fallback pass-through; shared collector
- `labeled_observations.py` — fallback tier + `collect_evaluated_forecast_rows`
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
AI annotation > Auto-derived > Manual compatibility > OHLC fallback
```

For event tags, AI and auto tags are merged (union).  Manual tags are used
only when neither AI nor auto provides any.

`annotation_source` values: `ai`, `ai_plus_auto`, `auto_only`, `manual_compat`,
`ohlc_fallback`, `none`

### 4.1 Deterministic OHLC fallback tier (FX-ANNOT-LIVE)

The lowest precedence tier is a deterministic, rule-based regime / volatility
annotator (`annotation_fallback.py`) derived **only** from realized OHLC. It
fills `regime_label` / `volatility_label` solely for forecasts where AI, auto,
and manual all leave the field empty, and never overrides a higher source.

Rows populated by AI **or** the OHLC fallback are market-derived and are marked
`annotation_status = confirmed`, so they pass both downstream gates: the weekly
slice gate (`annotation_source != none`) and the monthly slice gate
(`annotation_status == confirmed`). This is what restores live coverage — the
daily path (`run_annotation_analytics`) previously called
`build_labeled_observations` with no annotation source, leaving live weekly
reports unannotated despite the deterministic, API-free adapter being
available.

⚠️ **No performance leakage.** Both the default deterministic adapter and the
fallback derive regime / volatility from realized OHLC / market statistics
only — never from `direction_hit` / `close_error_bp`. Deriving regime from
whether the model was right is circular and invalidates regime-stratified
analysis (see `engine_review_2026_06_planning.md` §5.1). Output uses the shared
axes exactly: regime `trending`/`choppy`, volatility `low`/`normal`/`high` — no
`mixed`/`unknown` third bucket.

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
