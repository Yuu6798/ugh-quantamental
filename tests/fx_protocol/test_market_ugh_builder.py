"""Tests for market_ugh_builder.py — deterministic market-derived UGH request building."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.market_ugh_builder import (
    build_ugh_request_from_snapshot,
    compute_snapshot_statistics,
    derive_alignment_inputs,
    derive_question_features,
    derive_signal_features,
    derive_state_event_features,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

_JST = ZoneInfo("Asia/Tokyo")


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
    )


def _build_windows(
    n: int,
    base_close: float = 150.0,
    step: float = 0.1,
    range_width: float = 1.0,
) -> tuple[FxCompletedWindow, ...]:
    """Build *n* consecutive Mon→next-business-day windows.

    Parameters
    ----------
    n:
        Number of windows to build.
    base_close:
        Close price of the first window.
    step:
        Increment added to close price each window.
    range_width:
        Half-width of the high–low range around the close.
    """
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)  # Monday
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        close = base_close + count * step
        low = close - range_width
        high = close + range_width
        windows.append(
            FxCompletedWindow(
                window_start_jst=start,
                window_end_jst=end,
                open_price=close,  # open == close (flat per window)
                high_price=high,
                low_price=low,
                close_price=close,
            )
        )
        start = end
        count += 1
    return tuple(windows)


def _snapshot(
    n_windows: int = 20,
    current_spot: float = 150.0,
    base_close: float = 150.0,
    step: float = 0.1,
    range_width: float = 1.0,
) -> FxProtocolMarketSnapshot:
    wins = _build_windows(n_windows, base_close=base_close, step=step, range_width=range_width)
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=wins[-1].window_end_jst,
        current_spot=current_spot,
        completed_windows=wins,
        market_data_provenance=_provenance(),
    )


# ---------------------------------------------------------------------------
# Determinism: same snapshot → identical output
# ---------------------------------------------------------------------------


class TestBuildUghRequestDeterminism:
    """Same snapshot must always produce the exact same FullWorkflowRequest."""

    def test_build_ugh_request_from_snapshot_is_deterministic(self) -> None:
        snap = _snapshot(25, current_spot=152.0, step=0.15)
        req1 = build_ugh_request_from_snapshot(snap, snapshot_ref="det-test")
        req2 = build_ugh_request_from_snapshot(snap, snapshot_ref="det-test")
        assert req1 == req2

    def test_statistics_are_deterministic(self) -> None:
        snap = _snapshot(25, current_spot=152.0, step=0.15)
        s1 = compute_snapshot_statistics(snap)
        s2 = compute_snapshot_statistics(snap)
        assert s1 == s2

    def test_derived_features_are_deterministic(self) -> None:
        snap = _snapshot(25, current_spot=152.0, step=0.15)
        stats = compute_snapshot_statistics(snap)
        q1 = derive_question_features(stats)
        q2 = derive_question_features(stats)
        assert q1 == q2
        s1 = derive_signal_features(stats)
        s2 = derive_signal_features(stats)
        assert s1 == s2


# ---------------------------------------------------------------------------
# Sensitivity: different snapshots → different outputs
# ---------------------------------------------------------------------------


class TestBuildUghRequestSensitivity:
    """Materially different snapshots must produce different derived UGH inputs."""

    def test_build_ugh_request_from_snapshot_varies_with_snapshot(self) -> None:
        snap_up = _snapshot(25, current_spot=155.0, step=0.3)
        snap_down = _snapshot(25, current_spot=145.0, step=-0.3)
        req_up = build_ugh_request_from_snapshot(snap_up, snapshot_ref="ref")
        req_down = build_ugh_request_from_snapshot(snap_down, snapshot_ref="ref")
        # Projection features must differ.
        assert req_up.projection.question_features != req_down.projection.question_features
        assert req_up.projection.signal_features != req_down.projection.signal_features

    def test_different_spot_changes_fundamental_score(self) -> None:
        snap_high = _snapshot(20, current_spot=160.0, base_close=150.0, step=0.1)
        snap_low = _snapshot(20, current_spot=140.0, base_close=150.0, step=0.1)
        stats_high = compute_snapshot_statistics(snap_high)
        stats_low = compute_snapshot_statistics(snap_low)
        sig_high = derive_signal_features(stats_high)
        sig_low = derive_signal_features(stats_low)
        assert sig_high["fundamental_score"] > sig_low["fundamental_score"]

    def test_different_momentum_changes_direction(self) -> None:
        snap_up = _snapshot(25, current_spot=155.0, step=0.5)
        snap_down = _snapshot(25, current_spot=145.0, step=-0.5)
        stats_up = compute_snapshot_statistics(snap_up)
        stats_down = compute_snapshot_statistics(snap_down)
        q_up = derive_question_features(stats_up)
        q_down = derive_question_features(stats_down)
        assert q_up["question_direction"] == "positive"
        assert q_down["question_direction"] == "negative"

    def test_market_derived_alignment_inputs_are_not_placeholder_constants(self) -> None:
        """Alignment gaps must NOT all be the same constant (as the old placeholder had)."""
        snap = _snapshot(25, current_spot=155.0, step=0.4)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="ref")
        ai = req.projection.alignment_inputs
        gaps = [ai.d_qf, ai.d_qt, ai.d_qp, ai.d_ft, ai.d_fp, ai.d_tp]
        # Not all identical — at least 2 distinct values.
        assert len(set(gaps)) >= 2, f"All alignment gaps collapsed to one value: {gaps}"


# ---------------------------------------------------------------------------
# Feature bounds
# ---------------------------------------------------------------------------


class TestFeatureBounds:
    """All derived features must respect their declared field bounds."""

    @pytest.fixture()
    def stats(self) -> dict[str, float]:
        snap = _snapshot(25, current_spot=155.0, step=0.3, range_width=2.0)
        return compute_snapshot_statistics(snap)

    def test_question_features_bounded(self, stats: dict[str, float]) -> None:
        q = derive_question_features(stats)
        assert 0.0 <= q["q_strength"] <= 1.0
        assert 0.0 <= q["s_q"] <= 1.0
        assert 0.0 <= q["temporal_score"] <= 1.0
        assert q["question_direction"] in ("positive", "negative", "neutral")

    def test_signal_features_bounded(self, stats: dict[str, float]) -> None:
        s = derive_signal_features(stats)
        assert -1.0 <= s["fundamental_score"] <= 1.0
        assert -1.0 <= s["technical_score"] <= 1.0
        assert -1.0 <= s["price_implied_score"] <= 1.0
        assert 0.0 <= s["context_score"] <= 2.0
        assert 0.0 <= s["grv_lock"] <= 1.0
        assert 0.0 <= s["regime_fit"] <= 1.0
        assert 0.0 <= s["narrative_dispersion"] <= 1.0
        assert 0.0 <= s["evidence_confidence"] <= 1.0
        assert 0.0 <= s["fire_probability"] <= 1.0

    def test_alignment_inputs_bounded(self, stats: dict[str, float]) -> None:
        q = derive_question_features(stats)
        s = derive_signal_features(stats)
        from ugh_quantamental.engine.projection_models import QuestionDirectionSign

        direction = QuestionDirectionSign(q["question_direction"])
        a = derive_alignment_inputs(direction.sign, float(q["q_strength"]), s)
        for key in ("d_qf", "d_qt", "d_qp", "d_ft", "d_fp", "d_tp"):
            assert 0.0 <= a[key] <= 1.0, f"{key}={a[key]} out of bounds"

    def test_state_event_features_bounded(self, stats: dict[str, float]) -> None:
        ef = derive_state_event_features(stats)
        for key in (
            "catalyst_strength",
            "follow_through",
            "pricing_saturation",
            "disconfirmation_strength",
            "regime_shock",
            "observation_freshness",
        ):
            assert 0.0 <= ef[key] <= 1.0, f"{key}={ef[key]} out of bounds"


# ---------------------------------------------------------------------------
# Full request construction
# ---------------------------------------------------------------------------


class TestFullRequestConstruction:
    """The full builder must produce a valid FullWorkflowRequest."""

    def test_returns_valid_full_workflow_request(self) -> None:
        from ugh_quantamental.workflows.models import FullWorkflowRequest

        snap = _snapshot(25, current_spot=152.0, step=0.2)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="test-full")
        assert isinstance(req, FullWorkflowRequest)
        assert req.projection.projection_id == "test-full"
        assert req.projection.horizon_days == 1

    def test_ssv_snapshot_has_market_derived_tag(self) -> None:
        snap = _snapshot(25, current_spot=152.0, step=0.2)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="tag-test")
        assert "market_derived" in req.state.snapshot.x.tags

    def test_omega_evidence_lineage_source_type(self) -> None:
        snap = _snapshot(25, current_spot=152.0, step=0.2)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="lineage-test")
        lineage = req.state.omega.evidence_lineage
        assert len(lineage) == 1
        assert lineage[0].source_type == "fx_daily_protocol"
        assert lineage[0].source_id == "market-snapshot"

    def test_state_probabilities_sum_to_one(self) -> None:
        snap = _snapshot(25, current_spot=155.0, step=0.4, range_width=2.5)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="prob-test")
        probs = req.state.snapshot.phi.probabilities
        total = (
            probs.dormant
            + probs.setup
            + probs.fire
            + probs.expansion
            + probs.exhaustion
            + probs.failure
        )
        assert abs(total - 1.0) < 1e-5


# ---------------------------------------------------------------------------
# Integration: automation uses market-derived builder
# ---------------------------------------------------------------------------


class TestAutomationUsesMarketDerivedBuilder:
    """The automation module must call the market-derived builder, not the placeholder."""

    def test_daily_automation_uses_market_derived_ugh_request(self) -> None:
        """Verify that the automation import path references market_ugh_builder."""
        import inspect

        from ugh_quantamental.fx_protocol import automation

        source = inspect.getsource(automation.run_fx_daily_protocol_once)
        assert "build_ugh_request_from_snapshot" in source
        # The old placeholder should no longer be in the active forecast path.
        assert "_make_default_ugh_request" not in source


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_flat_market_produces_neutral_direction(self) -> None:
        """When all close prices are identical, direction should be neutral."""
        snap = _snapshot(20, current_spot=150.0, step=0.0, range_width=0.5)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="flat")
        from ugh_quantamental.engine.projection_models import QuestionDirectionSign

        assert req.projection.question_features.question_direction == QuestionDirectionSign.neutral

    def test_extreme_range_expansion_bounded(self) -> None:
        """Very wide ranges should not produce out-of-bounds features."""
        snap = _snapshot(25, current_spot=150.0, step=0.0, range_width=20.0)
        req = build_ugh_request_from_snapshot(snap, snapshot_ref="wide")
        sf = req.projection.signal_features
        assert 0.0 <= sf.context_score <= 2.0
        assert 0.0 <= sf.grv_lock <= 1.0
        assert 0.0 <= sf.fire_probability <= 1.0
