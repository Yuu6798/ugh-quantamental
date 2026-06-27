"""Tests for monthly review v1 — pure aggregation and review-flag layer."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.monthly_review import (
    build_recommendation_summary,
    compute_annotation_coverage_summary,
    compute_monthly_baseline_comparisons,
    compute_monthly_event_tag_metrics,
    compute_monthly_intervention_metrics,
    compute_monthly_regime_metrics,
    compute_monthly_slice_metrics,
    compute_monthly_state_metrics,
    compute_monthly_strategy_metrics,
    compute_monthly_volatility_metrics,
    compute_provider_health_summary,
    compute_review_flags,
    run_monthly_review,
    select_representative_cases,
)

_JST = ZoneInfo("Asia/Tokyo")
_REVIEW_DATE = datetime(2026, 4, 1, 8, 0, 0, tzinfo=_JST)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_obs(
    *,
    as_of_jst: str = "2026-03-18T08:00:00+09:00",
    forecast_batch_id: str = "batch_001",
    strategy_kind: str = "ugh",
    direction_hit: str = "True",
    range_hit: str = "True",
    state_proxy_hit: str = "True",
    close_error_bp: str = "15.0",
    magnitude_error_bp: str = "10.0",
    regime_label: str = "trending",
    volatility_label: str = "normal",
    intervention_risk: str = "low",
    event_tags: str = "fomc",
    annotation_status: str = "confirmed",
    dominant_state: str = "fire",
    forecast_direction: str = "up",
    realized_direction: str = "up",
    expected_close_change_bp: str = "20.0",
    realized_close_change_bp: str = "18.0",
) -> dict[str, str]:
    return {
        "as_of_jst": as_of_jst,
        "forecast_batch_id": forecast_batch_id,
        "strategy_kind": strategy_kind,
        "direction_hit": direction_hit,
        "range_hit": range_hit,
        "state_proxy_hit": state_proxy_hit,
        "close_error_bp": close_error_bp,
        "magnitude_error_bp": magnitude_error_bp,
        "regime_label": regime_label,
        "volatility_label": volatility_label,
        "intervention_risk": intervention_risk,
        "event_tags": event_tags,
        "annotation_status": annotation_status,
        "dominant_state": dominant_state,
        "forecast_direction": forecast_direction,
        "realized_direction": realized_direction,
        "expected_close_change_bp": expected_close_change_bp,
        "realized_close_change_bp": realized_close_change_bp,
    }


_UGH_V2_VARIANTS = (
    "ugh_v2_alpha",
    "ugh_v2_beta",
    "ugh_v2_gamma",
    "ugh_v2_delta",
)


def _make_v2_variant_month() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    range_hits_by_variant = {
        "ugh_v2_alpha": ["True", "True", "False", "True", "False"],
        "ugh_v2_beta": ["True", "False", "False", "True", "False"],
        "ugh_v2_gamma": ["False", "False", "False", "True", "False"],
        "ugh_v2_delta": ["True", "True", "True", "True", "False"],
    }
    for day_index in range(1, 6):
        for strategy_kind, range_hits in range_hits_by_variant.items():
            row = _make_obs(
                as_of_jst=f"2026-03-{day_index + 15:02d}T08:00:00+09:00",
                forecast_batch_id=f"batch_{day_index:03d}",
                strategy_kind=strategy_kind,
                range_hit=range_hits[day_index - 1],
                regime_label="trending",
                volatility_label="normal",
                intervention_risk="low",
                event_tags="fomc",
            )
            row["annotation_source"] = "ai"
            row["effective_event_tags"] = row["event_tags"]
            rows.append(row)
    return rows


def _make_health(
    *,
    as_of_jst: str = "2026-03-18T08:00:00+09:00",
    provider_name: str = "alphavantage",
    used_fallback_adjustment: str = "False",
    snapshot_lag_business_days: str = "0",
    run_status: str = "success",
) -> dict[str, str]:
    return {
        "as_of_jst": as_of_jst,
        "provider_name": provider_name,
        "used_fallback_adjustment": used_fallback_adjustment,
        "snapshot_lag_business_days": snapshot_lag_business_days,
        "run_status": run_status,
    }


# ---------------------------------------------------------------------------
# Tests: strategy metrics
# ---------------------------------------------------------------------------


class TestMonthlyStrategyMetrics:
    def test_basic_grouping(self) -> None:
        obs = [
            _make_obs(strategy_kind="ugh", direction_hit="True"),
            _make_obs(strategy_kind="ugh", direction_hit="False"),
            _make_obs(strategy_kind="baseline_random_walk", direction_hit="True"),
        ]
        metrics = compute_monthly_strategy_metrics(obs)
        ugh = next(m for m in metrics if m["strategy_kind"] == "ugh")
        assert ugh["forecast_count"] == 2
        assert ugh["direction_hit_count"] == 1
        assert ugh["direction_hit_rate"] == pytest.approx(0.5, abs=0.01)

        rw = next(m for m in metrics if m["strategy_kind"] == "baseline_random_walk")
        assert rw["forecast_count"] == 1
        assert rw["direction_hit_count"] == 1

    def test_empty_observations(self) -> None:
        metrics = compute_monthly_strategy_metrics([])
        ugh = next(m for m in metrics if m["strategy_kind"] == "ugh")
        assert ugh["forecast_count"] == 0
        assert ugh["direction_hit_rate"] is None

    def test_abs_error_computation(self) -> None:
        obs = [
            _make_obs(strategy_kind="ugh", close_error_bp="-20.0", magnitude_error_bp="-15.0"),
            _make_obs(strategy_kind="ugh", close_error_bp="10.0", magnitude_error_bp="5.0"),
        ]
        metrics = compute_monthly_strategy_metrics(obs)
        ugh = next(m for m in metrics if m["strategy_kind"] == "ugh")
        assert ugh["mean_abs_close_error_bp"] == 15.0
        assert ugh["mean_abs_magnitude_error_bp"] == 10.0

    def test_v2_range_hit_is_per_variant_without_ensemble_row(self) -> None:
        obs = _make_v2_variant_month()

        metrics = compute_monthly_strategy_metrics(obs)

        variant_rows = [
            m for m in metrics if m["strategy_kind"] in _UGH_V2_VARIANTS
        ]
        assert {m["strategy_kind"] for m in variant_rows} == set(_UGH_V2_VARIANTS)
        assert all(m["strategy_kind"] != "ugh_v2_ensemble" for m in metrics)
        expected_counts = {
            "ugh_v2_alpha": 3,
            "ugh_v2_beta": 2,
            "ugh_v2_gamma": 1,
            "ugh_v2_delta": 4,
        }
        for row in variant_rows:
            expected = expected_counts[row["strategy_kind"]]
            assert row["range_hit_count"] == expected
            assert row["range_hit_rate"] == pytest.approx(expected / 5, abs=0.001)


# ---------------------------------------------------------------------------
# Tests: baseline comparisons
# ---------------------------------------------------------------------------


class TestMonthlyBaselineComparisons:
    def test_delta_computation(self) -> None:
        obs = [
            _make_obs(strategy_kind="ugh", direction_hit="True", close_error_bp="10.0"),
            _make_obs(strategy_kind="ugh", direction_hit="True", close_error_bp="10.0"),
            _make_obs(
                strategy_kind="baseline_random_walk",
                direction_hit="False",
                close_error_bp="20.0",
            ),
            _make_obs(
                strategy_kind="baseline_random_walk",
                direction_hit="False",
                close_error_bp="20.0",
            ),
        ]
        strategy_metrics = compute_monthly_strategy_metrics(obs)
        comparisons = compute_monthly_baseline_comparisons(strategy_metrics)
        rw = next(
            c for c in comparisons if c["baseline_strategy_kind"] == "baseline_random_walk"
        )
        # baseline dir rate = 0.0, ugh dir rate = 1.0 → delta = -1.0
        assert rw["direction_accuracy_delta_vs_ugh"] == pytest.approx(-1.0, abs=0.01)
        # baseline close error = 20, ugh = 10 → delta = +10
        assert rw["mean_abs_close_error_bp_delta_vs_ugh"] == pytest.approx(10.0, abs=0.1)

    def test_no_ugh_data(self) -> None:
        obs = [
            _make_obs(strategy_kind="baseline_random_walk", direction_hit="True"),
        ]
        strategy_metrics = compute_monthly_strategy_metrics(obs)
        comparisons = compute_monthly_baseline_comparisons(strategy_metrics)
        rw = next(
            c for c in comparisons if c["baseline_strategy_kind"] == "baseline_random_walk"
        )
        assert rw["direction_accuracy_delta_vs_ugh"] is None

    def test_baseline_comparisons_only_include_baselines(self) -> None:
        strategy_metrics = compute_monthly_strategy_metrics(_make_v2_variant_month())

        comparisons = compute_monthly_baseline_comparisons(strategy_metrics)

        assert all(
            c["baseline_strategy_kind"] != "ugh_v2_ensemble"
            for c in comparisons
        )
        assert {
            c["baseline_strategy_kind"] for c in comparisons
        } == {
            "baseline_random_walk",
            "baseline_prev_day_direction",
            "baseline_simple_technical",
        }


# ---------------------------------------------------------------------------
# Tests: state metrics
# ---------------------------------------------------------------------------


class TestMonthlyStateMetrics:
    def test_grouping_by_state(self) -> None:
        obs = [
            _make_obs(dominant_state="fire", direction_hit="True"),
            _make_obs(dominant_state="fire", direction_hit="False"),
            _make_obs(dominant_state="dormant", direction_hit="True"),
        ]
        state_metrics = compute_monthly_state_metrics(obs)
        fire = next(s for s in state_metrics if s["dominant_state"] == "fire")
        assert fire["forecast_count"] == 2
        assert fire["direction_hit_rate"] == pytest.approx(0.5, abs=0.01)

        dormant = next(s for s in state_metrics if s["dominant_state"] == "dormant")
        assert dormant["forecast_count"] == 1


# ---------------------------------------------------------------------------
# Tests: annotation-aware metrics
# ---------------------------------------------------------------------------


class TestAnnotationConfirmedCase:
    def test_regime_metrics_confirmed_only(self) -> None:
        obs = [
            _make_obs(regime_label="trending", annotation_status="confirmed"),
            _make_obs(regime_label="choppy", annotation_status="confirmed"),
            _make_obs(regime_label="trending", annotation_status="pending"),
        ]
        regime = compute_monthly_regime_metrics(obs)
        labels = {r["regime_label"] for r in regime}
        assert "trending" in labels
        assert "choppy" in labels
        # pending row goes into unlabeled
        assert "unlabeled" in labels

    def test_volatility_metrics(self) -> None:
        obs = [
            _make_obs(volatility_label="high", annotation_status="confirmed"),
        ]
        vol = compute_monthly_volatility_metrics(obs)
        assert any(v["volatility_label"] == "high" for v in vol)

    def test_intervention_metrics(self) -> None:
        obs = [
            _make_obs(intervention_risk="high", annotation_status="confirmed"),
        ]
        intv = compute_monthly_intervention_metrics(obs)
        assert any(i["intervention_risk"] == "high" for i in intv)


class TestAnnotationUnlabeledPendingCase:
    def test_all_unlabeled(self) -> None:
        obs = [
            _make_obs(annotation_status=""),
            _make_obs(annotation_status=""),
        ]
        regime = compute_monthly_regime_metrics(obs)
        assert any(r["regime_label"] == "unlabeled" for r in regime)

    def test_all_pending(self) -> None:
        obs = [
            _make_obs(annotation_status="pending"),
        ]
        regime = compute_monthly_regime_metrics(obs)
        assert any(r["regime_label"] == "unlabeled" for r in regime)


class TestEventTagMetrics:
    def test_tag_expansion(self) -> None:
        obs = [
            _make_obs(event_tags="fomc|cpi_us", annotation_status="confirmed"),
        ]
        tags = compute_monthly_event_tag_metrics(obs)
        tag_names = {t["event_tag"] for t in tags}
        assert "fomc" in tag_names
        assert "cpi_us" in tag_names


class TestMonthlySliceMetrics:
    def test_v2_range_hit_is_per_variant_per_slice_without_ensemble_rows(self) -> None:
        slices = compute_monthly_slice_metrics(_make_v2_variant_month())
        assert all(s["strategy_kind"] != "ugh_v2_ensemble" for s in slices)

        expected_labels = {
            "regime_label": "trending",
            "volatility_label": "normal",
            "intervention_risk": "low",
            "event_tag": "fomc",
        }
        for dimension, label in expected_labels.items():
            variant_rows = [
                s
                for s in slices
                if s["slice_dimension"] == dimension
                and s["label"] == label
                and s["strategy_kind"] in _UGH_V2_VARIANTS
            ]
            assert {s["strategy_kind"] for s in variant_rows} == set(_UGH_V2_VARIANTS)
            expected_counts = {
                "ugh_v2_alpha": 3,
                "ugh_v2_beta": 2,
                "ugh_v2_gamma": 1,
                "ugh_v2_delta": 4,
            }
            for row in variant_rows:
                expected = expected_counts[row["strategy_kind"]]
                assert row["range_hit_count"] == expected
                assert row["range_hit_rate"] == str(round(expected / 5, 4))


# ---------------------------------------------------------------------------
# Tests: annotation coverage
# ---------------------------------------------------------------------------


class TestAnnotationCoverageSummary:
    def test_mixed(self) -> None:
        obs = [
            _make_obs(annotation_status="confirmed"),
            _make_obs(annotation_status="pending"),
            _make_obs(annotation_status=""),
        ]
        cov = compute_annotation_coverage_summary(obs)
        assert cov["confirmed_count"] == 1
        assert cov["pending_count"] == 1
        assert cov["unlabeled_count"] == 1
        assert cov["annotation_coverage_rate"] == pytest.approx(1 / 3, abs=0.01)

    def test_empty(self) -> None:
        cov = compute_annotation_coverage_summary([])
        assert cov["total_observations"] == 0
        assert cov["annotation_coverage_rate"] == 0.0


# ---------------------------------------------------------------------------
# Tests: provider health
# ---------------------------------------------------------------------------


class TestProviderHealthSummary:
    def test_basic(self) -> None:
        rows = [
            _make_health(run_status="success"),
            _make_health(run_status="success", used_fallback_adjustment="True",
                         snapshot_lag_business_days="1"),
        ]
        summary = compute_provider_health_summary(rows)
        assert summary["total_runs"] == 2
        assert summary["success_count"] == 2
        assert summary["fallback_adjustment_count"] == 1
        assert summary["lagged_snapshot_count"] == 1
        assert summary["provider_usage_count"] == 1

    def test_empty(self) -> None:
        summary = compute_provider_health_summary([])
        assert summary["total_runs"] == 0

    def test_provider_issue_multiple_providers(self) -> None:
        rows = [
            _make_health(provider_name="yahoo", run_status="failed"),
            _make_health(provider_name="alphavantage", run_status="success"),
        ]
        summary = compute_provider_health_summary(rows)
        assert summary["provider_usage_count"] == 2
        assert summary["failed_count"] == 1
        assert len(summary["provider_mix_summary"]) == 2


# ---------------------------------------------------------------------------
# Tests: representative cases
# ---------------------------------------------------------------------------


class TestRepresentativeCases:
    def test_success_and_failure_selection(self) -> None:
        obs = [
            _make_obs(direction_hit="True", close_error_bp="5.0"),
            _make_obs(direction_hit="True", close_error_bp="20.0"),
            _make_obs(direction_hit="False", close_error_bp="50.0"),
            _make_obs(direction_hit="False", close_error_bp="30.0"),
        ]
        successes, failures = select_representative_cases(obs, max_examples=2)
        assert len(successes) == 2
        assert len(failures) == 2
        # Successes sorted by smallest error
        assert float(successes[0]["close_error_bp"]) <= float(successes[1]["close_error_bp"])
        # Failures sorted by largest error
        assert float(failures[0]["close_error_bp"]) >= float(failures[1]["close_error_bp"])


# ---------------------------------------------------------------------------
# Tests: review flags
# ---------------------------------------------------------------------------


class TestReviewFlags:
    def test_keep_current_logic(self) -> None:
        """When no issues, keep_current_logic is returned."""
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.6,
                "range_hit_rate": 0.5,
                "state_proxy_hit_rate": 0.5,
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 12.0,
                "median_abs_close_error_bp": 14.0,
                "median_abs_magnitude_error_bp": 11.0,
                "direction_hit_count": 12,
                "range_hit_count": 10,
                "state_proxy_hit_count": 10,
            },
        ]
        baseline_comparisons = [
            {
                "baseline_strategy_kind": "baseline_random_walk",
                "direction_accuracy_delta_vs_ugh": -0.1,
                "mean_abs_close_error_bp_delta_vs_ugh": 5.0,
                "mean_abs_magnitude_error_bp_delta_vs_ugh": 3.0,
                "state_proxy_hit_rate_delta_vs_ugh": None,
            },
            {
                "baseline_strategy_kind": "baseline_simple_technical",
                "direction_accuracy_delta_vs_ugh": -0.05,
                "mean_abs_close_error_bp_delta_vs_ugh": 2.0,
                "mean_abs_magnitude_error_bp_delta_vs_ugh": 1.0,
                "state_proxy_hit_rate_delta_vs_ugh": None,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 1,
            "fallback_adjustment_count": 1,
        }

        flags = compute_review_flags(
            strategy_metrics, baseline_comparisons,
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        assert len(flags) == 1
        assert flags[0]["flag"] == "keep_current_logic"


class TestInsufficientDataFlag:
    def test_insufficient_data(self) -> None:
        strategy_metrics = [
            {"strategy_kind": "ugh", "forecast_count": 2},
        ]
        flags = compute_review_flags(
            strategy_metrics, [], {}, {"total_runs": 0},
            requested_window_count=20, missing_window_count=18,
        )
        assert len(flags) == 1
        assert flags[0]["flag"] == "insufficient_data"


def _healthy_inputs() -> tuple:
    """Blended inputs that produce only keep_current_logic (no other flags)."""
    strategy_metrics = [{
        "strategy_kind": "ugh",
        "forecast_count": 20,
        "direction_hit_rate": 0.6,
        "range_hit_rate": 0.5,
        "state_proxy_hit_rate": 0.5,
        "mean_abs_close_error_bp": 15.0,
        "mean_abs_magnitude_error_bp": 12.0,
    }]
    baseline_comparisons = [
        {"baseline_strategy_kind": "baseline_random_walk",
         "direction_accuracy_delta_vs_ugh": -0.1,
         "mean_abs_close_error_bp_delta_vs_ugh": 5.0,
         "mean_abs_magnitude_error_bp_delta_vs_ugh": 3.0,
         "state_proxy_hit_rate_delta_vs_ugh": None},
        {"baseline_strategy_kind": "baseline_simple_technical",
         "direction_accuracy_delta_vs_ugh": -0.05,
         "mean_abs_close_error_bp_delta_vs_ugh": 2.0,
         "mean_abs_magnitude_error_bp_delta_vs_ugh": 1.0,
         "state_proxy_hit_rate_delta_vs_ugh": None},
    ]
    annotation_cov = {"annotation_coverage_rate": 0.8}
    provider_health = {"total_runs": 20, "lagged_snapshot_count": 1, "fallback_adjustment_count": 1}
    return strategy_metrics, baseline_comparisons, annotation_cov, provider_health


class TestRegimeDirectionCollapseFlag:
    def test_choppy_collapse_fires_despite_healthy_blend(self) -> None:
        """A confirmed choppy 0% slice flags even when blended metrics are fine."""
        sm, bc, cov, ph = _healthy_inputs()
        regime_metrics = [
            {"regime_label": "trending", "observation_count": 10,
             "direction_hit_rate": 0.9, "mean_abs_close_error_bp": 12.0},
            {"regime_label": "choppy", "observation_count": 8,
             "direction_hit_rate": 0.0, "mean_abs_close_error_bp": 32.0},
        ]
        flags = compute_review_flags(
            sm, bc, cov, ph, requested_window_count=20, missing_window_count=0,
            regime_metrics=regime_metrics,
        )
        ids = {f["flag"] for f in flags}
        assert "regime_direction_collapse" in ids
        assert "keep_current_logic" not in ids

    def test_high_vol_collapse_fires(self) -> None:
        sm, bc, cov, ph = _healthy_inputs()
        vol_metrics = [
            {"volatility_label": "low", "observation_count": 9,
             "direction_hit_rate": 0.8, "mean_abs_close_error_bp": 10.0},
            {"volatility_label": "high", "observation_count": 7,
             "direction_hit_rate": 0.0, "mean_abs_close_error_bp": 64.0},
        ]
        flags = compute_review_flags(
            sm, bc, cov, ph, requested_window_count=20, missing_window_count=0,
            volatility_metrics=vol_metrics,
        )
        assert "volatility_direction_collapse" in {f["flag"] for f in flags}

    def test_sparse_slice_does_not_misfire(self) -> None:
        sm, bc, cov, ph = _healthy_inputs()
        regime_metrics = [
            {"regime_label": "choppy", "observation_count": 3,  # < THRESHOLD_MINIMUM_OBSERVATIONS
             "direction_hit_rate": 0.0, "mean_abs_close_error_bp": 32.0},
        ]
        flags = compute_review_flags(
            sm, bc, cov, ph, requested_window_count=20, missing_window_count=0,
            regime_metrics=regime_metrics,
        )
        ids = {f["flag"] for f in flags}
        assert "regime_direction_collapse" not in ids
        assert flags[0]["flag"] == "keep_current_logic"

    def test_unlabeled_slice_skipped(self) -> None:
        sm, bc, cov, ph = _healthy_inputs()
        regime_metrics = [
            {"regime_label": "unlabeled", "observation_count": 12,
             "direction_hit_rate": 0.0, "mean_abs_close_error_bp": 30.0},
        ]
        flags = compute_review_flags(
            sm, bc, cov, ph, requested_window_count=20, missing_window_count=0,
            regime_metrics=regime_metrics,
        )
        assert "regime_direction_collapse" not in {f["flag"] for f in flags}


class TestInspectMagnitudeMappingFlag:
    def test_close_error_worse_than_random_walk(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.6,
                "state_proxy_hit_rate": 0.4,
                "mean_abs_close_error_bp": 25.0,
                "mean_abs_magnitude_error_bp": 20.0,
            },
        ]
        baseline_comparisons = [
            {
                "baseline_strategy_kind": "baseline_random_walk",
                "direction_accuracy_delta_vs_ugh": 0.0,
                # baseline error lower than UGH → delta negative
                "mean_abs_close_error_bp_delta_vs_ugh": -10.0,
                "mean_abs_magnitude_error_bp_delta_vs_ugh": -5.0,
                "state_proxy_hit_rate_delta_vs_ugh": None,
            },
            {
                "baseline_strategy_kind": "baseline_simple_technical",
                "direction_accuracy_delta_vs_ugh": 0.0,
                "mean_abs_close_error_bp_delta_vs_ugh": 0.0,
                "mean_abs_magnitude_error_bp_delta_vs_ugh": 0.0,
                "state_proxy_hit_rate_delta_vs_ugh": None,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 0,
            "fallback_adjustment_count": 0,
        }

        flags = compute_review_flags(
            strategy_metrics, baseline_comparisons,
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "inspect_magnitude_mapping" in flag_ids


class TestInspectDirectionLogicFlag:
    def test_direction_deficit_vs_technical(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.4,
                "state_proxy_hit_rate": 0.4,
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 12.0,
            },
        ]
        baseline_comparisons = [
            {
                "baseline_strategy_kind": "baseline_random_walk",
                "direction_accuracy_delta_vs_ugh": 0.0,
                "mean_abs_close_error_bp_delta_vs_ugh": 0.0,
                "mean_abs_magnitude_error_bp_delta_vs_ugh": 0.0,
                "state_proxy_hit_rate_delta_vs_ugh": None,
            },
            {
                "baseline_strategy_kind": "baseline_simple_technical",
                # baseline direction 15% better than UGH
                "direction_accuracy_delta_vs_ugh": 0.15,
                "mean_abs_close_error_bp_delta_vs_ugh": 0.0,
                "mean_abs_magnitude_error_bp_delta_vs_ugh": 0.0,
                "state_proxy_hit_rate_delta_vs_ugh": None,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 0,
            "fallback_adjustment_count": 0,
        }

        flags = compute_review_flags(
            strategy_metrics, baseline_comparisons,
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "inspect_direction_logic" in flag_ids


class TestInspectStateMappingFlag:
    def test_state_hit_but_magnitude_bad(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.6,
                "state_proxy_hit_rate": 0.8,  # > THRESHOLD_STATE_HIT_HIGH
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 35.0,  # > THRESHOLD_MAGNITUDE_ERROR
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 0,
            "fallback_adjustment_count": 0,
        }

        flags = compute_review_flags(
            strategy_metrics, [],
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "inspect_state_mapping" in flag_ids


class TestProviderHealthIssueFlag:
    def test_high_lag_rate(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.6,
                "state_proxy_hit_rate": 0.5,
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 12.0,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 10,  # 50% lag rate
            "fallback_adjustment_count": 0,
        }

        flags = compute_review_flags(
            strategy_metrics, [],
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "provider_quality_issue" in flag_ids

    def test_high_fallback_rate(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.6,
                "state_proxy_hit_rate": 0.5,
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 12.0,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 0,
            "fallback_adjustment_count": 10,  # 50% fallback rate
        }

        flags = compute_review_flags(
            strategy_metrics, [],
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "provider_quality_issue" in flag_ids


class TestMissingWindowsFlag:
    def test_missing_windows(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 10,
                "direction_hit_rate": 0.6,
                "state_proxy_hit_rate": 0.5,
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 12.0,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.8}
        provider_health = {
            "total_runs": 10,
            "lagged_snapshot_count": 0,
            "fallback_adjustment_count": 0,
        }

        flags = compute_review_flags(
            strategy_metrics, [],
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=8,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "missing_windows" in flag_ids


class TestLowAnnotationCoverageFlag:
    def test_low_coverage(self) -> None:
        strategy_metrics = [
            {
                "strategy_kind": "ugh",
                "forecast_count": 20,
                "direction_hit_rate": 0.6,
                "state_proxy_hit_rate": 0.5,
                "mean_abs_close_error_bp": 15.0,
                "mean_abs_magnitude_error_bp": 12.0,
            },
        ]
        annotation_cov = {"annotation_coverage_rate": 0.1}
        provider_health = {
            "total_runs": 20,
            "lagged_snapshot_count": 0,
            "fallback_adjustment_count": 0,
        }

        flags = compute_review_flags(
            strategy_metrics, [],
            annotation_cov, provider_health,
            requested_window_count=20, missing_window_count=0,
        )
        flag_ids = [f["flag"] for f in flags]
        assert "low_annotation_coverage" in flag_ids


# ---------------------------------------------------------------------------
# Tests: recommendation summary
# ---------------------------------------------------------------------------


class TestRecommendationSummary:
    def test_keep_current(self) -> None:
        flags = [{"flag": "keep_current_logic", "reason": "ok"}]
        summary = build_recommendation_summary(flags)
        assert "keeping current logic" in summary.lower()

    def test_insufficient_data(self) -> None:
        flags = [{"flag": "insufficient_data", "reason": "too few"}]
        summary = build_recommendation_summary(flags)
        assert "insufficient" in summary.lower()

    def test_multiple_flags(self) -> None:
        flags = [
            {"flag": "inspect_magnitude_mapping", "reason": "reason1"},
            {"flag": "inspect_direction_logic", "reason": "reason2"},
        ]
        summary = build_recommendation_summary(flags)
        assert "magnitude" in summary.lower()
        assert "direction" in summary.lower()

    def test_collapse_only_flags_are_not_blank(self) -> None:
        """A collapse-only review must produce a non-empty recommendation
        (PR #120 review: build_recommendation_summary must handle the new IDs)."""
        for fid in ("regime_direction_collapse", "volatility_direction_collapse"):
            summary = build_recommendation_summary([{"flag": fid, "reason": "choppy 0%"}])
            assert summary.strip() != ""
            assert "direction logic" in summary.lower()


# ---------------------------------------------------------------------------
# Tests: full monthly review
# ---------------------------------------------------------------------------


class TestRunMonthlyReview:
    def test_basic_review(self) -> None:
        obs = [
            _make_obs(as_of_jst="2026-03-18T08:00:00+09:00", strategy_kind="ugh"),
            _make_obs(as_of_jst="2026-03-19T08:00:00+09:00", strategy_kind="ugh"),
            _make_obs(
                as_of_jst="2026-03-18T08:00:00+09:00",
                strategy_kind="baseline_random_walk",
            ),
        ]
        health = [_make_health()]

        review = run_monthly_review(
            obs, health,
            review_generated_at_jst=_REVIEW_DATE,
            business_day_count=20,
        )

        assert review["review_version"] == "v1"
        assert review["pair"] == "USDJPY"
        assert review["requested_window_count"] == 20
        assert review["included_window_count"] == 2
        assert review["missing_window_count"] == 18
        assert len(review["monthly_strategy_metrics"]) >= 4
        assert len(review["monthly_baseline_comparisons"]) >= 1
        assert len(review["review_flags"]) >= 1
        assert review["recommendation_summary"] != ""
        assert review["annotation_coverage_summary"]["total_observations"] == 3

    def test_empty_data(self) -> None:
        review = run_monthly_review(
            [], [],
            review_generated_at_jst=_REVIEW_DATE,
            business_day_count=20,
        )
        assert review["included_window_count"] == 0
        assert review["missing_window_count"] == 20
        # Should flag insufficient data
        assert any(f["flag"] == "insufficient_data" for f in review["review_flags"])

    def test_no_annotations(self) -> None:
        obs = [_make_obs() for _ in range(10)]
        review = run_monthly_review(
            obs, [],
            review_generated_at_jst=_REVIEW_DATE,
            include_annotations=False,
        )
        assert review["monthly_regime_metrics"] == []
        assert review["monthly_volatility_metrics"] == []


class TestExistingForecastUnchanged:
    """Verify that existing forecast/evaluation models are unchanged."""

    def test_forecast_record_unchanged(self) -> None:
        from ugh_quantamental.fx_protocol.models import ForecastRecord, StrategyKind

        assert hasattr(ForecastRecord, "model_fields")
        assert "forecast_id" in ForecastRecord.model_fields
        assert StrategyKind.ugh.value == "ugh"

    def test_evaluation_record_unchanged(self) -> None:
        from ugh_quantamental.fx_protocol.models import EvaluationRecord

        assert hasattr(EvaluationRecord, "model_fields")
        assert "evaluation_id" in EvaluationRecord.model_fields
        assert "direction_hit" in EvaluationRecord.model_fields

    def test_weekly_report_models_unchanged(self) -> None:
        from ugh_quantamental.fx_protocol.report_models import (
            WeeklyReportRequest,
            WeeklyReportResult,
        )

        assert hasattr(WeeklyReportRequest, "model_fields")
        assert hasattr(WeeklyReportResult, "model_fields")
        req = WeeklyReportRequest(
            pair="USDJPY",
            report_generated_at_jst=_REVIEW_DATE,
        )
        assert req.business_day_count == 5
