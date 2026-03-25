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
from ugh_quantamental.fx_protocol.csv_exports import (
    EVALUATION_FIELDNAMES,
    FORECAST_FIELDNAMES,
    OUTCOME_FIELDNAMES,
    evaluation_records_to_rows,
    export_daily_evaluation_csv,
    export_daily_forecast_csv,
    export_daily_outcome_csv,
    forecast_records_to_rows,
    make_daily_csv_stem,
    outcome_record_to_rows,
    write_csv_rows,
)
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.observability import (
    PROVIDER_HEALTH_FIELDNAMES,
    SCOREBOARD_FIELDNAMES,
    build_daily_report_md,
    build_input_snapshot,
    build_provider_health_row,
    build_run_summary,
    build_scoreboard_rows,
    collect_all_evaluations_from_history,
    publish_observability_to_layout,
)
from ugh_quantamental.fx_protocol.analytics_annotations import (
    AI_ANNOTATION_FIELDNAMES,
    LABELED_OBSERVATION_FIELDNAMES,
    MANUAL_ANNOTATION_FIELDNAMES,
    SLICE_SCOREBOARD_FIELDNAMES,
    TAG_SCOREBOARD_FIELDNAMES,
    build_labeled_observations,
    build_slice_scoreboard,
    build_tag_scoreboard,
    generate_ai_annotations,
    generate_manual_annotation_template,
    load_manual_annotations,
    run_annotation_analytics,
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
from ugh_quantamental.fx_protocol.weekly_reports_v2 import (
    WEEKLY_SLICE_METRICS_FIELDNAMES,
    WEEKLY_STRATEGY_METRICS_FIELDNAMES,
    run_weekly_report_v2,
)
from ugh_quantamental.fx_protocol.weekly_report_exports import (
    build_weekly_report_md,
    export_weekly_report_artifacts,
    export_weekly_report_json,
    export_weekly_report_md,
    export_weekly_slice_metrics_csv,
    export_weekly_strategy_metrics_csv,
)
from ugh_quantamental.fx_protocol.analytics_rebuild import (
    rebuild_annotation_analytics,
    rebuild_weekly_report,
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
    # observability
    "PROVIDER_HEALTH_FIELDNAMES",
    "SCOREBOARD_FIELDNAMES",
    "build_daily_report_md",
    "build_input_snapshot",
    "build_provider_health_row",
    "build_run_summary",
    "build_scoreboard_rows",
    "collect_all_evaluations_from_history",
    "publish_observability_to_layout",
    # csv_exports
    "EVALUATION_FIELDNAMES",
    "FORECAST_FIELDNAMES",
    "OUTCOME_FIELDNAMES",
    "evaluation_records_to_rows",
    "export_daily_evaluation_csv",
    "export_daily_forecast_csv",
    "export_daily_outcome_csv",
    "forecast_records_to_rows",
    "make_daily_csv_stem",
    "outcome_record_to_rows",
    "write_csv_rows",
    # analytics_annotations
    "AI_ANNOTATION_FIELDNAMES",
    "LABELED_OBSERVATION_FIELDNAMES",
    "MANUAL_ANNOTATION_FIELDNAMES",
    "SLICE_SCOREBOARD_FIELDNAMES",
    "TAG_SCOREBOARD_FIELDNAMES",
    "build_labeled_observations",
    "build_slice_scoreboard",
    "build_tag_scoreboard",
    "generate_ai_annotations",
    "generate_manual_annotation_template",
    "load_manual_annotations",
    "run_annotation_analytics",
    # weekly_reports_v2
    "WEEKLY_SLICE_METRICS_FIELDNAMES",
    "WEEKLY_STRATEGY_METRICS_FIELDNAMES",
    "run_weekly_report_v2",
    # weekly_report_exports
    "build_weekly_report_md",
    "export_weekly_report_artifacts",
    "export_weekly_report_json",
    "export_weekly_report_md",
    "export_weekly_slice_metrics_csv",
    "export_weekly_strategy_metrics_csv",
    # analytics_rebuild
    "rebuild_annotation_analytics",
    "rebuild_weekly_report",
]
