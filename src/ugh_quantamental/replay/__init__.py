"""Deterministic replay / regression layer for persisted runs (v1).

Import isolation policy:
- ``replay.models``, ``replay.batch_models``, and ``replay.baseline_models`` are
  importable without SQLAlchemy.
- ``replay.runners``, ``replay.batch``, and ``replay.baselines`` require SQLAlchemy
  at call time (imported lazily via TYPE_CHECKING).
"""

from __future__ import annotations

from ugh_quantamental.replay.baseline_models import (
    CompareRegressionBaselineRequest,
    CreateRegressionBaselineRequest,
    RegressionBaselineComparison,
    RegressionBaselineCompareResult,
    RegressionSuiteBaseline,
    RegressionSuiteBaselineBundle,
    RegressionSuiteCaseDelta,
)
from ugh_quantamental.replay.batch_models import (
    BatchReplayStatus,
    ProjectionBatchReplayAggregate,
    ProjectionBatchReplayItem,
    ProjectionBatchReplayRequest,
    ProjectionBatchReplayResult,
    StateBatchReplayAggregate,
    StateBatchReplayItem,
    StateBatchReplayRequest,
    StateBatchReplayResult,
)
from ugh_quantamental.replay.models import (
    ProjectionReplayComparison,
    ProjectionReplayRequest,
    ProjectionReplayResult,
    StateReplayComparison,
    StateReplayRequest,
    StateReplayResult,
)

__all__ = [
    # baseline models
    "CreateRegressionBaselineRequest",
    "CompareRegressionBaselineRequest",
    "RegressionSuiteBaseline",
    "RegressionSuiteBaselineBundle",
    "RegressionSuiteCaseDelta",
    "RegressionBaselineComparison",
    "RegressionBaselineCompareResult",
    # single-run replay models
    "ProjectionReplayRequest",
    "StateReplayRequest",
    "ProjectionReplayComparison",
    "StateReplayComparison",
    "ProjectionReplayResult",
    "StateReplayResult",
    "BatchReplayStatus",
    "ProjectionBatchReplayRequest",
    "StateBatchReplayRequest",
    "ProjectionBatchReplayItem",
    "StateBatchReplayItem",
    "ProjectionBatchReplayAggregate",
    "StateBatchReplayAggregate",
    "ProjectionBatchReplayResult",
    "StateBatchReplayResult",
]
