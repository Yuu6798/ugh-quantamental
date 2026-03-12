"""Synchronous read-only batch replay runners for projection and state runs (v1).

These runners are read-only and diagnostic only.  They do not write run records,
flush, or commit the session.  The caller owns the session and transaction boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ugh_quantamental.query.readers import (
    list_projection_run_summaries,
    list_state_run_summaries,
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
from ugh_quantamental.replay.models import ProjectionReplayRequest, StateReplayRequest
from ugh_quantamental.replay.runners import replay_projection_run, replay_state_run

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _deduplicate(run_ids: list[str]) -> list[str]:
    """Return a deduplicated list preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for rid in run_ids:
        if rid not in seen:
            seen.add(rid)
            result.append(rid)
    return result


def replay_projection_batch(
    session: Session,
    request: ProjectionBatchReplayRequest,
) -> ProjectionBatchReplayResult:
    """Replay multiple persisted projection runs and return per-run items with aggregate.

    If ``run_ids`` are provided, replays in the provided order (deduplicating if
    ``deduplicate_run_ids=True``).  If ``query`` is provided, resolves run IDs via the
    summary reader (newest-first) and then replays each one.

    Per-run errors are isolated: a single failing run never aborts the entire batch.
    Does not write, flush, or commit the session.
    """
    if request.run_ids is not None:
        run_ids: list[str] = list(request.run_ids)
    else:
        summaries = list_projection_run_summaries(session, request.query)  # type: ignore[arg-type]
        run_ids = [s.run_id for s in summaries]

    if request.deduplicate_run_ids:
        run_ids = _deduplicate(run_ids)

    requested_count = len(run_ids)
    items: list[ProjectionBatchReplayItem] = []

    for run_id in run_ids:
        try:
            result = replay_projection_run(session, ProjectionReplayRequest(run_id=run_id))
            if result is None:
                items.append(
                    ProjectionBatchReplayItem(
                        run_id=run_id,
                        status=BatchReplayStatus.missing,
                        result=None,
                        error_message=None,
                    )
                )
            else:
                items.append(
                    ProjectionBatchReplayItem(
                        run_id=run_id,
                        status=BatchReplayStatus.ok,
                        result=result,
                        error_message=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            items.append(
                ProjectionBatchReplayItem(
                    run_id=run_id,
                    status=BatchReplayStatus.error,
                    result=None,
                    error_message=str(exc),
                )
            )

    ok_items = [i for i in items if i.status == BatchReplayStatus.ok]
    missing_count = sum(1 for i in items if i.status == BatchReplayStatus.missing)
    error_count = sum(1 for i in items if i.status == BatchReplayStatus.error)
    processed_count = len(ok_items) + error_count
    exact_match_count = sum(1 for i in ok_items if i.result.comparison.exact_match)  # type: ignore[union-attr]
    mismatch_count = sum(1 for i in ok_items if not i.result.comparison.exact_match)  # type: ignore[union-attr]

    max_point_estimate_diff = max(
        (i.result.comparison.point_estimate_diff for i in ok_items),  # type: ignore[union-attr]
        default=0.0,
    )
    max_confidence_diff = max(
        (i.result.comparison.confidence_diff for i in ok_items),  # type: ignore[union-attr]
        default=0.0,
    )

    aggregate = ProjectionBatchReplayAggregate(
        requested_count=requested_count,
        processed_count=processed_count,
        exact_match_count=exact_match_count,
        mismatch_count=mismatch_count,
        missing_count=missing_count,
        error_count=error_count,
        max_point_estimate_diff=max_point_estimate_diff,
        max_confidence_diff=max_confidence_diff,
    )

    return ProjectionBatchReplayResult(items=tuple(items), aggregate=aggregate)


def replay_state_batch(
    session: Session,
    request: StateBatchReplayRequest,
) -> StateBatchReplayResult:
    """Replay multiple persisted state runs and return per-run items with aggregate.

    If ``run_ids`` are provided, replays in the provided order (deduplicating if
    ``deduplicate_run_ids=True``).  If ``query`` is provided, resolves run IDs via the
    summary reader (newest-first) and then replays each one.

    Per-run errors are isolated: a single failing run never aborts the entire batch.
    Does not write, flush, or commit the session.
    """
    if request.run_ids is not None:
        run_ids = list(request.run_ids)
    else:
        summaries = list_state_run_summaries(session, request.query)  # type: ignore[arg-type]
        run_ids = [s.run_id for s in summaries]

    if request.deduplicate_run_ids:
        run_ids = _deduplicate(run_ids)

    requested_count = len(run_ids)
    items: list[StateBatchReplayItem] = []

    for run_id in run_ids:
        try:
            result = replay_state_run(session, StateReplayRequest(run_id=run_id))
            if result is None:
                items.append(
                    StateBatchReplayItem(
                        run_id=run_id,
                        status=BatchReplayStatus.missing,
                        result=None,
                        error_message=None,
                    )
                )
            else:
                items.append(
                    StateBatchReplayItem(
                        run_id=run_id,
                        status=BatchReplayStatus.ok,
                        result=result,
                        error_message=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            items.append(
                StateBatchReplayItem(
                    run_id=run_id,
                    status=BatchReplayStatus.error,
                    result=None,
                    error_message=str(exc),
                )
            )

    ok_items = [i for i in items if i.status == BatchReplayStatus.ok]
    missing_count = sum(1 for i in items if i.status == BatchReplayStatus.missing)
    error_count = sum(1 for i in items if i.status == BatchReplayStatus.error)
    processed_count = len(ok_items) + error_count
    exact_match_count = sum(1 for i in ok_items if i.result.comparison.exact_match)  # type: ignore[union-attr]
    mismatch_count = sum(1 for i in ok_items if not i.result.comparison.exact_match)  # type: ignore[union-attr]

    max_transition_confidence_diff = max(
        (i.result.comparison.transition_confidence_diff for i in ok_items),  # type: ignore[union-attr]
        default=0.0,
    )

    aggregate = StateBatchReplayAggregate(
        requested_count=requested_count,
        processed_count=processed_count,
        exact_match_count=exact_match_count,
        mismatch_count=mismatch_count,
        missing_count=missing_count,
        error_count=error_count,
        max_transition_confidence_diff=max_transition_confidence_diff,
    )

    return StateBatchReplayResult(items=tuple(items), aggregate=aggregate)
