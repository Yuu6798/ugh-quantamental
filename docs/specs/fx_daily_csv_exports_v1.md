# FX Daily CSV Exports v1 (Phase 2 Milestone 17a)

**Status:** Implemented
**Date:** 2026-03-16

---

## 1. Purpose

After each daily protocol run, human-readable CSV files are written alongside the SQLite
database.  They are derived exclusively from persisted records and require no recomputation
of engine values.

---

## 2. Scope

**In scope:**
- Per-day forecast, outcome, and evaluation CSV exports
- Deterministic file naming and deterministic column ordering
- Idempotent overwrite on rerun
- Integration with `FxDailyAutomationConfig` / `FxDailyAutomationResult`

**Out of scope:**
- New DB tables or schema changes
- New engine formulas or protocol logic
- Async execution, scheduling, or external connectors
- Rolling/append-only log files
- Notebook or report generation

---

## 3. File Layout

CSV files are written under `csv_output_dir`.  In GitHub Actions, this is set to
`{github.workspace}/data/csv` (absolute path) so that all files land inside the
`fx-daily-data` branch checkout and are committed on every run.

```
{csv_output_dir}/
├── latest/                                   ← fixed paths; external tools read here
│   ├── manifest.json                         ← machine-readable run metadata (always)
│   ├── forecast.csv                          ← latest forecast (always)
│   ├── outcome.csv                           ← latest outcome (only when generated)
│   └── evaluation.csv                        ← latest evaluation (only when generated)
├── history/
│   └── {YYYYMMDD}/
│       └── {forecast_batch_id}/              ← one dir per run (deterministic batch ID)
│           ├── forecast.csv
│           ├── outcome.csv                   ← only when generated
│           └── evaluation.csv               ← only when generated
├── forecasts/{pair}_{YYYYMMDD}_forecast.csv  ← legacy staging path (backward-compat)
├── outcomes/{pair}_{YYYYMMDD}_outcome.csv
└── evaluations/{pair}_{YYYYMMDD}_evaluation.csv
```

`YYYYMMDD` is the date of `as_of_jst` in JST.

### latest/ policy

- `latest/` contains the most recent run's outputs under fixed filenames.
- `outcome.csv` and `evaluation.csv` are **deleted** from `latest/` when not generated
  in the current run, so stale files from a previous run are never served.
- `manifest.json` is always written (or overwritten) whenever `forecast.csv` is written.
- **Idempotency:** Re-running the protocol for the same day overwrites the same paths.

### history/ policy

- `history/{YYYYMMDD}/{forecast_batch_id}/` is written once per batch.
- Because `forecast_batch_id` is deterministic for a given `(pair, as_of_jst,
  protocol_version)` triple, a same-day rerun lands in the same directory and
  overwrites it — this is the intended behaviour.
- `outcome.csv` and `evaluation.csv` appear only when generated.

---

## 4. Source of Truth

CSV values are loaded from persisted records only:

| CSV file      | Source repository method                                   |
|---------------|------------------------------------------------------------|
| forecast      | `FxForecastRepository.load_fx_forecast_batch(session, batch_id)` |
| outcome       | `FxOutcomeEvaluationRepository.load_fx_outcome_record(session, outcome_id)` |
| evaluation    | `FxOutcomeEvaluationRepository.load_fx_evaluation_batch(session, outcome_id)` |

---

## 5. Forecast CSV

**Filename:** `forecasts/{pair}_{YYYYMMDD}_forecast.csv`
**Rows:** 4 per daily batch (one per strategy kind), ordered by `forecast_id` ascending.

### Columns (in order)

| Column | Source |
|---|---|
| `forecast_id` | `ForecastRecord.forecast_id` |
| `forecast_batch_id` | `ForecastRecord.forecast_batch_id` |
| `pair` | `ForecastRecord.pair.value` |
| `strategy_kind` | `ForecastRecord.strategy_kind.value` |
| `as_of_jst` | `ForecastRecord.as_of_jst.isoformat()` |
| `window_end_jst` | `ForecastRecord.window_end_jst.isoformat()` |
| `forecast_direction` | `ForecastRecord.forecast_direction.value` |
| `expected_close_change_bp` | `ForecastRecord.expected_close_change_bp` |
| `expected_range_low` | `ForecastRecord.expected_range.low_price` or blank |
| `expected_range_high` | `ForecastRecord.expected_range.high_price` or blank |
| `primary_question` | `ForecastRecord.primary_question` or blank |
| `dominant_state` | `ForecastRecord.dominant_state.value` or blank |
| `prob_dormant` | `ForecastRecord.state_probabilities.dormant` or blank |
| `prob_setup` | `ForecastRecord.state_probabilities.setup` or blank |
| `prob_fire` | `ForecastRecord.state_probabilities.fire` or blank |
| `prob_expansion` | `ForecastRecord.state_probabilities.expansion` or blank |
| `prob_exhaustion` | `ForecastRecord.state_probabilities.exhaustion` or blank |
| `prob_failure` | `ForecastRecord.state_probabilities.failure` or blank |
| `q_dir` | `ForecastRecord.q_dir.value` or blank |
| `q_strength` | `ForecastRecord.q_strength` or blank |
| `s_q` | `ForecastRecord.s_q` or blank |
| `temporal_score` | `ForecastRecord.temporal_score` or blank |
| `grv_raw` | `ForecastRecord.grv_raw` or blank |
| `grv_lock` | `ForecastRecord.grv_lock` or blank |
| `alignment` | `ForecastRecord.alignment` or blank |
| `e_star` | `ForecastRecord.e_star` or blank |
| `mismatch_px` | `ForecastRecord.mismatch_px` or blank |
| `mismatch_sem` | `ForecastRecord.mismatch_sem` or blank |
| `conviction` | `ForecastRecord.conviction` or blank |
| `urgency` | `ForecastRecord.urgency` or blank |
| `disconfirmer_rule_count` | `len(ForecastRecord.disconfirmers)` |
| `theory_version` | `ForecastRecord.theory_version` |
| `engine_version` | `ForecastRecord.engine_version` |
| `schema_version` | `ForecastRecord.schema_version` |
| `protocol_version` | `ForecastRecord.protocol_version` |
| `market_data_vendor` | `ForecastRecord.market_data_provenance.vendor` |
| `market_data_feed_name` | `ForecastRecord.market_data_provenance.feed_name` |
| `market_data_price_type` | `ForecastRecord.market_data_provenance.price_type` |
| `market_data_resolution` | `ForecastRecord.market_data_provenance.resolution` |
| `market_data_timezone` | `ForecastRecord.market_data_provenance.timezone` |

---

## 6. Outcome CSV

**Filename:** `outcomes/{pair}_{YYYYMMDD}_outcome.csv`
**Rows:** 0 or 1 per day.

### Columns (in order)

| Column | Source |
|---|---|
| `outcome_id` | `OutcomeRecord.outcome_id` |
| `pair` | `OutcomeRecord.pair.value` |
| `window_start_jst` | `OutcomeRecord.window_start_jst.isoformat()` |
| `window_end_jst` | `OutcomeRecord.window_end_jst.isoformat()` |
| `realized_open` | `OutcomeRecord.realized_open` |
| `realized_high` | `OutcomeRecord.realized_high` |
| `realized_low` | `OutcomeRecord.realized_low` |
| `realized_close` | `OutcomeRecord.realized_close` |
| `realized_direction` | `OutcomeRecord.realized_direction.value` |
| `realized_close_change_bp` | `OutcomeRecord.realized_close_change_bp` |
| `realized_range_price` | `OutcomeRecord.realized_range_price` |
| `event_happened` | `OutcomeRecord.event_happened` |
| `event_tags` | `|`-joined tag values, or blank |
| `schema_version` | `OutcomeRecord.schema_version` |
| `protocol_version` | `OutcomeRecord.protocol_version` |
| `market_data_vendor` | `OutcomeRecord.market_data_provenance.vendor` |
| `market_data_feed_name` | `OutcomeRecord.market_data_provenance.feed_name` |
| `market_data_price_type` | `OutcomeRecord.market_data_provenance.price_type` |
| `market_data_resolution` | `OutcomeRecord.market_data_provenance.resolution` |
| `market_data_timezone` | `OutcomeRecord.market_data_provenance.timezone` |

---

## 7. Evaluation CSV

**Filename:** `evaluations/{pair}_{YYYYMMDD}_evaluation.csv`
**Rows:** 0 or 4 per day (one per strategy kind), ordered by `evaluation_id` ascending.

### Columns (in order)

| Column | Source |
|---|---|
| `evaluation_id` | `EvaluationRecord.evaluation_id` |
| `forecast_id` | `EvaluationRecord.forecast_id` |
| `outcome_id` | `EvaluationRecord.outcome_id` |
| `pair` | `EvaluationRecord.pair.value` |
| `strategy_kind` | `EvaluationRecord.strategy_kind.value` |
| `direction_hit` | `EvaluationRecord.direction_hit` |
| `range_hit` | `EvaluationRecord.range_hit` or blank |
| `close_error_bp` | `EvaluationRecord.close_error_bp` or blank |
| `magnitude_error_bp` | `EvaluationRecord.magnitude_error_bp` or blank |
| `state_proxy_hit` | `EvaluationRecord.state_proxy_hit` or blank |
| `mismatch_change_bp` | `EvaluationRecord.mismatch_change_bp` or blank |
| `realized_state_proxy` | `EvaluationRecord.realized_state_proxy` or blank |
| `actual_state_change` | `EvaluationRecord.actual_state_change` or blank |
| `disconfirmers_hit` | `|`-joined rule IDs, or blank |
| `disconfirmer_explained` | `EvaluationRecord.disconfirmer_explained` or blank |
| `evaluated_at_utc` | `EvaluationRecord.evaluated_at_utc.isoformat()` |
| `theory_version` | `EvaluationRecord.theory_version` |
| `engine_version` | `EvaluationRecord.engine_version` |
| `schema_version` | `EvaluationRecord.schema_version` |
| `protocol_version` | `EvaluationRecord.protocol_version` |

---

## 8. Null / blank policy

- Fields that are `None` are written as empty strings (blank cells), not as `"None"` or `"null"`.
- Tuple fields (`event_tags`, `disconfirmers_hit`) are serialized as `|`-joined strings; empty
  tuples produce a blank cell.
- Boolean values are written as `True` / `False` (Python defaults via `csv.DictWriter`).

---

## 9. Automation integration

`run_fx_daily_protocol_once` in `automation.py` exports CSVs after the protocol run when
`config.write_csv_exports` is `True`.  Skipped gracefully when:
- `forecast_batch_id` is `None` (forecast not generated)
- `outcome_id` is `None` (outcome not available for the run)

CSV paths are returned in `FxDailyAutomationResult.forecast_csv_path`,
`.outcome_csv_path`, `.evaluation_csv_path`.

---

## 10. Configuration

`FxDailyAutomationConfig`:
- `write_csv_exports: bool = True` — enable/disable CSV export
- `csv_output_dir: str = "./data/csv"` — root output directory

`scripts/run_fx_daily_protocol.py` reads:
- `FX_WRITE_CSV_EXPORTS` — set to `"0"` to disable (default: enabled)
- `FX_CSV_OUTPUT_DIR` — override output dir (default: `./data/csv`)

---

## 11. Module layout

| File | Purpose |
|---|---|
| `src/ugh_quantamental/fx_protocol/csv_exports.py` | Deterministic flattening, CSV write, layout publication, and manifest helpers |
| Updated `automation_models.py` | Config/result field additions (`write_csv_exports`, `csv_output_dir`, `manifest_path`) |
| Updated `automation.py` | Post-run CSV export, layout publication, and manifest generation |
| Updated `scripts/run_fx_daily_protocol.py` | Env var wiring, fail-fast path guard, and summary printing |

---

## 12. manifest.json specification

**Path:** `{csv_output_dir}/latest/manifest.json`

Written (overwritten) on every run that produces a forecast CSV.  Path values are
**relative to `csv_output_dir`** for portability.

| Field | Type | Description |
|---|---|---|
| `as_of_jst` | `string` | ISO-8601 datetime of the forecast window (`as_of_jst.isoformat()`) |
| `generated_at_utc` | `string` | UTC timestamp of manifest generation (`YYYY-MM-DDTHH:MM:SSZ`) |
| `forecast_batch_id` | `string` | Forecast batch identifier |
| `outcome_id` | `string \| null` | Outcome record ID, or `null` if not generated |
| `evaluation_count` | `integer` | Number of evaluation records (0 when not generated) |
| `forecast_csv_path` | `string` | Relative path — always `"latest/forecast.csv"` |
| `outcome_csv_path` | `string \| null` | Relative path, or `null` when outcome not generated |
| `evaluation_csv_path` | `string \| null` | Relative path, or `null` when evaluation not generated |
| `protocol_version` | `string` | Protocol version string |
| `theory_version` | `string` | Theory version string |
| `engine_version` | `string` | Engine version string |
| `schema_version` | `string` | Schema version string |

**External tool access pattern:**

1. Fetch `latest/manifest.json` from the data branch.
2. Read `forecast_csv_path` (always non-null) to get the forecast CSV.
3. Check `outcome_csv_path` / `evaluation_csv_path` — if non-null, fetch those CSVs too.
4. Use `as_of_jst` and `forecast_batch_id` to cross-reference history if needed.

---

## 13. Fail-fast path guard

`scripts/run_fx_daily_protocol.py` validates at startup (when `write_csv_exports=True`)
that `FX_CSV_OUTPUT_DIR` is a path **inside** `FX_DATA_DIR`.  If it is not, the script
prints `[ERROR]` and exits non-zero before any DB work.

This prevents the silent failure mode where CSVs are written to `code/data/csv` (inside
the code checkout) instead of `data/csv` (inside the data-branch checkout), which would
cause them to be lost after the Actions runner terminates.
