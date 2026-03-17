"""Typed config and result models for the FX Daily Automation layer (v1).

Importable without SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ugh_quantamental.fx_protocol.models import CurrencyPair


class FxDailyAutomationConfig(BaseModel):
    """Configuration for one run of the FX daily automation protocol."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pair: CurrencyPair = CurrencyPair.USDJPY
    theory_version: str = Field(default="v1", min_length=1)
    engine_version: str = Field(default="v1", min_length=1)
    schema_version: str = Field(default="v1", min_length=1)
    protocol_version: str = Field(default="v1", min_length=1)
    data_branch: str = Field(default="fx-daily-data", min_length=1)
    sqlite_path: str = Field(default="./data/fx_protocol.db", min_length=1)
    run_outcome_evaluation: bool = True
    run_forecast_generation: bool = True
    input_snapshot_ref: str = Field(default="auto", min_length=1)
    write_csv_exports: bool = True
    csv_output_dir: str = Field(default="./data/csv", min_length=1)


class FxDailyAutomationResult(BaseModel):
    """Result of one completed FX daily automation run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of_jst: datetime
    forecast_batch_id: str | None = None
    outcome_id: str | None = None
    forecast_created: bool = False
    outcome_recorded: bool = False
    evaluation_count: int = 0
    data_commit_created: bool = False
    forecast_csv_path: str | None = None
    outcome_csv_path: str | None = None
    evaluation_csv_path: str | None = None
    manifest_path: str | None = None
