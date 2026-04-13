#!/usr/bin/env python3
"""Daily FX protocol automation entrypoint.

Reads configuration from environment variables, initialises the database,
and runs one full daily protocol cycle for USDJPY.

Environment variables
---------------------
FX_DATA_URL          : optional custom market-data endpoint URL.
                       If set, the custom HttpJsonFxMarketDataProvider is used.
FX_DATA_AUTH_TOKEN   : optional bearer token for a custom endpoint (FX_DATA_URL must be set).
ALPHAVANTAGE_API_KEY : Alpha Vantage API key (free, register at https://www.alphavantage.co).
                       If set and FX_DATA_URL is not set, AlphaVantageXMarketDataProvider is used.
                       If neither FX_DATA_URL nor ALPHAVANTAGE_API_KEY is set, the built-in
                       Yahoo Finance public provider is used as fallback.
FX_DATA_BRANCH       : git data branch name (default: fx-daily-data, informational only)
FX_SQLITE_FILENAME   : SQLite filename under the data directory (default: fx_protocol.db)
FX_THEORY_VERSION    : UGH theory version (default: v1)
FX_ENGINE_VERSION    : UGH engine version (default: v1)
FX_SCHEMA_VERSION    : schema version (default: v1)
FX_PROTOCOL_VERSION  : protocol version (default: v1)
FX_SQLITE_PATH       : full path to SQLite file (overrides FX_SQLITE_FILENAME)
FX_DISABLE_OUTCOME   : set to "1" to skip outcome/evaluation workflow
FX_DISABLE_FORECAST  : set to "1" to skip forecast workflow
FX_WRITE_CSV_EXPORTS : set to "0" to disable CSV export (default: enabled)
FX_CSV_OUTPUT_DIR    : directory for CSV exports (default: ./data/csv)
FX_LAST_RETRY        : set to "1" on the final retry (16:00 JST) or manual dispatch.
                       When set, data-fetch errors fail hard (exit 1) instead of
                       skipping gracefully, so the data gap is visible in CI.
"""

from __future__ import annotations

import os
import sys


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _fail(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Run the daily FX protocol once and print a summary."""
    # --- Config from environment ---
    # Provider selection:
    #   FX_DATA_URL set              → HttpJsonFxMarketDataProvider (custom endpoint)
    #   ALPHAVANTAGE_API_KEY set     → AlphaVantageXMarketDataProvider (recommended)
    #   neither set                  → YahooFinanceFxMarketDataProvider (fallback)
    fx_data_url = _env("FX_DATA_URL")
    alphavantage_api_key = _env("ALPHAVANTAGE_API_KEY")

    theory_version = _env("FX_THEORY_VERSION", "v1")
    engine_version = _env("FX_ENGINE_VERSION", "v1")
    schema_version = _env("FX_SCHEMA_VERSION", "v1")
    protocol_version = _env("FX_PROTOCOL_VERSION", "v1")
    data_branch = _env("FX_DATA_BRANCH", "fx-daily-data")

    # SQLite path: full path wins, else build from filename.
    # data_dir is always resolved so the CSV path guard below can reference it
    # regardless of which branch is taken.
    data_dir = _env("FX_DATA_DIR", "./data")
    sqlite_path = _env("FX_SQLITE_PATH")
    if not sqlite_path:
        sqlite_filename = _env("FX_SQLITE_FILENAME", "fx_protocol.db")
        sqlite_path = os.path.join(data_dir, sqlite_filename)

    run_outcome = _env("FX_DISABLE_OUTCOME") != "1"
    run_forecast = _env("FX_DISABLE_FORECAST") != "1"
    write_csv_exports = _env("FX_WRITE_CSV_EXPORTS", "1") != "0"
    csv_output_dir = _env("FX_CSV_OUTPUT_DIR", "./data/csv") or "./data/csv"

    # Fail fast: csv_output_dir must be inside data_dir so that CSV files land
    # inside the data-branch checkout and get committed.  A relative path like
    # ./data/csv satisfies this when data_dir=./data; an absolute path outside
    # data_dir (e.g. /tmp/csv) would produce CSV files that are never pushed.
    if write_csv_exports:
        abs_csv = os.path.abspath(csv_output_dir)
        abs_data = os.path.abspath(data_dir)
        if abs_csv != abs_data and not abs_csv.startswith(abs_data + os.sep):
            _fail(
                f"FX_CSV_OUTPUT_DIR ({abs_csv}) must be inside FX_DATA_DIR ({abs_data}). "
                "CSV files written outside the data-branch checkout are not persisted. "
                "Set FX_CSV_OUTPUT_DIR to a path under FX_DATA_DIR."
            )

    if fx_data_url:
        provider_name = f"custom ({fx_data_url})"
    elif alphavantage_api_key:
        provider_name = "alpha_vantage → yahoo_finance (fallback)"
    else:
        provider_name = "yahoo_finance (public, no fallback)"
    print(f"[INFO] provider        = {provider_name}")
    print(f"[INFO] sqlite_path     = {sqlite_path}")
    print(f"[INFO] data_branch     = {data_branch}")
    print(f"[INFO] protocol_version= {protocol_version}")
    print(f"[INFO] run_forecast    = {run_forecast}")
    print(f"[INFO] run_outcome     = {run_outcome}")

    # --- Validate versions (fail fast before any DB work) ---
    for name, val in (
        ("FX_THEORY_VERSION", theory_version),
        ("FX_ENGINE_VERSION", engine_version),
        ("FX_SCHEMA_VERSION", schema_version),
        ("FX_PROTOCOL_VERSION", protocol_version),
    ):
        if not val:
            _fail(f"{name} must not be empty.")

    # --- Imports deferred to keep startup fast (SQLAlchemy) ---
    try:
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
        from ugh_quantamental.fx_protocol.data_sources import (
            AlphaVantageXMarketDataProvider,
            FallbackFxMarketDataProvider,
            HttpJsonFxMarketDataProvider,
            YahooFinanceFxMarketDataProvider,
        )
        from ugh_quantamental.persistence.db import (
            create_db_engine,
            create_session_factory,
        )
    except ImportError as exc:
        _fail(f"Failed to import required modules: {exc}")
        return  # unreachable but satisfies type checkers

    # --- Run Alembic migrations ---
    sqlite_dir = os.path.dirname(sqlite_path)
    if sqlite_dir:
        os.makedirs(sqlite_dir, exist_ok=True)

    db_url = f"sqlite:///{os.path.abspath(sqlite_path)}"
    print(f"[INFO] db_url          = {db_url}")

    import subprocess

    result_alembic = subprocess.run(
        [
            sys.executable, "-m", "alembic",
            "-x", f"sqlalchemy.url={db_url}",
            "upgrade", "head",
        ],
        capture_output=True,
        text=True,
    )
    if result_alembic.returncode != 0:
        print(result_alembic.stderr, file=sys.stderr)
        _fail(
            f"Alembic migration failed (exit {result_alembic.returncode}). "
            "Database schema may be out of date. Aborting to prevent data inconsistency."
        )
    print("[INFO] Alembic migrations applied.")
    engine = create_db_engine(db_url)

    # --- Instantiate provider ---
    if fx_data_url:
        provider = HttpJsonFxMarketDataProvider(url=fx_data_url)
    elif alphavantage_api_key:
        provider = FallbackFxMarketDataProvider(
            primary=AlphaVantageXMarketDataProvider(api_key=alphavantage_api_key),
            fallback=YahooFinanceFxMarketDataProvider(),
        )
    else:
        provider = YahooFinanceFxMarketDataProvider()

    # --- Run protocol ---
    config = FxDailyAutomationConfig(
        theory_version=theory_version,
        engine_version=engine_version,
        schema_version=schema_version,
        protocol_version=protocol_version,
        data_branch=data_branch,
        sqlite_path=sqlite_path,
        run_outcome_evaluation=run_outcome,
        run_forecast_generation=run_forecast,
        write_csv_exports=write_csv_exports,
        csv_output_dir=csv_output_dir,
    )

    from ugh_quantamental.fx_protocol.data_sources import FxDataFetchError

    session_factory = create_session_factory(engine)
    with session_factory() as session:
        try:
            automation_result = run_fx_daily_protocol_once(config, provider, session)
            session.commit()
        except FxDataFetchError as exc:
            session.rollback()
            is_last_retry = _env("FX_LAST_RETRY") == "1"
            if is_last_retry:
                # Final retry (16:00 JST) or manual dispatch — fail hard so
                # CI goes red and the data gap is visible.
                _fail(f"Data fetch failed on final retry: {exc}")
                return
            # Earlier retry (08:00 / 12:00 JST) — skip gracefully so CI
            # stays green; the next scheduled run will retry.
            print(f"[WARN] Data fetch failed (skipping): {exc}")
            print("[INFO] Retries remaining today — next run will retry automatically.")
            return
        except Exception as exc:
            session.rollback()
            _fail(f"Protocol run failed: {exc}")
            return

    # --- Summary ---
    print("\n=== FX Daily Protocol Summary ===")
    print(f"  as_of_jst          : {automation_result.as_of_jst}")
    print(f"  forecast_batch_id  : {automation_result.forecast_batch_id}")
    print(f"  forecast_created   : {automation_result.forecast_created}")
    print(f"  outcome_id         : {automation_result.outcome_id}")
    print(f"  outcome_recorded   : {automation_result.outcome_recorded}")
    print(f"  evaluation_count   : {automation_result.evaluation_count}")
    if automation_result.forecast_csv_path:
        print(f"  forecast_csv       : {automation_result.forecast_csv_path}")
    if automation_result.outcome_csv_path:
        print(f"  outcome_csv        : {automation_result.outcome_csv_path}")
    if automation_result.evaluation_csv_path:
        print(f"  evaluation_csv     : {automation_result.evaluation_csv_path}")
    if automation_result.manifest_path:
        print(f"  manifest           : {automation_result.manifest_path}")
    if automation_result.annotation_analytics:
        for key, val in automation_result.annotation_analytics.items():
            if val:
                print(f"  {key}: {val}")
    print("=================================\n")

    # --- Weekly report generation (Friday, final attempt only) ---
    # On Friday's last scheduled run, auto-generate the weekly report so it
    # is available the same evening instead of waiting for Monday's analysis
    # pipeline.  Guarded by FX_LAST_RETRY to avoid redundant rebuilds on
    # earlier retry runs (each would write a different generated_at_utc and
    # create extra commits).
    #
    # Uses run_weekly_report_v2 (read-only) + export_weekly_report_artifacts
    # rather than rebuild_weekly_report, which destructively deletes
    # labeled_observations.csv before rebuilding.  This way a failure here
    # cannot corrupt the analytics state rebuilt in Step 8 above.
    # The Monday analysis pipeline remains as a safety-net fallback.
    _is_last_attempt = _env("FX_LAST_RETRY") == "1"
    # Gate on Step 8 success: annotation_analytics contains the result of
    # run_annotation_analytics().  If it is None or labeled_observations_path
    # is missing, the labeled_observations.csv may be stale or absent and we
    # must not publish a weekly report built from outdated data.
    _has_fresh_observations = bool(
        automation_result.annotation_analytics
        and automation_result.annotation_analytics.get("labeled_observations_path")
    )
    if (
        write_csv_exports
        and automation_result.as_of_jst.isoweekday() == 5
        and _is_last_attempt
        and _has_fresh_observations
    ):
        print("--- Weekly report (Friday auto-trigger) ---")
        try:
            from datetime import datetime, timedelta, timezone

            from ugh_quantamental.fx_protocol.weekly_report_exports import (
                export_weekly_report_artifacts,
            )
            from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
                run_weekly_report_v2,
            )

            # report_date = Saturday so _resolve_week_window covers Mon–Fri.
            _report_date = (automation_result.as_of_jst + timedelta(days=1)).replace(
                hour=8, minute=0, second=0, microsecond=0,
            )
            weekly_result = run_weekly_report_v2(
                csv_output_dir,
                _report_date,
                generated_at_utc=datetime.now(timezone.utc),
            )
            _date_str = _report_date.strftime("%Y%m%d")
            export_weekly_report_artifacts(weekly_result, csv_output_dir, _date_str)

            _obs = weekly_result.get("observation_count", 0)
            _ww = weekly_result.get("week_window", {})
            print(f"  week_window    : {_ww.get('start', '?')} - {_ww.get('end', '?')}")
            print(f"  observations   : {_obs}")
            print("[OK] Weekly report generated.")
        except Exception as exc:
            print(f"[WARN] Weekly report generation failed (non-fatal): {exc}")


if __name__ == "__main__":
    main()
