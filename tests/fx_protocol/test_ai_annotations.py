"""Tests for ai_annotations.py — AI annotation execution boundary."""

from __future__ import annotations

from datetime import datetime, timezone

from ugh_quantamental.fx_protocol.ai_annotations import (
    ai_batch_to_lookup,
    make_deterministic_adapter,
    run_ai_annotation_pass,
)
from ugh_quantamental.fx_protocol.annotation_models import (
    ExternalEvidenceBundle,
    ExternalEvidenceItem,
)

_UTC = timezone.utc
_NOW = datetime(2026, 3, 20, 6, 0, 0, tzinfo=_UTC)


def _make_obs(
    *,
    forecast_id: str = "fc-001",
    as_of_jst: str = "2026-03-18T08:00:00+09:00",
    direction_hit: str = "True",
    close_error_bp: str = "15.0",
    realized_close_change_bp: str = "20.0",
    strategy_kind: str = "ugh",
    realized_open: str = "150.00",
    realized_high: str = "150.30",
    realized_low: str = "149.70",
    realized_close: str = "150.30",
) -> dict[str, str]:
    return {
        "forecast_id": forecast_id,
        "forecast_batch_id": "batch-001",
        "as_of_jst": as_of_jst,
        "pair": "USDJPY",
        "strategy_kind": strategy_kind,
        "direction_hit": direction_hit,
        "close_error_bp": close_error_bp,
        "realized_close_change_bp": realized_close_change_bp,
        # OHLC drives the (market-derived) regime / volatility labels.
        # Default: ~40bp intraday range, single positive close change.
        "realized_open": realized_open,
        "realized_high": realized_high,
        "realized_low": realized_low,
        "realized_close": realized_close,
        "effective_event_tags": "fomc",
    }


class TestDeterministicAdapter:
    def test_produces_records(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        obs = [_make_obs()]
        batch = adapter(obs, None)
        assert len(batch.records) == 1
        rec = batch.records[0]
        # OHLC-derived: positive close change -> trending; ~40bp range -> low.
        assert rec.regime_label == "trending"
        assert rec.volatility_label == "low"
        assert rec.intervention_risk == "low"  # change=20 < 50
        assert "fomc" in rec.event_tags

    def test_direction_miss_sets_failure_reason(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        obs = [_make_obs(direction_hit="False", strategy_kind="ugh")]
        batch = adapter(obs, None)
        assert batch.records[0].failure_reason == "direction_miss"

    def test_non_ugh_no_failure_reason(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        obs = [_make_obs(direction_hit="False", strategy_kind="baseline_random_walk")]
        batch = adapter(obs, None)
        assert batch.records[0].failure_reason is None

    def test_evidence_refs_populated(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        evidence = ExternalEvidenceBundle(
            bundle_id="eb1", created_at_utc=_NOW,
            items=(
                ExternalEvidenceItem(
                    source_id="src-a", source_kind="news",
                    title="A", text="a", content_hash="h1",
                ),
            ),
        )
        batch = adapter([_make_obs()], evidence)
        assert "src-a" in batch.records[0].evidence_refs

    def test_deterministic_output(self) -> None:
        """Same inputs produce identical outputs."""
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        obs = [_make_obs(), _make_obs(forecast_id="fc-002")]
        b1 = adapter(obs, None)
        b2 = adapter(obs, None)
        assert b1.records == b2.records

    def test_high_volatility_label(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        # ~100bp intraday range (>= 90bp absolute threshold) -> high.
        obs = [_make_obs(realized_high="151.00", realized_low="149.50")]
        batch = adapter(obs, None)
        assert batch.records[0].volatility_label == "high"

    def test_labels_ignore_performance_fields(self) -> None:
        """regime / volatility must NOT depend on direction_hit / close_error_bp.

        Holding OHLC fixed, flipping the performance fields must not change the
        market-derived labels (guards against the circular-label leakage that
        FX-ANNOT-LIVE removes).
        """
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        hit = adapter([_make_obs(direction_hit="True", close_error_bp="5.0")], None)
        miss = adapter([_make_obs(direction_hit="False", close_error_bp="95.0")], None)
        assert hit.records[0].regime_label == miss.records[0].regime_label
        assert hit.records[0].volatility_label == miss.records[0].volatility_label

    def test_medium_intervention_risk(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        obs = [_make_obs(realized_close_change_bp="80.0")]
        batch = adapter(obs, None)
        assert batch.records[0].intervention_risk == "medium"


class TestAiBatchToLookup:
    def test_lookup_keys(self) -> None:
        adapter = make_deterministic_adapter(generated_at_utc=_NOW)
        batch = adapter([_make_obs()], None)
        lookup = ai_batch_to_lookup(batch)
        assert "fc-001" in lookup
        row = lookup["fc-001"]
        assert row["ai_regime_label"] == "trending"  # positive close change
        assert row["ai_annotation_status"] == "generated"
        assert row["ai_annotation_model_version"] == "deterministic-v1"


class TestRunAiAnnotationPass:
    def test_default_adapter(self) -> None:
        batch = run_ai_annotation_pass(
            [_make_obs()], generated_at_utc=_NOW,
        )
        assert batch is not None
        assert len(batch.records) == 1

    def test_custom_adapter(self) -> None:
        adapter = make_deterministic_adapter(
            model_version="custom-v2",
            generated_at_utc=_NOW,
        )
        batch = run_ai_annotation_pass([_make_obs()], adapter=adapter)
        assert batch is not None
        assert batch.model_version == "custom-v2"

    def test_failing_adapter_returns_none(self) -> None:
        def _bad_adapter(obs: list, evidence: object) -> None:
            raise RuntimeError("boom")

        batch = run_ai_annotation_pass([_make_obs()], adapter=_bad_adapter)  # type: ignore[arg-type]
        assert batch is None
