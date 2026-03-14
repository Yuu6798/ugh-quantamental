"""Deterministic daily FX outcome recording and per-forecast evaluation (Phase 2 Milestone 15)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ugh_quantamental.fx_protocol.ids import (
    make_evaluation_id,
    make_forecast_batch_id,
    make_outcome_id,
)
from ugh_quantamental.fx_protocol.models import (
    DisconfirmerRule,
    EvaluationRecord,
    ForecastDirection,
    ForecastRecord,
    OutcomeRecord,
    StrategyKind,
)
from ugh_quantamental.fx_protocol.outcome_models import (
    DailyOutcomeWorkflowRequest,
    PersistedOutcomeEvaluationBatch,
)
from ugh_quantamental.persistence.repositories import FxForecastRepository, FxOutcomeEvaluationRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_CLOSE_CHANGE_BP_OPERATORS: frozenset[str] = frozenset({"gt", "gte", "lt", "lte", "eq", "ne"})
_STATE_PROXY_OPERATORS: frozenset[str] = frozenset({"eq", "ne"})
_EVENT_TAG_OPERATORS: frozenset[str] = frozenset({"check"})
_RANGE_BREAK_OPERATORS: frozenset[str] = frozenset({"check"})
_RANGE_BREAK_THRESHOLDS: frozenset[str] = frozenset(
    {"below_expected_low", "above_expected_high", "outside_expected_range"}
)


def _direction_from_prices(open_price: float, close_price: float) -> ForecastDirection:
    """Derive realized direction from open and close prices."""
    if close_price > open_price:
        return ForecastDirection.up
    if close_price < open_price:
        return ForecastDirection.down
    return ForecastDirection.flat


def build_outcome_record(request: DailyOutcomeWorkflowRequest) -> OutcomeRecord:
    """Construct a canonical ``OutcomeRecord`` from a ``DailyOutcomeWorkflowRequest``.

    Derives ``realized_direction``, ``realized_close_change_bp``, and ``realized_range_price``
    from the OHLC prices, then delegates all consistency checks to ``OutcomeRecord``'s own
    model validators.
    """
    outcome_id = make_outcome_id(
        request.pair,
        request.window_start_jst,
        request.window_end_jst,
        request.schema_version,
    )
    realized_direction = _direction_from_prices(request.realized_open, request.realized_close)
    realized_close_change_bp = (
        (request.realized_close - request.realized_open) / request.realized_open * 10_000
    )
    realized_range_price = request.realized_high - request.realized_low
    event_happened = len(request.event_tags) > 0

    return OutcomeRecord(
        outcome_id=outcome_id,
        pair=request.pair,
        window_start_jst=request.window_start_jst,
        window_end_jst=request.window_end_jst,
        market_data_provenance=request.market_data_provenance,
        realized_open=request.realized_open,
        realized_high=request.realized_high,
        realized_low=request.realized_low,
        realized_close=request.realized_close,
        realized_direction=realized_direction,
        realized_close_change_bp=realized_close_change_bp,
        realized_range_price=realized_range_price,
        event_happened=event_happened,
        event_tags=request.event_tags,
        schema_version=request.schema_version,
        protocol_version=request.protocol_version,
    )


def _evaluate_disconfirmer(
    rule: DisconfirmerRule,
    outcome: OutcomeRecord,
    realized_state_proxy: str | None,
    forecast: ForecastRecord,
) -> bool:
    """Return ``True`` iff *rule* fires for the given outcome and state proxy.

    Raises ``ValueError`` for unsupported ``audit_kind`` / ``operator`` / ``threshold_value``
    combinations.  Rules are never silently skipped.
    """
    if rule.audit_kind == "event_tag":
        if rule.operator not in _EVENT_TAG_OPERATORS:
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: unsupported operator "
                f"{rule.operator!r} for audit_kind='event_tag'; "
                f"supported: {sorted(_EVENT_TAG_OPERATORS)}"
            )
        if not isinstance(rule.threshold_value, str):
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: audit_kind='event_tag' requires "
                f"a string threshold_value, got {type(rule.threshold_value).__name__!r}"
            )
        return rule.threshold_value in {tag.value for tag in outcome.event_tags}

    if rule.audit_kind == "close_change_bp":
        if rule.operator not in _CLOSE_CHANGE_BP_OPERATORS:
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: unsupported operator "
                f"{rule.operator!r} for audit_kind='close_change_bp'; "
                f"supported: {sorted(_CLOSE_CHANGE_BP_OPERATORS)}"
            )
        if not isinstance(rule.threshold_value, (int, float)):
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: audit_kind='close_change_bp' requires "
                f"a numeric threshold_value, got {type(rule.threshold_value).__name__!r}"
            )
        actual = outcome.realized_close_change_bp
        threshold = float(rule.threshold_value)
        if rule.operator == "gt":
            return actual > threshold
        if rule.operator == "gte":
            return actual >= threshold
        if rule.operator == "lt":
            return actual < threshold
        if rule.operator == "lte":
            return actual <= threshold
        if rule.operator == "eq":
            return actual == threshold
        if rule.operator == "ne":
            return actual != threshold

    if rule.audit_kind == "state_proxy":
        if rule.operator not in _STATE_PROXY_OPERATORS:
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: unsupported operator "
                f"{rule.operator!r} for audit_kind='state_proxy'; "
                f"supported: {sorted(_STATE_PROXY_OPERATORS)}"
            )
        if not isinstance(rule.threshold_value, str):
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: audit_kind='state_proxy' requires "
                f"a string threshold_value, got {type(rule.threshold_value).__name__!r}"
            )
        if realized_state_proxy is None:
            return False
        if rule.operator == "eq":
            return realized_state_proxy == rule.threshold_value
        if rule.operator == "ne":
            return realized_state_proxy != rule.threshold_value

    if rule.audit_kind == "range_break":
        if rule.operator not in _RANGE_BREAK_OPERATORS:
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: unsupported operator "
                f"{rule.operator!r} for audit_kind='range_break'; "
                f"supported: {sorted(_RANGE_BREAK_OPERATORS)}"
            )
        if forecast.expected_range is None:
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: audit_kind='range_break' requires "
                "forecast.expected_range to be non-None"
            )
        if rule.threshold_value not in _RANGE_BREAK_THRESHOLDS:
            raise ValueError(
                f"DisconfirmerRule {rule.rule_id!r}: unsupported threshold_value "
                f"{rule.threshold_value!r} for audit_kind='range_break'; "
                f"supported: {sorted(_RANGE_BREAK_THRESHOLDS)}"
            )
        close = outcome.realized_close
        low = forecast.expected_range.low_price
        high = forecast.expected_range.high_price
        if rule.threshold_value == "below_expected_low":
            return close < low
        if rule.threshold_value == "above_expected_high":
            return close > high
        if rule.threshold_value == "outside_expected_range":
            return close < low or close > high

    raise ValueError(
        f"DisconfirmerRule {rule.rule_id!r}: unsupported audit_kind {rule.audit_kind!r}"
    )


def compute_disconfirmers_hit(
    forecast: ForecastRecord,
    outcome: OutcomeRecord,
    realized_state_proxy: str | None,
) -> tuple[str, ...]:
    """Return the tuple of ``rule_id`` values for every disconfirmer rule that fired.

    Evaluates each ``DisconfirmerRule`` in ``forecast.disconfirmers`` deterministically.
    Raises ``ValueError`` on unsupported rule configurations.
    """
    return tuple(
        rule.rule_id
        for rule in forecast.disconfirmers
        if _evaluate_disconfirmer(rule, outcome, realized_state_proxy, forecast)
    )


def build_evaluation_record(
    forecast: ForecastRecord,
    outcome: OutcomeRecord,
    realized_state_proxy: str | None,
    evaluated_at_utc: datetime,
) -> EvaluationRecord:
    """Generate one ``EvaluationRecord`` joining *forecast* with *outcome*.

    All per-forecast diagnostic metrics are computed deterministically.
    State-proxy fields are ``None`` for baseline strategies.
    ``range_hit`` is ``None`` for baseline strategies and always set for UGH.
    """
    is_ugh = forecast.strategy_kind == StrategyKind.ugh

    direction_hit = forecast.forecast_direction == outcome.realized_direction

    range_hit: bool | None
    if is_ugh:
        if forecast.expected_range is None:
            raise ValueError(
                f"UGH forecast {forecast.forecast_id!r} missing expected_range; "
                "cannot compute range_hit"
            )
        range_hit = (
            forecast.expected_range.low_price
            <= outcome.realized_close
            <= forecast.expected_range.high_price
        )
    else:
        range_hit = None

    close_error_bp = abs(forecast.expected_close_change_bp - outcome.realized_close_change_bp)
    magnitude_error_bp = abs(
        abs(forecast.expected_close_change_bp) - abs(outcome.realized_close_change_bp)
    )

    state_proxy_hit: bool | None = None
    actual_state_change: bool | None = None
    mismatch_change_bp: float | None = None
    realized_state_proxy_out: str | None = None

    if is_ugh:
        realized_state_proxy_out = realized_state_proxy
        if forecast.dominant_state is not None and realized_state_proxy is not None:
            state_proxy_hit = forecast.dominant_state.value == realized_state_proxy
            actual_state_change = forecast.dominant_state.value != realized_state_proxy
        mismatch_change_bp = outcome.realized_close_change_bp - forecast.expected_close_change_bp

    disconfirmers_hit = compute_disconfirmers_hit(forecast, outcome, realized_state_proxy)
    disconfirmer_explained = (not direction_hit) and bool(disconfirmers_hit)

    evaluation_id = make_evaluation_id(
        forecast.forecast_id, outcome.outcome_id, forecast.schema_version
    )

    return EvaluationRecord(
        evaluation_id=evaluation_id,
        forecast_id=forecast.forecast_id,
        outcome_id=outcome.outcome_id,
        pair=forecast.pair,
        strategy_kind=forecast.strategy_kind,
        direction_hit=direction_hit,
        range_hit=range_hit,
        close_error_bp=close_error_bp,
        magnitude_error_bp=magnitude_error_bp,
        state_proxy_hit=state_proxy_hit,
        mismatch_change_bp=mismatch_change_bp,
        realized_state_proxy=realized_state_proxy_out,
        actual_state_change=actual_state_change,
        disconfirmers_hit=disconfirmers_hit,
        disconfirmer_explained=disconfirmer_explained,
        evaluated_at_utc=evaluated_at_utc,
        theory_version=forecast.theory_version,
        engine_version=forecast.engine_version,
        schema_version=forecast.schema_version,
        protocol_version=forecast.protocol_version,
    )


def run_daily_outcome_evaluation_workflow(
    session: "Session",
    request: DailyOutcomeWorkflowRequest,
) -> PersistedOutcomeEvaluationBatch:
    """Record one canonical outcome and generate per-forecast evaluations.

    Steps:
    1. Build the canonical ``OutcomeRecord``.
    2. Check idempotency — if already persisted, reload and continue.
    3. Load the matching forecast batch; fail fast if missing or incomplete.
    4. Try to load the next-day UGH batch for realized state proxy (read-only).
    5. Generate one ``EvaluationRecord`` per forecast.
    6. Check evaluation idempotency; fail fast on partial batch.
    7. Persist outcome + evaluations (flush only, caller owns transaction).
    """
    evaluated_at_utc = request.evaluated_at_utc or datetime.now(timezone.utc)

    # --- Step 1: build canonical outcome ---
    outcome = build_outcome_record(request)

    # --- Step 2: idempotency check for outcome ---
    existing_outcome = FxOutcomeEvaluationRepository.load_fx_outcome_record(
        session, outcome.outcome_id
    )
    if existing_outcome is None:
        FxOutcomeEvaluationRepository.save_fx_outcome_record(session, outcome=outcome)
        persisted_outcome = outcome
    else:
        persisted_outcome = existing_outcome

    # --- Step 3: load matching forecast batch ---
    forecast_batch_id = make_forecast_batch_id(
        request.pair, request.window_start_jst, request.protocol_version
    )
    batch = FxForecastRepository.load_fx_forecast_batch(session, forecast_batch_id)
    if batch is None:
        raise ValueError(
            f"No forecast batch found for {forecast_batch_id!r}. "
            "Run run_daily_forecast_workflow for this window first."
        )
    if len(batch.forecasts) != 4:
        raise ValueError(
            f"Forecast batch {forecast_batch_id!r} is incomplete: "
            f"expected 4 forecasts, found {len(batch.forecasts)}."
        )

    # --- Step 4: try next-day batch for realized state proxy (read-only) ---
    next_batch_id = make_forecast_batch_id(
        request.pair, request.window_end_jst, request.protocol_version
    )
    next_batch = FxForecastRepository.load_fx_forecast_batch(session, next_batch_id)
    realized_state_proxy: str | None = None
    if next_batch is not None:
        ugh_next = next(
            (f for f in next_batch.forecasts if f.strategy_kind == StrategyKind.ugh),
            None,
        )
        if ugh_next is not None and ugh_next.dominant_state is not None:
            realized_state_proxy = ugh_next.dominant_state.value

    # --- Step 5: idempotency check for evaluations ---
    existing_evals = FxOutcomeEvaluationRepository.load_fx_evaluation_batch(
        session, persisted_outcome.outcome_id
    )
    if existing_evals is not None:
        count = len(existing_evals)
        if count == 4:
            return PersistedOutcomeEvaluationBatch(
                outcome=persisted_outcome,
                evaluations=existing_evals,
            )
        raise ValueError(
            f"Partial evaluation batch found for outcome {persisted_outcome.outcome_id!r}: "
            f"expected 4 evaluations, found {count}. "
            "Cannot merge old and new evaluation records."
        )

    # --- Step 6: generate evaluations ---
    evaluations = tuple(
        build_evaluation_record(forecast, persisted_outcome, realized_state_proxy, evaluated_at_utc)
        for forecast in batch.forecasts
    )

    # --- Step 7: persist evaluations ---
    FxOutcomeEvaluationRepository.save_fx_evaluation_batch(
        session,
        outcome_id=persisted_outcome.outcome_id,
        evaluations=evaluations,
    )

    return PersistedOutcomeEvaluationBatch(
        outcome=persisted_outcome,
        evaluations=evaluations,
    )
