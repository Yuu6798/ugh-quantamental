# FX Weekly Report v1 — Phase 2 Milestone 16

## Purpose

The weekly FX report provides read-only monitoring over persisted forecast,
outcome, and evaluation data for a single currency pair.  It aggregates
per-forecast evaluation rows into weekly strategy metrics, baseline comparisons,
state/GRV/mismatch summaries, and curated case examples.

The report is generated on demand.  It does not write any data and requires no
new persistence tables.  It is intentionally separate from the monthly review /
version governance layer (deferred to a future milestone).

---

## Completed-window selection

A "completed window" is a protocol forecast window whose `window_end_jst`
(08:00 JST on a Mon–Fri business day) has already passed at the time the
report is generated.

**Algorithm** (`resolve_completed_window_ends`):

1. Normalize `report_generated_at_jst` to Asia/Tokyo.
2. Compute the 08:00 JST anchor on the same calendar date.
   - If the anchor is strictly after `report_generated_at_jst` (i.e. the report
     is generated before 08:00), move the anchor one calendar day back.
3. Walk backward day by day; collect each Mon–Fri 08:00 JST timestamp until
   `business_day_count` values have been gathered.
4. Return the values in chronological order (oldest first).

**Examples**:

| `report_generated_at_jst` | `business_day_count` | Latest completed window_end |
|---|---|---|
| Monday 10:00 | 5 | Monday 08:00 |
| Monday 07:59 | 5 | Previous Friday 08:00 |
| Saturday 14:00 | 5 | Previous Friday 08:00 |
| Sunday 00:00 | 5 | Previous Friday 08:00 |

---

## Report request

```
WeeklyReportRequest
  pair                    : CurrencyPair
  report_generated_at_jst : datetime
  business_day_count      : int  (>= 1, default 5)
  max_examples            : int  (>= 1, default 3)
```

Report generation may happen on weekends.  The algorithm above handles this
correctly without special casing.

---

## Data loading policy

`run_weekly_report` is read-only.  It:

1. Resolves the `business_day_count` most recent completed `window_end_jst`
   timestamps.
2. Queries `FxEvaluationRecord` by `(pair, window_end_jst IN (...))`.
3. Loads corresponding `FxForecastRecord` rows (by `forecast_id`) in a single
   batch query.
4. Loads corresponding `FxOutcomeRecord` rows (by `outcome_id`) in a single
   batch query.
5. Builds metrics and returns `WeeklyReportResult`.

No data is written, flushed, or committed.

---

## Missing-window handling

If some requested `window_end_jst` values have no evaluation rows in the DB,
they are counted in `missing_window_count`.  The report is built from the
available windows only.

If **zero** windows have data, `run_weekly_report` raises `ValueError` with a
clear message.  A report with no data provides no signal and must not silently
return empty metrics.

---

## Strategy metrics (`StrategyWeeklyMetrics`)

Computed separately for: `ugh`, `baseline_random_walk`,
`baseline_prev_day_direction`, `baseline_simple_technical`.

| Field | Rule |
|---|---|
| `forecast_count` | Total rows for the strategy |
| `direction_evaluable_count` | Rows where `direction_hit` is not None (always == forecast_count in v1) |
| `direction_hit_count` | Rows where `direction_hit == True` |
| `direction_accuracy` | `direction_hit_count / direction_evaluable_count`; `None` when count == 0 |
| `range_evaluable_count` | Rows where `range_hit` is not None; **0 for baselines** |
| `range_hit_count` | Rows where `range_hit == True`; **0 for baselines** |
| `range_hit_rate` | `range_hit_count / range_evaluable_count`; **None for baselines** |
| `mean_abs_close_error_bp` | Mean of non-null `close_error_bp` values |
| `mean_abs_magnitude_error_bp` | Mean of non-null `magnitude_error_bp` values |

---

## Baseline comparison (`BaselineWeeklyComparison`)

For each baseline strategy, compare against UGH:

| Field | Rule |
|---|---|
| `direction_accuracy_delta_vs_ugh` | `baseline.direction_accuracy − ugh.direction_accuracy`; `None` if either is `None` |
| `mean_abs_close_error_bp_delta_vs_ugh` | `baseline.mean_abs_close_error_bp − ugh.mean_abs_close_error_bp`; `None` if either is `None` |

Negative delta in accuracy means the baseline underperforms UGH.
Positive delta in error means the baseline has higher error than UGH.

---

## State metrics (`StateWeeklyMetrics`)

UGH rows only.  Bucket by `dominant_state`:

| Field | Rule |
|---|---|
| `forecast_count` | Rows in this state bucket |
| `direction_accuracy` | Hit rate within bucket; `None` if count == 0 |
| `mean_abs_close_error_bp` | Mean of non-null `close_error_bp`; `None` if none available |

---

## GRV / fire summary (`WeeklyGrvFireSummary`)

UGH rows only.  Fire bucket = `dominant_state == "fire"`.

| Field | Rule |
|---|---|
| `fire_count` | Rows where `dominant_state == "fire"` |
| `non_fire_count` | Rows where `dominant_state != "fire"` |
| `mean_grv_lock_fire` | Mean `grv_lock` for fire rows; `None` if no non-null values |
| `mean_grv_lock_non_fire` | Mean `grv_lock` for non-fire rows; `None` if no non-null values |
| `fire_direction_accuracy` | Hit rate for fire rows; `None` if fire_count == 0 |

---

## Mismatch summary (`WeeklyMismatchSummary`)

UGH rows only.  Bucket by sign of `mismatch_px`:

| Field | Rule |
|---|---|
| `positive_mismatch_count` | Rows where `mismatch_px > 0` |
| `non_positive_mismatch_count` | Rows where `mismatch_px <= 0` |
| `positive_mismatch_direction_accuracy` | Hit rate for positive bucket; `None` if count == 0 |
| `non_positive_mismatch_direction_accuracy` | Hit rate for non-positive bucket; `None` if count == 0 |

Rows where `mismatch_px is None` are excluded from both buckets.

---

## Disconfirmer explained rate

UGH rows only.  Mean of `disconfirmer_explained == True` over rows where
`disconfirmer_explained is not None`.  `None` if no such rows exist.

---

## Case example selection (`WeeklyCaseExample`)

All case examples are UGH rows only.

### False-positive cases
- Rows where `direction_hit == False`
- Sort: descending `conviction`, descending `close_error_bp`
- Take up to `max_examples`

### Representative successes
- Rows where `direction_hit == True`
- Sort: descending `conviction`, ascending `close_error_bp`
- Take up to `max_examples`

### Representative failures
- Rows where `direction_hit == False`
- Sort: descending `close_error_bp`, descending `conviction`
- Take up to `max_examples`

Note: false-positive cases and representative failures both draw from
`direction_hit == False` rows but use different sort keys, yielding
complementary views.

---

## Output shape (`WeeklyReportResult`)

```
WeeklyReportResult
  pair                           : CurrencyPair
  report_generated_at_jst        : datetime
  window_end_jst_values          : tuple[datetime, ...]   # resolved window ends
  requested_window_count         : int
  included_window_count          : int
  missing_window_count           : int
  strategy_metrics               : tuple[StrategyWeeklyMetrics, ...]
  baseline_comparisons           : tuple[BaselineWeeklyComparison, ...]
  state_metrics                  : tuple[StateWeeklyMetrics, ...]
  grv_fire_summary               : WeeklyGrvFireSummary
  mismatch_summary               : WeeklyMismatchSummary
  ugh_disconfirmer_explained_rate : float | None
  false_positive_cases           : tuple[WeeklyCaseExample, ...]
  representative_successes       : tuple[WeeklyCaseExample, ...]
  representative_failures        : tuple[WeeklyCaseExample, ...]
```

---

## Intentionally deferred

The following are **not** implemented in this milestone:

- **Monthly review / version governance** — periodic roll-up and governance
  workflow comparing model versions.
- **Persisted report storage** — the weekly report is ephemeral; each call
  re-reads from persisted evaluation records.
- **Scheduling** — no cron, scheduler, or background job integration.
- **Event-regime bucketing beyond raw tags** — event tags are stored in
  `OutcomeRecord` but regime-level aggregation (e.g. FOMC-week vs. normal) is
  not computed in this milestone.
- **Richer error metrics** — MASE, sMAPE, calibration curves, Brier scores,
  and confidence-interval coverage are out of scope for v1.
- **Multi-pair aggregation** — the report is scoped to a single `CurrencyPair`.
- **CLI / notebook / API layer** — the report is a pure Python function call.
