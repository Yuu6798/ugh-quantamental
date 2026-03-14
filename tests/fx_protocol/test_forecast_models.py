"""Tests for daily FX forecast workflow request and model contracts."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    QuestionDirectionSign,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.engine.state_models import StateEventFeatures
from ugh_quantamental.fx_protocol.forecast_models import (
    BaselineContext,
    DailyForecastWorkflowRequest,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance
from ugh_quantamental.workflows.models import (
    FullWorkflowRequest,
    FullWorkflowStateRequest,
    ProjectionWorkflowRequest,
)


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test_vendor",
        feed_name="test_feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 13, 0, 0, 0, tzinfo=timezone.utc),
    )


def _full_request() -> FullWorkflowRequest:
    return FullWorkflowRequest(
        projection=ProjectionWorkflowRequest(
            projection_id="Will USDJPY close higher?",
            horizon_days=1,
            question_features=QuestionFeatures(
                question_direction=QuestionDirectionSign.positive,
                q_strength=0.7,
                s_q=0.6,
                temporal_score=0.8,
            ),
            signal_features=SignalFeatures(
                fundamental_score=0.2,
                technical_score=0.3,
                price_implied_score=0.1,
                context_score=1.0,
                grv_lock=0.7,
                regime_fit=0.6,
                narrative_dispersion=0.3,
                evidence_confidence=0.8,
                fire_probability=0.4,
            ),
            alignment_inputs=AlignmentInputs(
                d_qf=0.1,
                d_qt=0.1,
                d_qp=0.1,
                d_ft=0.1,
                d_fp=0.1,
                d_tp=0.1,
            ),
        ),
        state=FullWorkflowStateRequest(
            snapshot={
                "snapshot_id": "snap-001",
                "q": {
                    "ledger": {
                        "as_of": "2026-03-13",
                        "coverage_ratio": 1.0,
                        "questions": [
                            {
                                "question_id": "q1",
                                "direction": "positive",
                                "score": 0.6,
                                "weight": 1.0,
                            }
                        ],
                    }
                },
                "f": {"factor_count": 3, "aggregate_signal": 0.2},
                "t": {"timestamp": "2026-03-13T00:00:00Z", "lookback_days": 30},
                "p": {
                    "implied_move_30d": 0.03,
                    "implied_volatility": 0.2,
                    "skew_25d": 0.01,
                },
                "phi": {
                    "dominant_state": "setup",
                    "probabilities": {
                        "dormant": 0.2,
                        "setup": 0.4,
                        "fire": 0.2,
                        "expansion": 0.1,
                        "exhaustion": 0.05,
                        "failure": 0.05,
                    },
                },
                "r": {
                    "market_regime": "neutral",
                    "macro_cycle_regime": "expansion",
                    "conviction": 0.5,
                },
                "x": {"tags": ["test"]},
            },
            omega={
                "omega_id": "omega-001",
                "market_svp": {
                    "as_of": "2026-03-13T00:00:00Z",
                    "regime": "neutral",
                    "phi": {
                        "dominant_state": "setup",
                        "probabilities": {
                            "dormant": 0.2,
                            "setup": 0.4,
                            "fire": 0.2,
                            "expansion": 0.1,
                            "exhaustion": 0.05,
                            "failure": 0.05,
                        },
                    },
                    "confidence": 0.8,
                },
                "question_ledger": {
                    "as_of": "2026-03-13",
                    "coverage_ratio": 1.0,
                    "questions": [
                        {
                            "question_id": "q1",
                            "direction": "positive",
                            "score": 0.6,
                            "weight": 1.0,
                        }
                    ],
                },
                "evidence_lineage": [
                    {
                        "source_id": "s1",
                        "observed_at": "2026-03-13T00:00:00Z",
                        "source_type": "internal",
                    }
                ],
                "block_confidence": {"q": 0.9, "f": 0.9, "t": 0.9, "p": 0.9, "r": 0.9, "x": 0.9},
                "block_observability": {"q": 0.9, "f": 0.9, "t": 0.9, "p": 0.9, "r": 0.9, "x": 0.9},
                "confidence": 0.9,
            },
            event_features=StateEventFeatures(
                catalyst_strength=0.6,
                follow_through=0.5,
                pricing_saturation=0.3,
                disconfirmation_strength=0.2,
                regime_shock=0.1,
                observation_freshness=0.8,
            ),
        ),
    )


def _baseline_context(**kwargs) -> BaselineContext:
    base = {
        "current_spot": 150.0,
        "previous_close_change_bp": 12.0,
        "trailing_mean_range_price": 1.2,
        "trailing_mean_abs_close_change_bp": 20.0,
        "sma5": 150.2,
        "sma20": 149.8,
        "warmup_window_count": 20,
    }
    base.update(kwargs)
    return BaselineContext(**base)


def _request(**kwargs) -> DailyForecastWorkflowRequest:
    base = {
        "pair": CurrencyPair.USDJPY,
        "as_of_jst": datetime(2026, 3, 13, 8, 0, 0),
        "market_data_provenance": _provenance(),
        "input_snapshot_ref": "snapshot/ref/001",
        "ugh_request": _full_request(),
        "baseline_context": _baseline_context(),
        "theory_version": "v1",
        "engine_version": "v1",
        "schema_version": "v1",
        "protocol_version": "v1",
    }
    base.update(kwargs)
    return DailyForecastWorkflowRequest(**base)


def test_request_rejects_non_business_day() -> None:
    with pytest.raises(ValidationError, match="as_of_jst must be a protocol business day"):
        _request(as_of_jst=datetime(2026, 3, 14, 8, 0, 0))


def test_request_rejects_wrong_as_of_hour() -> None:
    with pytest.raises(ValidationError, match="as_of_jst must be exactly 08:00 JST"):
        _request(as_of_jst=datetime(2026, 3, 13, 9, 0, 0))


def test_request_rejects_warmup_window_below_20() -> None:
    with pytest.raises(ValidationError, match="warmup_window_count must be >= 20"):
        _request(baseline_context=_baseline_context(warmup_window_count=19))
