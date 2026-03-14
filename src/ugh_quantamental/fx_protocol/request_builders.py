"""Deterministic request builders for the FX Daily Automation layer (v1).

Converts ``FxProtocolMarketSnapshot`` into typed workflow request objects.
All builders are pure functions with no I/O.
"""

from __future__ import annotations

from ugh_quantamental.fx_protocol.calendar import next_as_of_jst
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.forecast_models import (
    BaselineContext,
    DailyForecastWorkflowRequest,
)
from ugh_quantamental.fx_protocol.outcome_models import DailyOutcomeWorkflowRequest
from ugh_quantamental.workflows.models import FullWorkflowRequest

_MIN_WARMUP_WINDOWS: int = 20


def _close_change_bp(window: FxCompletedWindow) -> float:
    """Compute close change in basis points for a completed window."""
    return (window.close_price - window.open_price) / window.open_price * 10_000


def _range_price(window: FxCompletedWindow) -> float:
    """Compute high − low price range for a completed window."""
    return window.high_price - window.low_price


def build_baseline_context(snapshot: FxProtocolMarketSnapshot) -> BaselineContext:
    """Derive a ``BaselineContext`` from the market snapshot.

    Uses the last 20 completed windows for trailing statistics.

    Parameters
    ----------
    snapshot:
        Market snapshot with at least 20 completed windows ordered oldest→newest.

    Returns
    -------
    BaselineContext
        Fully populated baseline context for the forecast workflow.

    Raises
    ------
    ValueError
        If ``snapshot.completed_windows`` has fewer than 20 entries.
    """
    wins = snapshot.completed_windows
    if len(wins) < _MIN_WARMUP_WINDOWS:
        raise ValueError(
            f"Need at least {_MIN_WARMUP_WINDOWS} completed windows; "
            f"got {len(wins)}"
        )

    # Use the last 20 windows for all trailing statistics.
    trailing = wins[-_MIN_WARMUP_WINDOWS:]

    # Previous close change: most recent completed window.
    newest = trailing[-1]
    previous_close_change_bp = _close_change_bp(newest)

    # Trailing mean range price.
    trailing_mean_range_price = sum(_range_price(w) for w in trailing) / len(trailing)

    # Trailing mean absolute close change in bp.
    trailing_mean_abs_close_change_bp = (
        sum(abs(_close_change_bp(w)) for w in trailing) / len(trailing)
    )

    # SMA20: mean of close prices over the last 20 windows.
    sma20 = sum(w.close_price for w in trailing) / len(trailing)

    # SMA5: mean of close prices over the last 5 windows.
    last5 = wins[-5:]
    sma5 = sum(w.close_price for w in last5) / len(last5)

    return BaselineContext(
        current_spot=snapshot.current_spot,
        previous_close_change_bp=previous_close_change_bp,
        trailing_mean_range_price=trailing_mean_range_price,
        trailing_mean_abs_close_change_bp=trailing_mean_abs_close_change_bp,
        sma5=sma5,
        sma20=sma20,
        warmup_window_count=len(wins),
    )


def build_daily_forecast_request(
    snapshot: FxProtocolMarketSnapshot,
    *,
    ugh_request: FullWorkflowRequest,
    input_snapshot_ref: str,
    theory_version: str,
    engine_version: str,
    schema_version: str,
    protocol_version: str,
) -> DailyForecastWorkflowRequest:
    """Build a ``DailyForecastWorkflowRequest`` from a market snapshot.

    The ``ugh_request`` must be constructed by the caller and injected here.
    This function builds the deterministic, market-data-derived fields only.

    Parameters
    ----------
    snapshot:
        Market snapshot with at least 20 completed windows.
    ugh_request:
        Pre-built UGH engine workflow request (caller's responsibility).
    input_snapshot_ref:
        Opaque reference string identifying the UGH input snapshot.
    theory_version, engine_version, schema_version, protocol_version:
        Protocol versioning metadata.

    Returns
    -------
    DailyForecastWorkflowRequest
        Fully populated forecast workflow request.
    """
    baseline_context = build_baseline_context(snapshot)

    return DailyForecastWorkflowRequest(
        pair=snapshot.pair,
        as_of_jst=snapshot.as_of_jst,
        market_data_provenance=snapshot.market_data_provenance,
        input_snapshot_ref=input_snapshot_ref,
        ugh_request=ugh_request,
        baseline_context=baseline_context,
        theory_version=theory_version,
        engine_version=engine_version,
        schema_version=schema_version,
        protocol_version=protocol_version,
    )


def build_daily_outcome_request(
    snapshot: FxProtocolMarketSnapshot,
    *,
    schema_version: str,
    protocol_version: str,
) -> DailyOutcomeWorkflowRequest:
    """Build a ``DailyOutcomeWorkflowRequest`` from the most recent completed window.

    Uses the newest (last) entry in ``snapshot.completed_windows`` as the
    realized OHLC for the prior forecast window.

    Parameters
    ----------
    snapshot:
        Market snapshot with at least 1 completed window.
    schema_version:
        Schema version string.
    protocol_version:
        Protocol version string.

    Returns
    -------
    DailyOutcomeWorkflowRequest
        Fully populated outcome workflow request.

    Raises
    ------
    ValueError
        If ``snapshot.completed_windows`` is empty.
    """
    if not snapshot.completed_windows:
        raise ValueError("snapshot.completed_windows must not be empty")

    newest = snapshot.completed_windows[-1]

    # The window end is the canonical next business-day 08:00 JST.
    # We already have it in the FxCompletedWindow.
    return DailyOutcomeWorkflowRequest(
        pair=snapshot.pair,
        window_start_jst=newest.window_start_jst,
        window_end_jst=newest.window_end_jst,
        market_data_provenance=snapshot.market_data_provenance,
        realized_open=newest.open_price,
        realized_high=newest.high_price,
        realized_low=newest.low_price,
        realized_close=newest.close_price,
        event_tags=newest.event_tags,
        schema_version=schema_version,
        protocol_version=protocol_version,
    )


def previous_window_matches(snapshot: FxProtocolMarketSnapshot) -> bool:
    """Return True iff the newest completed window ends at or before ``as_of_jst``.

    Used by the automation layer to decide whether to run outcome/evaluation.
    The newest completed window must end at exactly the current ``as_of_jst``
    (i.e. the window_end_jst of the newest window equals as_of_jst), meaning
    this is the immediately-preceding protocol window.

    Parameters
    ----------
    snapshot:
        Market snapshot.

    Returns
    -------
    bool
        True if outcome evaluation should proceed.
    """
    if not snapshot.completed_windows:
        return False
    newest = snapshot.completed_windows[-1]
    # next_as_of_jst of the newest window's start must equal snapshot.as_of_jst
    expected_end = next_as_of_jst(newest.window_start_jst)
    return newest.window_end_jst == expected_end and newest.window_end_jst == snapshot.as_of_jst
