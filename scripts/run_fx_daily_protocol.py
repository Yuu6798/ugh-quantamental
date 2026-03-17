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
    sqlite_path = _env("FX_SQLITE_PATH")
    if not sqlite_path:
        sqlite_filename = _env("FX_SQLITE_FILENAME", "fx_protocol.db")
        data_dir = _env("FX_DATA_DIR", "./data")
        sqlite_path = os.path.join(data_dir, sqlite_filename)

    run_outcome = _env("FX_DISABLE_OUTCOME") != "1"
    run_forecast = _env("FX_DISABLE_FORECAST") != "1"
    write_csv_exports = _env("FX_WRITE_CSV_EXPORTS", "1") != "0"
    csv_output_dir = _env("FX_CSV_OUTPUT_DIR", "./data/csv") or "./data/csv"

    if fx_data_url:
        provider_name = f"custom ({fx_data_url})"
    elif alphavantage_api_key:
        provider_name = "alpha_vantage"
    else:
        provider_name = "yahoo_finance (public, fallback)"
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
        provider = AlphaVantageXMarketDataProvider(api_key=alphavantage_api_key)
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

    session_factory = create_session_factory(engine)
    with session_factory() as session:
        try:
            automation_result = run_fx_daily_protocol_once(config, provider, session)
            session.commit()
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
    print("=================================\n")


if __name__ == "__main__":
    main()
