"""Persistence round-trip tests for FxOutcomeEvaluationRepository."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_UTC = timezone.utc


def _provenance():
    from ugh_quantamental.fx_protocol.models import MarketDataProvenance

    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 16, 0, 0, 0, tzinfo=_UTC),
    )


def _make_outcome():
    from ugh_quantamental.fx_protocol.models import (
        CurrencyPair,
        ForecastDirection,
        OutcomeRecord,
    )

    return OutcomeRecord(
        outcome_id="oc_test_001",
        pair=CurrencyPair.USDJPY,
        window_start_jst=datetime(2026, 3, 13, 8, 0, 0),
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        market_data_provenance=_provenance(),
        realized_open=150.0,
        realized_high=151.0,
        realized_low=149.5,
        realized_close=150.8,
        realized_direction=ForecastDirection.up,
        realized_close_change_bp=(150.8 - 150.0) / 150.0 * 10_000,
        realized_range_price=1.5,
        event_happened=False,
        event_tags=(),
        schema_version="v1",
        protocol_version="v1",
    )


def _make_eval(i: int, outcome_id: str, strategy_kind=None):
    from ugh_quantamental.fx_protocol.models import (
        CurrencyPair,
        EvaluationRecord,
        StrategyKind,
    )

    sk = strategy_kind or StrategyKind.baseline_random_walk
    kwargs: dict = dict(
        evaluation_id=f"ev_fc_{i}_{outcome_id}_v1_abcd1234abcd1234",
        forecast_id=f"fc_{i}",
        outcome_id=outcome_id,
        pair=CurrencyPair.USDJPY,
        strategy_kind=sk,
        direction_hit=True,
        close_error_bp=0.0,
        magnitude_error_bp=0.0,
        disconfirmers_hit=(),
        disconfirmer_explained=False,
        evaluated_at_utc=datetime(2026, 3, 16, 9, 0, 0, tzinfo=_UTC),
        theory_version="v1",
        engine_version="v1",
        schema_version="v1",
        protocol_version="v1",
    )
    if sk == StrategyKind.ugh:
        kwargs["range_hit"] = True
    return EvaluationRecord(**kwargs)


@pytest.fixture()
def db_session():
    if not HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine()
    create_all_tables(engine)
    session = create_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_outcome_round_trip(db_session) -> None:
    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    outcome = _make_outcome()
    FxOutcomeEvaluationRepository.save_fx_outcome_record(db_session, outcome=outcome)

    loaded = FxOutcomeEvaluationRepository.load_fx_outcome_record(db_session, outcome.outcome_id)
    assert loaded is not None
    assert loaded.outcome_id == outcome.outcome_id
    assert loaded.pair == outcome.pair
    assert loaded.protocol_version == outcome.protocol_version


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_outcome_load_missing_returns_none(db_session) -> None:
    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    result = FxOutcomeEvaluationRepository.load_fx_outcome_record(db_session, "nonexistent")
    assert result is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_evaluation_batch_round_trip(db_session) -> None:
    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    outcome = _make_outcome()
    FxOutcomeEvaluationRepository.save_fx_outcome_record(db_session, outcome=outcome)

    evals = tuple(_make_eval(i, outcome.outcome_id) for i in range(4))
    FxOutcomeEvaluationRepository.save_fx_evaluation_batch(
        db_session, outcome_id=outcome.outcome_id, evaluations=evals
    )

    loaded = FxOutcomeEvaluationRepository.load_fx_evaluation_batch(db_session, outcome.outcome_id)
    assert loaded is not None
    assert len(loaded) == 4
    loaded_ids = {ev.evaluation_id for ev in loaded}
    expected_ids = {ev.evaluation_id for ev in evals}
    assert loaded_ids == expected_ids


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_evaluation_batch_load_missing_returns_none(db_session) -> None:
    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    result = FxOutcomeEvaluationRepository.load_fx_evaluation_batch(db_session, "no_such_outcome")
    assert result is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_save_evaluation_without_outcome_raises(db_session) -> None:
    """save_fx_evaluation_batch must fail fast if outcome is not persisted."""
    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    evals = tuple(_make_eval(i, "missing_outcome") for i in range(4))
    with pytest.raises(ValueError, match="not found"):
        FxOutcomeEvaluationRepository.save_fx_evaluation_batch(
            db_session, outcome_id="missing_outcome", evaluations=evals
        )


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_no_duplicate_outcome_id(db_session) -> None:
    """SQLAlchemy PK constraint prevents duplicate outcome_ids at the DB level."""
    from sqlalchemy.exc import IntegrityError

    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    outcome = _make_outcome()
    FxOutcomeEvaluationRepository.save_fx_outcome_record(db_session, outcome=outcome)
    db_session.flush()

    with pytest.raises(IntegrityError):
        FxOutcomeEvaluationRepository.save_fx_outcome_record(db_session, outcome=outcome)
        db_session.flush()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_no_duplicate_evaluation_id(db_session) -> None:
    """SQLAlchemy PK constraint prevents duplicate evaluation_ids at the DB level."""
    from sqlalchemy.exc import IntegrityError

    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    outcome = _make_outcome()
    FxOutcomeEvaluationRepository.save_fx_outcome_record(db_session, outcome=outcome)

    evals = tuple(_make_eval(i, outcome.outcome_id) for i in range(4))
    FxOutcomeEvaluationRepository.save_fx_evaluation_batch(
        db_session, outcome_id=outcome.outcome_id, evaluations=evals
    )
    db_session.flush()

    with pytest.raises(IntegrityError):
        FxOutcomeEvaluationRepository.save_fx_evaluation_batch(
            db_session, outcome_id=outcome.outcome_id, evaluations=evals
        )
        db_session.flush()


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_outcome_payload_json_fields_preserved(db_session) -> None:
    """Full OutcomeRecord fields are faithfully round-tripped through payload_json."""
    from ugh_quantamental.fx_protocol.models import EventTag
    from ugh_quantamental.fx_protocol.models import (
        CurrencyPair,
        ForecastDirection,
        OutcomeRecord,
    )
    from ugh_quantamental.persistence.repositories import FxOutcomeEvaluationRepository

    bp = (150.8 - 150.0) / 150.0 * 10_000
    outcome = OutcomeRecord(
        outcome_id="oc_test_002",
        pair=CurrencyPair.USDJPY,
        window_start_jst=datetime(2026, 3, 13, 8, 0, 0),
        window_end_jst=datetime(2026, 3, 16, 8, 0, 0),
        market_data_provenance=_provenance(),
        realized_open=150.0,
        realized_high=151.0,
        realized_low=149.5,
        realized_close=150.8,
        realized_direction=ForecastDirection.up,
        realized_close_change_bp=bp,
        realized_range_price=1.5,
        event_happened=True,
        event_tags=(EventTag.fomc,),
        schema_version="v1",
        protocol_version="v1",
    )
    FxOutcomeEvaluationRepository.save_fx_outcome_record(db_session, outcome=outcome)
    loaded = FxOutcomeEvaluationRepository.load_fx_outcome_record(db_session, outcome.outcome_id)
    assert loaded is not None
    assert loaded.event_happened is True
    assert EventTag.fomc in loaded.event_tags
    assert abs(loaded.realized_close_change_bp - bp) < 1e-6
