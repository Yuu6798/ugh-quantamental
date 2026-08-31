"""Deterministic request builders for the FX Daily Automation layer (v1).

Converts ``FxProtocolMarketSnapshot`` into typed workflow request objects.
All builders are pure functions with no I/O.
"""

from __future__ import annotations

from datetime import datetime

from ugh_quantamental.fx_protocol.calendar import next_as_of_jst, prev_as_of_jst
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.forecast_models import (
    BaselineContext,
    DailyForecastWorkflowRequest,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance
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


def build_outcome_request_for_window(
    window: FxCompletedWindow,
    *,
    pair: CurrencyPair,
    market_data_provenance: MarketDataProvenance,
    schema_version: str,
    protocol_version: str,
) -> DailyOutcomeWorkflowRequest:
    """Build a ``DailyOutcomeWorkflowRequest`` for an arbitrary completed window.

    Generalizes the window-selection logic of :func:`build_daily_outcome_request`
    (which is pinned to ``snapshot.completed_windows[-1]``, the immediately
    preceding window) to any window drawn from a snapshot's trailing history.
    Used by the outcome catch-up path (``automation.py`` Step 4b /
    :func:`catchup_window_candidates`) to recover older closed-but-unevaluated
    windows without touching the single-window semantics of
    :func:`build_daily_outcome_request`.

    Parameters
    ----------
    window:
        The completed window to build an outcome request for.
    pair:
        Currency pair.
    market_data_provenance:
        Source metadata for this outcome (typically ``snapshot.market_data_provenance``).
    schema_version, protocol_version:
        Protocol versioning metadata.

    Returns
    -------
    DailyOutcomeWorkflowRequest
        Fully populated outcome workflow request for *window*.
    """
    return DailyOutcomeWorkflowRequest(
        pair=pair,
        window_start_jst=window.window_start_jst,
        window_end_jst=window.window_end_jst,
        market_data_provenance=market_data_provenance,
        realized_open=window.open_price,
        realized_high=window.high_price,
        realized_low=window.low_price,
        realized_close=window.close_price,
        event_tags=window.event_tags,
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
    return build_outcome_request_for_window(
        newest,
        pair=snapshot.pair,
        market_data_provenance=snapshot.market_data_provenance,
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


def _business_day_lag(window_end_jst: datetime, as_of_jst: datetime, *, max_lag: int) -> int | None:
    """Return the protocol-business-day distance from *window_end_jst* to *as_of_jst*.

    Counts how many :func:`prev_as_of_jst` steps from *as_of_jst* land exactly on
    *window_end_jst*. A distance of ``0`` means *window_end_jst* IS *as_of_jst*
    (the immediately preceding window — handled separately by
    :func:`previous_window_matches`, not by catch-up).

    Parameters
    ----------
    window_end_jst:
        Window close time to measure.
    as_of_jst:
        Current run's canonical as-of time.
    max_lag:
        Upper bound on steps to walk before giving up. Bounds the loop so a
        timestamp that is not business-day-aligned with *as_of_jst* cannot spin
        indefinitely.

    Returns
    -------
    int | None
        The business-day distance, or ``None`` if *window_end_jst* is after
        *as_of_jst*, or is not reached within *max_lag* steps.
    """
    if window_end_jst > as_of_jst:
        return None
    cursor = as_of_jst
    lag = 0
    while cursor > window_end_jst:
        if lag >= max_lag:
            return None
        cursor = prev_as_of_jst(cursor)
        lag += 1
    if cursor != window_end_jst:
        # The walk overshot window_end_jst without ever landing exactly on it
        # (a misaligned / non-business-day timestamp) — reject rather than
        # report a lag for a window that isn't actually reachable via
        # prev_as_of_jst steps from as_of_jst.
        return None
    return lag


def catchup_window_candidates(
    snapshot: FxProtocolMarketSnapshot,
    *,
    max_business_days: int,
) -> tuple[FxCompletedWindow, ...]:
    """Return closed windows eligible for outcome catch-up, oldest first.

    A window is a catch-up *candidate* iff it is strictly older than the
    immediately-preceding window handled by :func:`previous_window_matches`
    (business-day distance >= 1 from ``snapshot.as_of_jst``) and its distance
    is at most *max_business_days*. This function only bounds the *set* of
    windows catch-up may draw from — callers (``automation.py`` Step 4b) still
    need to check forecast-batch completeness and evaluation idempotency
    before acting on a candidate, and must skip (never raise) on a window that
    fails either check.

    Parameters
    ----------
    snapshot:
        Market snapshot (``completed_windows`` ordered oldest→newest).
    max_business_days:
        Maximum lookback distance in protocol business days
        (``FxDailyAutomationConfig.outcome_catchup_days``). ``0`` disables
        catch-up entirely (returns ``()``).

    Returns
    -------
    tuple[FxCompletedWindow, ...]
        Eligible windows ordered oldest first (largest distance first).
    """
    if max_business_days <= 0:
        return ()

    as_of_jst = snapshot.as_of_jst
    dated: list[tuple[int, FxCompletedWindow]] = []
    for window in snapshot.completed_windows:
        lag = _business_day_lag(window.window_end_jst, as_of_jst, max_lag=max_business_days)
        if lag is not None and lag >= 1:
            dated.append((lag, window))
    dated.sort(key=lambda item: item[0], reverse=True)
    return tuple(window for _, window in dated)
