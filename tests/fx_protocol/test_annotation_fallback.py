"""Tests for annotation_fallback.py — deterministic OHLC-derived labels."""

from __future__ import annotations

from ugh_quantamental.fx_protocol.annotation_fallback import (
    build_ohlc_fallback_annotations,
    classify_regime,
    classify_volatility,
    intraday_range_bp,
)


class TestPrimitives:
    def test_intraday_range_bp(self) -> None:
        # (151 - 149) / 150 * 1e4 ≈ 133.3 bp
        assert round(intraday_range_bp(151.0, 149.0, 150.0), 1) == 133.3

    def test_intraday_range_nonpositive_open(self) -> None:
        assert intraday_range_bp(1.0, 0.5, 0.0) == 0.0

    def test_regime_trending_consistent_sign(self) -> None:
        assert classify_regime([10.0, 12.0, 8.0, 15.0, 9.0]) == "trending"

    def test_regime_choppy_alternating_sign(self) -> None:
        # Balanced signs (2 up / 2 down) -> dominant share 0.5 < 0.6 -> choppy.
        assert classify_regime([10.0, -12.0, 8.0, -15.0]) == "choppy"

    def test_regime_all_flat_is_choppy(self) -> None:
        assert classify_regime([0.0, 0.0, 0.0]) == "choppy"

    def test_regime_empty_is_choppy(self) -> None:
        assert classify_regime([]) == "choppy"

    def test_volatility_absolute_thresholds(self) -> None:
        assert classify_volatility(120.0, 0.0) == "high"
        assert classify_volatility(60.0, 0.0) == "normal"
        assert classify_volatility(10.0, 0.0) == "low"

    def test_volatility_ratio_thresholds(self) -> None:
        assert classify_volatility(100.0, 50.0) == "high"  # ratio 2.0
        assert classify_volatility(60.0, 50.0) == "normal"  # ratio 1.2
        assert classify_volatility(20.0, 50.0) == "low"  # ratio 0.4


def _obs(
    forecast_id: str,
    as_of: str,
    *,
    o: float,
    h: float,
    low: float,
    c: float,
    change: float,
) -> dict[str, str]:
    return {
        "forecast_id": forecast_id,
        "as_of_jst": as_of,
        "realized_open": str(o),
        "realized_high": str(h),
        "realized_low": str(low),
        "realized_close": str(c),
        "realized_close_change_bp": str(change),
    }


class TestBuildOhlcFallbackAnnotations:
    def test_deterministic_same_input_same_labels(self) -> None:
        obs = [
            _obs("fc1", "2026-03-16T08:00:00+09:00", o=150, h=150.5, low=149.5, c=150.4, change=10),
            _obs("fc2", "2026-03-17T08:00:00+09:00", o=150.4, h=151.0, low=150.2, c=150.9, change=12),
        ]
        a = build_ohlc_fallback_annotations(obs)
        b = build_ohlc_fallback_annotations(obs)
        assert a == b
        assert set(a) == {"fc1", "fc2"}
        assert a["fc1"]["regime_label"] in ("trending", "choppy")
        assert a["fc1"]["volatility_label"] in ("low", "normal", "high")

    def test_variants_share_one_market_day(self) -> None:
        """Multiple forecast_ids on the same day get the same labels."""
        obs = [
            _obs("alpha", "2026-03-16T08:00:00+09:00", o=150, h=150.5, low=149.5, c=150.4, change=10),
            _obs("gamma", "2026-03-16T08:00:00+09:00", o=150, h=150.5, low=149.5, c=150.4, change=10),
        ]
        result = build_ohlc_fallback_annotations(obs)
        assert result["alpha"] == result["gamma"]

    def test_skips_rows_without_ohlc(self) -> None:
        obs = [{"forecast_id": "fc1", "as_of_jst": "2026-03-16T08:00:00+09:00"}]
        assert build_ohlc_fallback_annotations(obs) == {}

    def test_skips_rows_without_forecast_id(self) -> None:
        obs = [_obs("", "2026-03-16T08:00:00+09:00", o=150, h=151, low=149, c=150.5, change=10)]
        assert build_ohlc_fallback_annotations(obs) == {}

    def test_trending_series(self) -> None:
        obs = [
            _obs(f"fc{i}", f"2026-03-{16 + i:02d}T08:00:00+09:00",
                 o=150 + i, h=150.5 + i, low=149.8 + i, c=150.4 + i, change=15)
            for i in range(5)
        ]
        result = build_ohlc_fallback_annotations(obs)
        assert all(v["regime_label"] == "trending" for v in result.values())

    def test_labels_use_ohlc_not_performance(self) -> None:
        """direction_hit / close_error_bp are ignored entirely."""
        base = _obs("fc1", "2026-03-16T08:00:00+09:00", o=150, h=150.5, low=149.5, c=150.4, change=10)
        leaky = dict(base, direction_hit="False", close_error_bp="999.0")
        assert build_ohlc_fallback_annotations([base]) == build_ohlc_fallback_annotations([leaky])
