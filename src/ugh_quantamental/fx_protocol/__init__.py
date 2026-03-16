"""FX Daily Protocol v1 — Phase 2 Milestone 13.

This package provides the frozen protocol contracts, deterministic calendar helpers,
and deterministic ID generation for the FX daily prediction cycle.

Importable without SQLAlchemy.
"""

from __future__ import annotations

from ugh_quantamental.fx_protocol.forecast_models import (
    BaselineContext,
    DailyForecastBatch,
    DailyForecastWorkflowRequest,
    PersistedDailyForecastBatch,
)
from ugh_quantamental.fx_protocol.models import (
    CurrencyPair,
    DisconfirmerRule,
    EvaluationRecord,
    EventTag,
    ExpectedRange,
    ForecastDirection,
    ForecastRecord,
    MarketDataProvenance,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.outcome_models import (
    DailyOutcomeWorkflowRequest,
    PersistedOutcomeEvaluationBatch,
)
from ugh_quantamental.fx_protocol.automation_models import (
    FxDailyAutomationConfig,
    FxDailyAutomationResult,
)
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.report_models import (
    BaselineWeeklyComparison,
    StateWeeklyMetrics,
    StrategyWeeklyMetrics,
    WeeklyCaseExample,
    WeeklyGrvFireSummary,
    WeeklyMismatchSummary,
    WeeklyReportRequest,
    WeeklyReportResult,
)

__all__ = [
    "BaselineContext",
    "DailyForecastBatch",
    "DailyForecastWorkflowRequest",
    "DailyOutcomeWorkflowRequest",
    "CurrencyPair",
    "DisconfirmerRule",
    "EvaluationRecord",
    "EventTag",
    "ExpectedRange",
    "ForecastDirection",
    "ForecastRecord",
    "MarketDataProvenance",
    "PersistedDailyForecastBatch",
    "PersistedOutcomeEvaluationBatch",
    "OutcomeRecord",
    "StrategyKind",
    "FxDailyAutomationConfig",
    "FxDailyAutomationResult",
    "FxCompletedWindow",
    "FxProtocolMarketSnapshot",
    "BaselineWeeklyComparison",
    "StateWeeklyMetrics",
    "StrategyWeeklyMetrics",
    "WeeklyCaseExample",
    "WeeklyGrvFireSummary",
    "WeeklyMismatchSummary",
    "WeeklyReportRequest",
    "WeeklyReportResult",
]
