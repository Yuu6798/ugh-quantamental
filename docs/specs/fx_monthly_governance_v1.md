# FX Monthly Governance Protocol v1 — Specification

**Status**: Draft
**Depends on**: fx_monthly_review_v1, fx_observability_artifacts_v1
**Scope**: Monthly governance layer — uses existing artifacts to make keep/change/version decisions
**Pipeline**: Part of the FX Analysis Pipeline (weekly → monthly → governance), automated via `fx-analysis-pipeline.yml`

---

## 0. Purpose

This protocol defines how the monthly review outputs are consumed to make governance decisions about the FX Daily Protocol. It specifies:

- What artifacts to inspect, and in what order
- What diagnostic axes to evaluate
- How to classify findings into actionable categories
- When and how version updates are permitted

**This is a governance protocol, not an analysis protocol.** The analysis is performed by `fx_monthly_review_v1`. This protocol defines what to do with those results.

**The role of this protocol is not to improve predictions, but to ensure that improvement decisions are recorded in an auditable form.**

### Automation boundary

Governance **outputs** (decision log, change candidate list, version decision record) are **auto-generated** as part of the analysis pipeline. Only the resulting **logic modifications** (code changes, version bumps) require human decision. The pipeline generates the data; humans decide what to do with it.

---

## 1. Scope

### 1.1 What this protocol covers

1. **Monthly review** — consuming existing monthly and daily artifacts to perform a 6-axis diagnostic
2. **Logic audit** — separating items that may be revised monthly from items that must remain fixed
3. **Version update decisions** — determining update timing, update unit, change records, and prohibitions

### 1.2 What this protocol does NOT cover

- Daily forecast generation logic
- Daily outcome / evaluation generation logic
- Automated trading or execution
- Automated calibration or parameter tuning
- Ad-hoc specification changes on arbitrary dates
- Threshold values (thresholds are defined in implementation modules, not in this protocol)

---

## 2. Monthly Review Inputs

The monthly review consumes the following artifacts. All are defined in `fx_monthly_review_v1` or `fx_observability_artifacts_v1`. No new artifacts are introduced.

### 2.1 From fx_monthly_review_v1

| Artifact | Source |
|---|---|
| `monthly_review.json` | `analytics/monthly/{YYYYMM}/monthly_review.json` |
| `monthly_review.md` | `analytics/monthly/{YYYYMM}/monthly_review.md` |
| `monthly_strategy_metrics.csv` | `analytics/monthly/{YYYYMM}/monthly_strategy_metrics.csv` |
| `monthly_slice_metrics.csv` | `analytics/monthly/{YYYYMM}/monthly_slice_metrics.csv` |
| `monthly_review_flags.csv` | `analytics/monthly/{YYYYMM}/monthly_review_flags.csv` |

### 2.2 From fx_observability_artifacts_v1

| Artifact | Source |
|---|---|
| `input_snapshot.json` | `latest/input_snapshot.json` or `history/{YYYYMMDD}/{batch_id}/input_snapshot.json` |
| `run_summary.json` | `latest/run_summary.json` or `history/{YYYYMMDD}/{batch_id}/run_summary.json` |
| `daily_report.md` | `latest/daily_report.md` or `history/{YYYYMMDD}/{batch_id}/daily_report.md` |
| `scoreboard.csv` | `latest/scoreboard.csv` or `history/{YYYYMMDD}/{batch_id}/scoreboard.csv` |
| `provider_health.csv` | `provider_health.csv` (append-only master log) |

---

## 3. Monthly Review — 6-Axis Diagnostic

The monthly review evaluates the following 6 axes **in this order**. The order is fixed and must not be rearranged.

### Axis 1: Basic Performance

Evaluate UGH and each baseline (`baseline_random_walk`, `baseline_prev_day_direction`, `baseline_simple_technical`) on:

- `forecast_count`
- `direction_hit_rate`
- `range_hit_rate`
- `mean_abs_close_error_bp`
- `mean_abs_magnitude_error_bp`

Source: `monthly_strategy_metrics.csv`

### Axis 2: Baseline Differential

For each baseline, evaluate deltas versus UGH:

- `direction_accuracy_delta_vs_ugh`
- `mean_abs_close_error_bp_delta_vs_ugh`
- `mean_abs_magnitude_error_bp_delta_vs_ugh`

Judgment is made from the delta table, not from subjective impression. Source: baseline comparisons in `monthly_review.json`.

### Axis 3: State / Regime / Event Slice

UGH only. Evaluate performance sliced by:

- `dominant_state`
- `regime_label`
- `volatility_label`
- `intervention_risk`
- `event_tag`

Source: `monthly_slice_metrics.csv`

### Axis 4: Disconfirmer / False Positive

UGH only. Evaluate:

- Representative cases where `direction_hit == false`
- Proportion of `disconfirmer_explained == true` among disconfirmed cases
- Concentration of false positives by `dominant_state`, `event_tag`, and `regime_label`

Source: `monthly_review.json` (representative failures, review data)

### Axis 5: Provider / Observability

Evaluate operational health:

- Missing windows (from `missing_window_count` in `monthly_review.json`)
- Provider lag rate (from `provider_health_summary`)
- Fallback adjustment rate (from `provider_health_summary`)
- Provider mix (from `provider_mix_summary`)
- `annotation_coverage_rate` (from `annotation_coverage_summary`)

Source: `monthly_review.json`, `provider_health.csv`

### Axis 6: Review Flags

Confirm the review flags produced by `fx_monthly_review_v1`:

- `insufficient_data`
- `inspect_magnitude_mapping`
- `inspect_direction_logic`
- `inspect_state_mapping`
- `low_annotation_coverage`
- `provider_quality_issue`
- `missing_windows`
- `keep_current_logic`

Source: `monthly_review_flags.csv`

**Flags are material for recommendations but are not automatically adopted. Governance outputs are auto-generated; logic modifications based on those outputs require human decision.**

---

## 4. Monthly Judgment Categories

Every monthly review must classify its conclusion into exactly one of the following four categories.

| Category | Meaning | Version Update |
|---|---|---|
| **Keep** | Current logic is maintained as-is | No |
| **Logic audit** | Identified as a logic review candidate; deferred to the next month's investigation | No |
| **Data / provider remediation** | Classified as a data infrastructure or operational issue | No |
| **Version promotion candidate** | Adopted as a version update candidate for the following month | Yes (one of `theory_version` / `engine_version` / `schema_version` / `protocol_version`) |

### Condition examples

- **Keep**: All review flags resolve to `keep_current_logic`. Baseline deltas are within acceptable ranges. No anomalous slice concentration.
- **Logic audit**: `inspect_direction_logic` or `inspect_state_mapping` flags are raised. False positive concentration is observed in specific `dominant_state` or `regime_label` slices. Requires further investigation before any change is made.
- **Data / provider remediation**: `provider_quality_issue` or `missing_windows` flags are raised. `annotation_coverage_rate` is below acceptable levels. The issue is in the input data, not in the prediction logic.
- **Version promotion candidate**: A specific logic change has been investigated in a prior logic audit cycle, the expected benefit and risk are documented, and the change is ready for controlled deployment.

---

## 5. Logic Audit Scope

**Design intent: The monthly review is not a place to redesign the measurement instrument; it is a place to recalibrate it.**

### 5.1 Items eligible for monthly review

The following may be revised through the monthly governance process:

- `q_strength` coefficients
- `alignment` weights
- `grv_raw` / `grv_lock` coefficients
- State thresholds
- Disconfirmer rule design
- X block inclusion/exclusion
- `expected_range` generation rules
- Weekly / monthly aggregation thresholds

### 5.2 Items fixed at the monthly level

The following must NOT be changed through the monthly governance process:

- Lifecycle state definitions
- Core schema (`extra="forbid", frozen=True` contracts)
- Canonical business-day rule
- Forecast fixed time
- Forecast horizon
- Baseline strategy types (`baseline_random_walk`, `baseline_prev_day_direction`, `baseline_simple_technical`)
- ID / uniqueness rules (`forecast_batch_id`, `forecast_id`, `outcome_id`, `evaluation_id`)
- Fail-fast policy

Changes to fixed items require a separate design process outside the scope of this protocol.

---

## 6. Version Update Rules

### 6.1 Update timing

Version updates are permitted **only after the monthly review is completed**. Changes during business days or business weeks are prohibited.

### 6.2 Update unit

Each version update must be classified into exactly one of:

| Version | Scope |
|---|---|
| `theory_version` | UGH theoretical framework (coefficients, state logic, disconfirmer rules) |
| `engine_version` | Engine implementation (projection, state lifecycle, review-audit functions) |
| `schema_version` | Record schema (Pydantic models, CSV column definitions) |
| `protocol_version` | Operational protocol (ID generation, business-day rules, automation flow) |

### 6.3 Change record

Every version update must include the following in its change record:

- Change rationale
- Change target (which version layer)
- Version before and after the change
- Expected impact on baseline comparisons
- Period requiring re-evaluation (if any)

### 6.4 Prohibitions

The following are prohibited:

- Incrementing a version without documenting the change content
- Combining changes across multiple version layers in a single update
- Retroactively modifying historical records mid-month

---

## 7. Monthly Review Outputs

The monthly review produces three output artifacts.

### 7.1 Monthly Decision Log

| Field | Description |
|---|---|
| `review_month` | The month under review (YYYYMM) |
| `overall_judgment` | One of: `keep`, `logic_audit`, `data_provider_remediation`, `version_promotion_candidate` |
| `key_flags` | Review flags that were raised |
| `baseline_comparison_summary` | Summary of UGH vs baseline deltas |
| `logic_audit_candidates` | List of items identified for logic audit (if any) |
| `provider_annotation_concerns` | Provider health or annotation coverage issues (if any) |
| `final_recommendation` | Free-text recommendation |

### 7.2 Change Candidate List

| Field | Description |
|---|---|
| `candidate_id` | Unique identifier for the change candidate |
| `category` | One of the four judgment categories |
| `rationale` | Why this candidate was identified |
| `expected_benefit` | What improvement is expected |
| `expected_risk` | What could go wrong |
| `owner` | Who is responsible for investigating or implementing |
| `status` | `proposed` / `investigating` / `accepted` / `rejected` / `deferred` |

### 7.3 Version Decision Record

| Field | Description |
|---|---|
| `update_performed` | `true` or `false` |
| `updated_versions` | List of `{version_layer, old_value, new_value}` (empty if no update) |
| `unchanged_versions` | List of version layers that were not updated |
| `freeze_window_start` | Start of the freeze window (first business day of the new month) |
| `freeze_window_end` | End of the freeze window (last business day of the new month) |
| `rollback_trigger` | Conditions under which the update should be rolled back |

---

## 8. Judgment Procedure

The following 10 steps are executed in this fixed order every month. The order must not be changed.

1. Confirm that monthly artifacts are finalized
2. Review strategy metrics (Axis 1)
3. Review baseline comparisons (Axis 2)
4. Review state / regime / event slices (Axis 3)
5. Review false positive / disconfirmer patterns (Axis 4)
6. Review provider / annotation health (Axis 5)
7. Review flags (Axis 6)
8. Classify into keep / logic audit / data-provider remediation / version promotion candidate
9. Determine version update eligibility
10. Finalize the monthly decision log

**Reason for fixed ordering: to prevent conflation of theoretical issues with operational issues.**

---

## 9. Judgment Priority

When findings conflict, the following priority order applies (highest priority first):

1. **Provider / missing window issues** — data pipeline integrity
2. **Annotation coverage issues** — observability completeness
3. **Clear inferiority to baselines** — demonstrated underperformance vs baseline deltas
4. **State / disconfirmer bias** — systematic bias in specific slices
5. **Magnitude / range improvement opportunities** — refinement candidates

**Design intent: Do not adjust the theory when the inputs are broken.**

---

## 10. Completion Criteria

A monthly governance cycle is complete when all of the following are satisfied:

- All 6 axes have been evaluated
- The 10-step procedure has been followed in order
- A judgment category has been assigned
- The monthly decision log has been written
- If the judgment is `version_promotion_candidate`, a change candidate list and version decision record have been produced
- All outputs are stored alongside the monthly review artifacts

---

## 11. Pipeline Integration

This protocol is implemented as the final stage of the **FX Analysis Pipeline**, which runs as a single GitHub Actions workflow (`fx-analysis-pipeline.yml`) separate from the daily data collection workflow.

### Pipeline architecture (2 Actions)

| Action | Schedule | Purpose |
|---|---|---|
| `fx-daily-protocol.yml` | Mon-Fri 08:00/12:00/16:00 JST | Data collection: fetch → forecast → outcome → evaluation → CSV |
| `fx-analysis-pipeline.yml` | Weekly: Mon 10:00 JST / Monthly: 1st 10:00 JST | Analysis: weekly aggregation → monthly review → governance outputs |

### Monthly pipeline flow

```
Step 1: Generate weekly reports for each week in the month
        (rebuild annotation analytics → run_weekly_report_v2 → export)
            ↓
Step 2: Generate monthly review
        (rebuild_monthly_review → strategy metrics, baseline comparisons,
         slice metrics, review flags, recommendation)
            ↓
Step 3: Load weekly report artifacts as governance input
        (read weekly_report.json for each week → extract weekly trends)
            ↓
Step 4: Generate governance outputs
        (run_monthly_governance → decision log, change candidates,
         version decision record, governance summary)
```

### Module layout

| File | Purpose |
|---|---|
| `fx_protocol/monthly_governance.py` | Pure functions: judgment classification, trend extraction, output generation |
| `fx_protocol/monthly_governance_exports.py` | File I/O: JSON, MD export + orchestrator |
| `scripts/run_fx_analysis_pipeline.py` | CLI entrypoint for both weekly and monthly modes |
| `.github/workflows/fx-analysis-pipeline.yml` | Analysis pipeline GitHub Actions workflow |
| `tests/fx_protocol/test_monthly_governance.py` | Tests for pure governance functions |

### Output layout

```
{csv_output_dir}/analytics/monthly/{YYYYMM}/
├── monthly_review.json              (from monthly review)
├── monthly_review.md                (from monthly review)
├── monthly_strategy_metrics.csv     (from monthly review)
├── monthly_slice_metrics.csv        (from monthly review)
├── monthly_review_flags.csv         (from monthly review)
├── governance_decision_log.json     (from governance)
├── governance_change_candidates.json (from governance)
├── governance_version_decision.json (from governance)
└── governance_summary.md            (from governance)
```

---

## 12. One-Sentence Definition

**FX Monthly Review / Feedback / Logic Audit Protocol v1** is a governance protocol that uses monthly aggregated artifacts to compare UGH against baselines, diagnose state / event / provider / annotation conditions, classify change candidates, and determine version update eligibility — all in an auditable sequence and record format.
