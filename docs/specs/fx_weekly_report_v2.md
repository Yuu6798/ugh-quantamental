# FX Weekly Report v2 — Specification

## Overview

Weekly Report v2 extends the existing FX weekly report with annotation-aware
analytics, persistent artifact output, and rebuild capability.  It operates
as a pure post-processing layer on persisted CSV history — no forecast or
evaluation logic is changed.

## Design Principles

- **Internal logic unchanged**: All forecast, outcome, evaluation, state,
  baseline, and GRV computations remain identical.
- **v1 compatibility**: The existing `run_weekly_report` function and all
  report models (`WeeklyReportRequest`, `WeeklyReportResult`, etc.) are
  preserved without modification.
- **CSV-first**: v2 reads from `history/` and `annotations/` CSVs, not
  from the database, enabling standalone operation.
- **No SQLAlchemy dependency**: All v2 modules are importable without
  SQLAlchemy installed.
- **Pure + export separation**: Report computation is side-effect-free;
  file I/O is isolated in a separate export module.

## Architecture

```
weekly_reports_v2.py     Pure report computation (no file writes)
weekly_report_exports.py Artifact export helpers (JSON, MD, CSV)
analytics_rebuild.py     Orchestrator for rebuilding from history
```

## Data Flow

```
history/ CSVs ──┐
                ├─→ labeled_observations.csv ──→ run_weekly_report_v2()
annotations/ ───┘                                       │
                                                        ▼
provider_health.csv ──────────────────────→  Weekly Report v2 dict
                                                        │
                                                        ▼
                                            export_weekly_report_artifacts()
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    ▼                   ▼                   ▼
                            weekly_report.json  weekly_report.md  weekly_*_metrics.csv
```

## v2 Report Contents

### Annotation Coverage

| Field | Description |
|---|---|
| `total_observations` | Total labeled observation rows in the week |
| `confirmed_annotation_count` | Rows with `annotation_status=confirmed` |
| `pending_annotation_count` | Rows with `annotation_status=pending` |
| `unlabeled_count` | Rows with no annotation status |
| `annotation_coverage_rate` | `confirmed / total` |

### Strategy Metrics

Per-strategy aggregate metrics from weekly observations:

| Field | Description |
|---|---|
| `strategy_kind` | Strategy identifier |
| `observation_count` | Total observations |
| `direction_hit_count` / `direction_hit_rate` | Direction accuracy |
| `range_hit_count` / `range_hit_rate` | Range hit rate (UGH only) |
| `state_proxy_hit_count` / `state_proxy_hit_rate` | State proxy hit rate |
| `mean_close_error_bp` / `median_close_error_bp` | Close error statistics |
| `mean_magnitude_error_bp` | Magnitude error mean |

### Slice Metrics

Metrics sliced by annotation dimensions.  Only confirmed annotations are
used for labeled slices; non-confirmed rows appear as `unlabeled`.

Slice dimensions:
- `strategy_kind × regime_label`
- `strategy_kind × volatility_label`
- `strategy_kind × intervention_risk`
- `strategy_kind × event_tag` (expanded per tag)

Each slice has the same metric fields as strategy metrics.

### Provider Health Summary

| Field | Description |
|---|---|
| `total_runs` | Provider health rows in the week |
| `providers` | Dict of provider name → usage count |
| `fallback_adjustment_count` | Runs using fallback adjustment |
| `lag_count` | Runs with snapshot lag > 0 |
| `success_count` / `failed_count` / `skipped_count` | Run status counts |

### Generated Artifact Paths

List of absolute paths to all generated artifacts, populated by the
export layer.

## Artifact Layout

```
{csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_report.json
{csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_report.md
{csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_strategy_metrics.csv
{csv_output_dir}/analytics/weekly/{YYYYMMDD}/weekly_slice_metrics.csv
{csv_output_dir}/analytics/weekly/latest/weekly_report.json
{csv_output_dir}/analytics/weekly/latest/weekly_report.md
{csv_output_dir}/analytics/weekly/latest/weekly_strategy_metrics.csv
{csv_output_dir}/analytics/weekly/latest/weekly_slice_metrics.csv
```

## Annotation Priority

- **Confirmed** manual annotations are the primary data source for labeled
  analysis (regime, volatility, intervention risk, event tags).
- **AI suggestions** are supplementary — never used as ground truth in
  the v2 report.
- **Pending** annotations are counted but not used for labeled analysis.
- **Unlabeled** observations (no annotation status) are grouped separately
  in slice metrics.

## CLI Scripts

### `scripts/run_fx_weekly_report.py`

Generates the weekly v2 report from persisted CSV history.

| Environment Variable | Default | Description |
|---|---|---|
| `FX_CSV_OUTPUT_DIR` | `./data/csv` | Root CSV output directory |
| `FX_REPORT_DATE` | Today (JST) | Report date in YYYYMMDD format |
| `FX_WEEK_DAYS` | `5` | Number of business days |

### `scripts/rebuild_fx_analytics.py`

Rebuilds all annotation analytics and optionally the weekly report.

| Environment Variable | Default | Description |
|---|---|---|
| `FX_CSV_OUTPUT_DIR` | `./data/csv` | Root CSV output directory |
| `FX_REPORT_DATE` | (none) | If set, also rebuild weekly report |
| `FX_WEEK_DAYS` | `5` | Number of business days |

## Scheduled Execution

The `fx-weekly-report.yml` GitHub Actions workflow runs weekly:
- **Schedule**: Monday 10:00 JST (Sunday 01:00 UTC)
- **Manual trigger**: `workflow_dispatch` enabled
- **Independence**: Does not affect or depend on the daily protocol workflow
- **Data branch**: Pushes artifacts to the same `fx-daily-data` branch

## Confirmed / Pending / Unlabeled Handling

| Status | In strategy metrics? | In slice labels? | In tag analysis? |
|---|---|---|---|
| confirmed | Yes | Yes (labeled) | Yes |
| pending | Yes | No (unlabeled bucket) | No |
| (empty/missing) | Yes | No (unlabeled bucket) | No |

## Changes from v1

| Aspect | v1 | v2 |
|---|---|---|
| Data source | Database (SQLAlchemy) | CSV history files |
| Annotation awareness | None | Full (regime, volatility, intervention, tags) |
| Output format | Pydantic model | Dict (JSON-serializable) |
| Persistent artifacts | None | JSON, MD, CSV |
| Rebuild capability | None | Yes (from history + annotations) |
| Scheduled execution | None | Weekly GitHub Actions workflow |
| SQLAlchemy required | Yes | No |

## Non-Changes

The following are explicitly **not changed** by v2:

- UGH formulas and state judgment
- Baseline computation rules
- Forecast / outcome / evaluation judgment logic
- Request builder semantics
- Workflow engine internals
- Existing CSV / manifest column definitions
- DB schema
- Batch ID / outcome ID generation rules
- Existing `run_weekly_report` function (v1)
- Existing `WeeklyReportRequest` / `WeeklyReportResult` models
