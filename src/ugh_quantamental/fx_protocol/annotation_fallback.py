"""Deterministic OHLC-derived regime / volatility annotation fallback.

Pure functions: the same realized-OHLC window always yields the same labels.
No network, file I/O, or randomness.

This module is used in two places:

1. As the **market-derived label source** for the default deterministic AI
   adapter (:mod:`ai_annotations`), replacing the previous performance-derived
   heuristics.
2. As the **lowest-precedence annotation fallback tier** (below manual) that
   fills regime / volatility only when AI, auto, and manual sources are all
   absent (consumed by :func:`labeled_observations.build_labeled_observations`).

⚠️ Labels are derived ONLY from realized OHLC / market statistics — never from
forecast performance fields (``direction_hit``, ``close_error_bp``). Deriving
regime from whether the model was *right* makes "choppy = days the model
missed" definitionally circular and invalidates regime-stratified analysis
(``engine_review_2026_06_planning.md`` §5.1). Keeping the two axes
market-derived is the whole point of FX-ANNOT-LIVE.

Importable without SQLAlchemy.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

# ---------------------------------------------------------------------------
# Shared label vocabulary (must match the monthly review regime / volatility
# axes exactly — see engine_review_2026_06_planning.md §5.1).
# ---------------------------------------------------------------------------

REGIME_TRENDING: str = "trending"
REGIME_CHOPPY: str = "choppy"

VOL_LOW: str = "low"
VOL_NORMAL: str = "normal"
VOL_HIGH: str = "high"

# ---------------------------------------------------------------------------
# Tunable thresholds (module-level constants, easily changeable — mirrors the
# THRESHOLD_* convention in monthly_review.py).
# ---------------------------------------------------------------------------

#: Trailing window (in market days, inclusive of the current day) over which
#: close-change sign consistency is measured for the regime label.
REGIME_WINDOW_DAYS: int = 5
#: Dominant-sign share at/above which a window is "trending" (else "choppy").
REGIME_TRENDING_FRACTION: float = 0.6

#: Trailing window (prior market days, excluding the current day) used to
#: build the volatility baseline.
VOL_WINDOW_DAYS: int = 5
#: Current-day intraday range / trailing-mean-range ratios for high / low.
VOL_HIGH_RATIO: float = 1.5
VOL_LOW_RATIO: float = 0.6
#: Absolute intraday-range thresholds (bp) used when no trailing baseline is
#: available yet (the first few days of a series).
VOL_HIGH_ABS_BP: float = 90.0
VOL_NORMAL_ABS_BP: float = 45.0


# ---------------------------------------------------------------------------
# Pure classification primitives
# ---------------------------------------------------------------------------


def intraday_range_bp(high: float, low: float, open_: float) -> float:
    """Return the realized intraday range as basis points of the open price."""
    if open_ <= 0:
        return 0.0
    return (high - low) / open_ * 10000.0


def classify_regime(close_changes_bp: Sequence[float]) -> str:
    """Classify regime from a trailing window of signed close changes (bp).

    "trending" when one sign accounts for at least
    :data:`REGIME_TRENDING_FRACTION` of the non-flat changes; "choppy"
    otherwise (an all-flat or empty window is "choppy").
    """
    signs = [1 if c > 0 else (-1 if c < 0 else 0) for c in close_changes_bp]
    nonflat = [s for s in signs if s != 0]
    if not nonflat:
        return REGIME_CHOPPY
    pos = sum(1 for s in nonflat if s > 0)
    dominant = max(pos, len(nonflat) - pos) / len(nonflat)
    return REGIME_TRENDING if dominant >= REGIME_TRENDING_FRACTION else REGIME_CHOPPY


def classify_volatility(range_bp: float, baseline_bp: float) -> str:
    """Classify volatility from the intraday range vs a trailing baseline.

    Ratio thresholds are used when a positive baseline is available; otherwise
    absolute basis-point thresholds are used.
    """
    if baseline_bp > 0:
        ratio = range_bp / baseline_bp
        if ratio >= VOL_HIGH_RATIO:
            return VOL_HIGH
        if ratio <= VOL_LOW_RATIO:
            return VOL_LOW
        return VOL_NORMAL
    if range_bp >= VOL_HIGH_ABS_BP:
        return VOL_HIGH
    if range_bp >= VOL_NORMAL_ABS_BP:
        return VOL_NORMAL
    return VOL_LOW


# ---------------------------------------------------------------------------
# Series-level builder
# ---------------------------------------------------------------------------


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def build_ohlc_fallback_annotations(
    observations: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Derive per-forecast regime / volatility labels from realized OHLC.

    Pure and deterministic. Observations are grouped by ``as_of_jst`` (one
    market day shared across strategy variants); the daily close-change and
    intraday-range series are built, then each day is assigned a regime /
    volatility label from its trailing window. Returns a dict keyed by
    ``forecast_id`` with ``regime_label`` / ``volatility_label``.

    Rows lacking a ``forecast_id``, ``as_of_jst``, or a complete, positive
    OHLC quadruple are skipped (no label is produced for them).
    """
    day_ohlc: dict[str, dict[str, float]] = {}
    day_forecasts: dict[str, list[str]] = defaultdict(list)

    for obs in observations:
        forecast_id = obs.get("forecast_id", "")
        as_of = obs.get("as_of_jst", "")
        if not forecast_id or not as_of:
            continue
        o = _parse_float(obs.get("realized_open", ""))
        h = _parse_float(obs.get("realized_high", ""))
        low = _parse_float(obs.get("realized_low", ""))
        c = _parse_float(obs.get("realized_close", ""))
        if o is None or h is None or low is None or c is None or o <= 0:
            continue

        day_forecasts[as_of].append(forecast_id)
        if as_of not in day_ohlc:
            change = _parse_float(obs.get("realized_close_change_bp", ""))
            if change is None:
                change = (c - o) / o * 10000.0
            day_ohlc[as_of] = {
                "range_bp": intraday_range_bp(h, low, o),
                "change_bp": change,
            }

    day_order = sorted(day_ohlc)

    labels_by_day: dict[str, tuple[str, str]] = {}
    for i, day in enumerate(day_order):
        window = day_order[max(0, i - REGIME_WINDOW_DAYS + 1): i + 1]
        regime = classify_regime([day_ohlc[d]["change_bp"] for d in window])

        prior = day_order[max(0, i - VOL_WINDOW_DAYS): i]
        prior_ranges = [day_ohlc[d]["range_bp"] for d in prior]
        baseline = sum(prior_ranges) / len(prior_ranges) if prior_ranges else 0.0
        vol = classify_volatility(day_ohlc[day]["range_bp"], baseline)
        labels_by_day[day] = (regime, vol)

    result: dict[str, dict[str, str]] = {}
    for day, forecast_ids in day_forecasts.items():
        regime, vol = labels_by_day[day]
        for forecast_id in forecast_ids:
            result[forecast_id] = {
                "regime_label": regime,
                "volatility_label": vol,
            }
    return result


__all__ = [
    "REGIME_TRENDING",
    "REGIME_CHOPPY",
    "VOL_LOW",
    "VOL_NORMAL",
    "VOL_HIGH",
    "intraday_range_bp",
    "classify_regime",
    "classify_volatility",
    "build_ohlc_fallback_annotations",
]
