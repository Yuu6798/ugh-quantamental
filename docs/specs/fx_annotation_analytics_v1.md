# FX Annotation & Analytics Layer — Specification v1

## Overview

This layer adds **AI draft annotations**, **human-confirmed annotations**, and
**slice-based analytics** on top of the existing FX Daily Protocol pipeline.

**Design principles:**

- The existing forecast/outcome/evaluation logic is **unchanged**.
- AI annotations are **supplementary drafts** — never used as ground truth.
- Human-confirmed annotations are the **authoritative labels** for analysis.
- All analytics outputs are **derived artifacts** generated after existing steps.
- Failures in this layer **never break** the daily run.

---

## 1. AI Annotation Suggestions

**Path:** `{csv_output_dir}/annotations/ai_annotation_suggestions.csv`

One row per `as_of_jst`. Generated automatically during each daily run.

### Columns

| Column | Type | Description |
|---|---|---|
| `as_of_jst` | ISO 8601 datetime | Protocol window open (08:00 JST) |
| `ai_regime_label` | string | Heuristic regime classification (e.g. `trending`, `choppy`, `mixed`, `unknown`) |
| `ai_event_tags` | pipe-delimited string | Recent event tags from outcome history |
| `ai_volatility_label` | string | Heuristic volatility level (`low`, `normal`, `high`) |
| `ai_intervention_risk` | string | Heuristic intervention risk (`low`, `medium`, `high`) |
| `ai_notes` | string | Free-form notes from the generator |
| `generated_at_utc` | ISO 8601 datetime | Generation timestamp |

### Heuristic rules

- **regime_label**: Based on recent UGH direction hit rate (5-day window).
  - >= 80% hit rate -> `trending`
  - <= 20% hit rate -> `choppy`
  - otherwise -> `mixed`
  - no data -> `unknown`
- **volatility_label**: Based on average `close_error_bp` from recent evaluations.
  - > 50 bp -> `high`
  - > 20 bp -> `normal`
  - <= 20 bp -> `low`
- **intervention_risk**: Based on maximum absolute `realized_close_change_bp` from recent outcomes.
  - > 100 bp -> `high`
  - > 50 bp -> `medium`
  - <= 50 bp -> `low`

These heuristics are intentionally simple and are **not authoritative**.

---

## 2. Manual Annotations

**Path:** `{csv_output_dir}/annotations/manual_annotations.csv`

Human-authored file. One row per `as_of_jst`.

### Columns

| Column | Type | Description |
|---|---|---|
| `as_of_jst` | ISO 8601 datetime | Protocol window open (must match forecast/outcome dates) |
| `regime_label` | string | Human-assigned regime label |
| `event_tags` | pipe-delimited string | Human-assigned event tags |
| `volatility_label` | string | Human-assigned volatility level |
| `intervention_risk` | string | Human-assigned intervention risk level |
| `notes` | string | Free-form notes |
| `annotation_status` | string | `confirmed` or `pending` |

### Status values

| Status | Meaning |
|---|---|
| `confirmed` | Human has reviewed and finalized this annotation. Used as ground truth in analysis. |
| `pending` | Draft or partial annotation. Not used as ground truth; treated as unlabeled in aggregations. |

### Template

A template file is auto-generated at:
`{csv_output_dir}/annotations/manual_annotations.template.csv`

Contains column headers and one sample row. Operators copy this to
`manual_annotations.csv` and fill in their annotations, referencing
`ai_annotation_suggestions.csv` as a starting point.

### Graceful handling

- If `manual_annotations.csv` does not exist, the daily run proceeds normally.
- All annotation columns in derived outputs are left blank for unmatched dates.

---

## 3. Labeled Observations

**Path:** `{csv_output_dir}/analytics/labeled_observations.csv`

Joins history forecast/outcome/evaluation CSVs with manual annotations.

### Columns

| Column | Source | Description |
|---|---|---|
| `as_of_jst` | forecast | Protocol window date |
| `forecast_batch_id` | forecast | Batch identifier |
| `outcome_id` | evaluation | Outcome identifier |
| `strategy_kind` | forecast | Strategy (ugh, baseline_*) |
| `forecast_direction` | forecast | Predicted direction |
| `expected_close_change_bp` | forecast | Predicted change in basis points |
| `realized_direction` | outcome | Actual direction |
| `realized_close_change_bp` | outcome | Actual change in basis points |
| `direction_hit` | evaluation | Direction prediction hit |
| `range_hit` | evaluation | Range prediction hit (UGH only) |
| `state_proxy_hit` | evaluation | State proxy hit (UGH only) |
| `close_error_bp` | evaluation | Absolute close error |
| `magnitude_error_bp` | evaluation | Absolute magnitude error |
| `regime_label` | manual_annotations | Human-assigned regime |
| `event_tags` | manual_annotations | Human-assigned event tags |
| `volatility_label` | manual_annotations | Human-assigned volatility |
| `intervention_risk` | manual_annotations | Human-assigned intervention risk |
| `annotation_status` | manual_annotations | `confirmed`, `pending`, or empty |

### Key design decisions

- **AI suggestion columns are excluded.** This CSV uses only human annotations.
- Dates without manual annotations have empty annotation columns.
- The file can be regenerated from history at any time.

---

## 4. Slice Scoreboard

**Path:** `{csv_output_dir}/analytics/slice_scoreboard.csv`

Aggregated metrics by `(strategy_kind, regime_label, volatility_label, intervention_risk)`.

### Columns

| Column | Description |
|---|---|
| `strategy_kind` | Strategy identifier |
| `regime_label` | Regime label (empty = unlabeled) |
| `volatility_label` | Volatility label (empty = unlabeled) |
| `intervention_risk` | Intervention risk (empty = unlabeled) |
| `observation_count` | Number of observations in this slice |
| `direction_hit_count` | Count of direction hits |
| `direction_hit_rate` | Hit rate (0.0–1.0) |
| `range_hit_count` | Count of range hits (UGH only) |
| `range_hit_rate` | Range hit rate |
| `state_proxy_hit_count` | Count of state proxy hits (UGH only) |
| `state_proxy_hit_rate` | State proxy hit rate |
| `mean_close_error_bp` | Mean absolute close error |
| `median_close_error_bp` | Median absolute close error |
| `mean_magnitude_error_bp` | Mean absolute magnitude error |
| `last_updated_utc` | Generation timestamp |

### Aggregation rules

- **Confirmed rows**: Use their human-assigned labels as group keys.
- **Non-confirmed rows** (pending, missing, empty status): Labels are replaced with
  empty strings, effectively grouping them as **unlabeled**.
- This ensures that only human-verified labels drive the labeled analysis,
  while all data remains visible in the unlabeled bucket.

---

## 5. Tag Scoreboard

**Path:** `{csv_output_dir}/analytics/tag_scoreboard.csv`

Per-tag aggregation with tag expansion.

### Columns

| Column | Description |
|---|---|
| `strategy_kind` | Strategy identifier |
| `event_tag` | Individual event tag (expanded from pipe-delimited field) |
| `observation_count` | Number of observations with this tag |
| `direction_hit_rate` | Direction hit rate |
| `range_hit_rate` | Range hit rate |
| `state_proxy_hit_rate` | State proxy hit rate |
| `mean_close_error_bp` | Mean close error |
| `mean_magnitude_error_bp` | Mean magnitude error |
| `last_updated_utc` | Generation timestamp |

### Tag expansion

If an observation has `event_tags=fomc|cpi_us`, it contributes one observation
to the `fomc` group and one to the `cpi_us` group.

---

## 6. AI vs Human Role Separation

| Aspect | AI Suggestions | Manual Annotations |
|---|---|---|
| Authority | Supplementary draft only | Ground truth for analysis |
| Used in labeled_observations.csv | No | Yes |
| Used in slice_scoreboard.csv | No | Yes (confirmed only) |
| Used in tag_scoreboard.csv | No (from manual event_tags) | Yes |
| Required for daily run | No | No |
| Failure impact | None (non-fatal) | None (graceful degradation) |

**Invariant:** AI suggestion columns (`ai_*`) never appear in the main analysis
CSV (`labeled_observations.csv`). The AI draft exists solely to assist human
annotators in filling out `manual_annotations.csv`.

---

## 7. Integration with Daily Run

The annotation/analytics layer runs as **Step 8** in `automation.py`, after all
existing steps (forecast, outcome, evaluation, CSV export, layout, manifest,
observability) have completed.

The entire step is wrapped in a try/except block. Any failure is logged as a
warning but does not affect the return value of existing fields or the success
of the daily run.

### Output paths

```
{csv_output_dir}/
├── annotations/
│   ├── ai_annotation_suggestions.csv    (auto-generated each run)
│   └── manual_annotations.template.csv  (auto-generated each run)
│   └── manual_annotations.csv           (human-authored, optional)
├── analytics/
│   ├── labeled_observations.csv         (auto-generated each run)
│   ├── slice_scoreboard.csv             (auto-generated each run)
│   └── tag_scoreboard.csv               (auto-generated each run)
```

### Regeneration

All analytics outputs can be regenerated from history CSVs + manual_annotations.csv
at any time by calling `run_annotation_analytics()` with the appropriate
`csv_output_dir` and `as_of_jst`.
