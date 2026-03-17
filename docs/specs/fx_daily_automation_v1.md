# FX Daily Automation v1

## Overview

This document specifies the automated daily execution layer for the FX Daily Protocol (Phase 2).
It covers data ingestion, request construction, orchestration, durable storage, and GitHub Actions scheduling.

Milestones 13, 14, and 15 define the protocol schema, forecast workflow, and outcome/evaluation workflow respectively.
This document specifies the operational automation layer that drives those workflows on a daily cadence.

---

## Scope

- USDJPY only (v1)
- GitHub Actions schedule-triggered execution
- Durable SQLite storage via a dedicated Git data branch
- No weekly/monthly reporting
- No async, no external broker, no scheduler framework
- No new core protocol logic

---

## Data model (`data_models.py`)

### `FxCompletedWindow`

A single completed OHLC window with event annotations.

| Field | Type | Description |
|---|---|---|
| `window_start_jst` | `datetime` | 08:00 JST on a business day (canonical open) |
| `window_end_jst` | `datetime` | 08:00 JST on the next business day (canonical close) |
| `open_price` | `float` | Canonical open price (positive finite) |
| `high_price` | `float` | Canonical high price |
| `low_price` | `float` | Canonical low price |
| `close_price` | `float` | Canonical close price |
| `event_tags` | `tuple[EventTag, ...]` | Zero or more event tags for this window |

Ordering: `completed_windows` in `FxProtocolMarketSnapshot` must be ordered oldest→newest.

### `FxProtocolMarketSnapshot`

Typed provider output for one USDJPY market snapshot.

| Field | Type | Description |
|---|---|---|
| `pair` | `CurrencyPair` | Always `USDJPY` for v1 |
| `as_of_jst` | `datetime` | Canonical 08:00 JST timestamp for today's forecast window |
| `current_spot` | `float` | Current mid spot price |
| `completed_windows` | `tuple[FxCompletedWindow, ...]` | At least 20 completed windows, oldest first |
| `market_data_provenance` | `MarketDataProvenance` | Source metadata |

---

## Data provider abstraction (`data_sources.py`)

### `FxMarketDataProvider` (protocol)

A structural typing protocol:

```python
class FxMarketDataProvider(Protocol):
    def fetch_snapshot(self, as_of_jst: datetime) -> FxProtocolMarketSnapshot: ...
```

Provider selection order (evaluated by the script entrypoint):

1. `FX_DATA_URL` set → `HttpJsonFxMarketDataProvider` (custom private endpoint)
2. `ALPHAVANTAGE_API_KEY` set → `AlphaVantageXMarketDataProvider` (**recommended**)
3. Neither set → `YahooFinanceFxMarketDataProvider` (public fallback, no auth)

### `AlphaVantageXMarketDataProvider` (recommended)

Uses the [Alpha Vantage](https://www.alphavantage.co) `FX_DAILY` endpoint (free API key required).

Endpoint:
```
https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=USD&to_symbol=JPY&outputsize=full&apikey=<key>
```

- Requires `ALPHAVANTAGE_API_KEY` set as a GitHub Actions repository secret.
- Uses only stdlib `urllib.request`; no third-party SDK dependency.
- `outputsize=full` returns full daily history; completed windows are filtered to those
  with `window_end_jst ≤ as_of_jst`.
- **Freshness guard:** the provider allows up to **1 business-day provider lag** before
  raising a `ValueError`.  This tolerates the ~24-hour data publication delay that is
  common with free-tier Alpha Vantage keys.
- **`current_spot`** is set to the `close_price` of the newest completed window (not a
  separate live quote field), which avoids look-ahead contamination.

### `YahooFinanceFxMarketDataProvider` (public fallback)

Uses the Yahoo Finance chart API with no authentication.

Endpoint:
```
https://query2.finance.yahoo.com/v8/finance/chart/USDJPY=X?interval=1d&range=60d
```

- No API key, no GitHub Secrets required.
- Uses only stdlib `urllib.request`.
- Returns the last 60 calendar days of daily OHLC bars.
- `current_spot` is taken from `meta.regularMarketPrice` in the response.

### `HttpJsonFxMarketDataProvider` (optional, custom endpoint)

Retained for users who have a private data feed.  Requires `FX_DATA_URL`.

Configuration via environment variables:
- `FX_DATA_URL` — base URL for the data endpoint (required for this provider only)
- `FX_DATA_AUTH_TOKEN` — optional bearer token

---

## Normalization rule: public source → protocol windows

Both `YahooFinanceFxMarketDataProvider` and `AlphaVantageXMarketDataProvider` map raw daily
bars to protocol windows as follows (deterministic):

| Step | Operation |
|---|---|
| 1 | Parse the bar date string (or Unix timestamp) and convert to JST |
| 2 | Discard bars whose JST date is Saturday or Sunday |
| 3 | `window_start_jst` = 08:00 JST on the JST date of the bar |
| 4 | `window_end_jst` = `next_as_of_jst(window_start_jst)` = 08:00 JST next business day |
| 5 | Only include windows where `window_end_jst ≤ as_of_jst` (completed windows) |
| 6 | If `high < low` (rare FX artefact): swap them |
| 7 | Clamp `open` and `close` to `[low, high]` to tolerate floating-point drift |

`current_spot` derivation differs by provider:

| Provider | `current_spot` source |
|---|---|
| `YahooFinanceFxMarketDataProvider` | `meta.regularMarketPrice` from the API response |
| `AlphaVantageXMarketDataProvider` | `close_price` of the **newest completed window** (avoids look-ahead contamination) |
| `HttpJsonFxMarketDataProvider` | `current_spot` field from the JSON payload |

---

## Request builders (`request_builders.py`)

### `build_baseline_context(snapshot) -> BaselineContext`

Derives `BaselineContext` from the last 20+ completed windows:

- `current_spot` = `snapshot.current_spot`
- `previous_close_change_bp` = close change in basis points of the most recent completed window
- `trailing_mean_range_price` = mean of `(high - low)` over last 20 completed windows
- `trailing_mean_abs_close_change_bp` = mean of `|close_change_bp|` over last 20 completed windows
- `sma5` = mean of close prices over last 5 completed windows
- `sma20` = mean of close prices over last 20 completed windows
- `warmup_window_count` = `len(completed_windows)`

### `build_daily_forecast_request(snapshot, *, theory_version, engine_version, schema_version, protocol_version) -> DailyForecastWorkflowRequest`

Builds a complete `DailyForecastWorkflowRequest` from a market snapshot.
Uses `build_baseline_context` for the baseline context field.
The `ugh_request` field must be constructed by the caller or injected; this function raises `NotImplementedError` for UGH-specific inputs and documents the required caller contract.

### `build_daily_outcome_request(snapshot, *, schema_version, protocol_version) -> DailyOutcomeWorkflowRequest`

Builds a `DailyOutcomeWorkflowRequest` from the most recent completed window (newest in `completed_windows`).

---

## Automation layer

### `FxDailyAutomationConfig` (`automation_models.py`)

| Field | Type | Description |
|---|---|---|
| `pair` | `CurrencyPair` | Target pair |
| `theory_version` | `str` | UGH theory version string |
| `engine_version` | `str` | UGH engine version string |
| `schema_version` | `str` | Schema version string |
| `protocol_version` | `str` | Protocol version string |
| `data_branch` | `str` | Git branch for durable data storage (default: `fx-daily-data`) |
| `sqlite_path` | `str` | Path to SQLite file in the data branch checkout |
| `run_outcome_evaluation` | `bool` | Whether to run outcome/evaluation workflow |
| `run_forecast_generation` | `bool` | Whether to run forecast workflow |
| `write_csv_exports` | `bool` | Whether to write CSV exports after each run (default: `True`) |
| `csv_output_dir` | `str` | Root directory for CSV output files (default: `./data/csv`) |

### `FxDailyAutomationResult` (`automation_models.py`)

| Field | Type | Description |
|---|---|---|
| `as_of_jst` | `datetime` | Canonical as_of_jst for this run |
| `forecast_batch_id` | `str \| None` | Batch ID if forecast was created or already existed |
| `outcome_id` | `str \| None` | Outcome ID if outcome was recorded |
| `forecast_created` | `bool` | Whether a new forecast batch was created |
| `outcome_recorded` | `bool` | Whether a new outcome was recorded |
| `evaluation_count` | `int` | Number of evaluation records |
| `data_commit_created` | `bool` | Whether the data branch was updated (set by caller/script) |
| `forecast_csv_path` | `str \| None` | Path of the written forecast CSV, or `None` if skipped |
| `outcome_csv_path` | `str \| None` | Path of the written outcome CSV, or `None` if skipped |
| `evaluation_csv_path` | `str \| None` | Path of the written evaluation CSV, or `None` if skipped |

### `run_fx_daily_protocol_once(config, provider, session) -> FxDailyAutomationResult`

Orchestration function in `automation.py`:

1. Determine canonical `as_of_jst` (08:00 JST today or previous business day)
2. Fetch one USDJPY snapshot via `provider.fetch_snapshot(as_of_jst)`
3. Build `DailyForecastWorkflowRequest` using request builders
4. If `config.run_forecast_generation`: call `run_daily_forecast_workflow`; idempotent
5. If `config.run_outcome_evaluation` and prior window data is available in snapshot: call `run_daily_outcome_evaluation_workflow`; idempotent
6. If `config.write_csv_exports`: write forecast / outcome / evaluation CSVs under `config.csv_output_dir`; skipped gracefully when the relevant batch or outcome ID is `None`
7. Return `FxDailyAutomationResult`

Idempotency: rerunning the same `as_of_jst` must not duplicate records. Both workflows are already idempotent per Milestones 14 and 15. CSV exports overwrite the same deterministic paths on each rerun.

---

## Durable storage strategy

GitHub Actions runners are ephemeral; the SQLite database would be lost after each run.

Strategy:
- Maintain a dedicated Git branch (`fx-daily-data`) separate from the code branch
- Check out this branch into a subdirectory during the workflow
- Run Alembic migrations against the SQLite file in that directory
- After protocol execution, commit and push the updated SQLite (and any log files) back to `fx-daily-data`
- The code branch (`main`) is never modified by the data workflow

Rationale:
- SQLite + Git is simple, auditable, and requires no external storage service
- The data branch accumulates history; individual runs are commit-stamped
- SQLite files are small enough for this research/scaffold use case

---

## GitHub Actions workflow (`.github/workflows/fx-daily-protocol.yml`)

### Triggers

- `schedule`: `0 23 * * 0-4` (UTC) = 08:00 JST Mon–Fri
- `workflow_dispatch`: manual trigger

### Permissions

```yaml
permissions:
  contents: write
```

Required to push to the data branch.

### Steps

1. Check out code branch
2. Set up Python 3.11
3. Install dependencies (`pip install -e .`)
4. Check out or create `fx-daily-data` branch into `./data`
5. Run Alembic migrations against `./data/fx_protocol.db`
6. Run `python scripts/run_fx_daily_protocol.py`
7. If data branch changed: commit and push to `fx-daily-data`

### Environment variables

Provider selection: `FX_DATA_URL` (custom) → `ALPHAVANTAGE_API_KEY` (recommended) → Yahoo Finance (public fallback).
Set `ALPHAVANTAGE_API_KEY` as a **repository secret** (Settings → Secrets → Actions) for the recommended provider.

| Variable | Kind | Required | Description |
|---|---|---|---|
| `ALPHAVANTAGE_API_KEY` | Secret | No | Alpha Vantage API key; activates `AlphaVantageXMarketDataProvider` (recommended) |
| `FX_DATA_URL` | Secret | No | Custom private endpoint URL; takes precedence over `ALPHAVANTAGE_API_KEY` |
| `FX_DATA_AUTH_TOKEN` | Secret | No | Bearer token for custom endpoint only |
| `FX_DATA_BRANCH` | Variable | No | Data branch name (default: `fx-daily-data`) |
| `FX_SQLITE_FILENAME` | Variable | No | SQLite filename (default: `fx_protocol.db`) |
| `FX_THEORY_VERSION` | Variable | No | Theory version (default: `v1`) |
| `FX_ENGINE_VERSION` | Variable | No | Engine version (default: `v1`) |
| `FX_SCHEMA_VERSION` | Variable | No | Schema version (default: `v1`) |
| `FX_PROTOCOL_VERSION` | Variable | No | Protocol version (default: `v1`) |
| `FX_WRITE_CSV_EXPORTS` | Variable | No | Set to `"0"` to disable CSV exports (default: enabled) |
| `FX_CSV_OUTPUT_DIR` | Variable | No | Root directory for CSV output (default: `./data/csv`) |

---

## Script entrypoint (`scripts/run_fx_daily_protocol.py`)

- Reads all config from environment variables
- Initializes DB engine against the SQLite file
- Runs Alembic migrations
- Selects provider by priority: `FX_DATA_URL` → `ALPHAVANTAGE_API_KEY` → Yahoo Finance fallback
- Creates a session and calls `run_fx_daily_protocol_once`
- Prints a concise summary including provider name and CSV paths
- Exits non-zero on validation failure

---

## Out of scope (v1)

- Weekly reporting
- Monthly review
- Multi-pair support
- Intraday or high-frequency data
- External broker integration
- Async execution
- General scheduler framework
- ML calibration
