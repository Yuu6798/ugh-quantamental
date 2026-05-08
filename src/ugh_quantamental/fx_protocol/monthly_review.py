"""Monthly Review v1 — pure aggregation and review-flag layer for the FX Daily Protocol.

Aggregates one month of daily forecast/outcome/evaluation data to produce:
- Per-strategy monthly metrics (UGH + baselines)
- Baseline vs UGH delta comparisons
- Annotation-aware regime/volatility/intervention/event-tag slicing
- Provider health monthly summary
- Rule-based review flags and recommendation summary
- Representative success/failure case examples

This module is a pure post-processing / read-only layer:
- No forecast / outcome / evaluation logic is changed.
- No new forecasts are generated.
- Importable without SQLAlchemy.
- All data is derived from persisted CSV history and annotation files.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from ugh_quantamental.fx_protocol.metrics_utils import (
    collect_floats,
    count_bool_rows,
    safe_mean,
    safe_median,
    safe_rate,
)
from ugh_quantamental.fx_protocol.models import is_ugh_kind

logger = logging.getLogger(__name__)

_JST = ZoneInfo("Asia/Tokyo")

# ---------------------------------------------------------------------------
# Review flag threshold constants
# ---------------------------------------------------------------------------
# All thresholds are explicit, documented, and intended to be easily changed.

#: UGH loses to baseline_random_walk on mean close error for this many bp or more.
THRESHOLD_CLOSE_ERROR_VS_RANDOM_WALK_BP: float = 5.0
#: UGH direction accuracy is this many pct points below baseline_simple_technical.
THRESHOLD_DIRECTION_DEFICIT_VS_TECHNICAL_PCT: float = 0.10
#: State proxy hit rate is high but magnitude error exceeds this bp threshold.
THRESHOLD_STATE_HIT_HIGH: float = 0.70
THRESHOLD_MAGNITUDE_ERROR_DESPITE_STATE_HIT_BP: float = 30.0
#: Confirmed annotation coverage rate below this triggers a flag.
THRESHOLD_ANNOTATION_COVERAGE_LOW: float = 0.30
#: Provider lag or fallback count exceeding this fraction of total runs triggers a flag.
THRESHOLD_PROVIDER_LAG_RATE: float = 0.30
THRESHOLD_PROVIDER_FALLBACK_RATE: float = 0.30
#: Missing window count exceeding this fraction of requested windows triggers a flag.
THRESHOLD_MISSING_WINDOW_RATE: float = 0.25
#: Minimum observations to evaluate strategy performance meaningfully.
THRESHOLD_MINIMUM_OBSERVATIONS: int = 5


# ---------------------------------------------------------------------------
# Strategies to compare
# ---------------------------------------------------------------------------

#: Order: legacy ``ugh`` first (for v1-era replay), then v2 variants, then baselines.
#: Downstream UGH-only paths pool rows via :func:`is_ugh_kind` rather than
#: relying on a single canonical kind. Anchor-based comparisons (baseline
#: deltas, review flags) iterate ``UGH_KINDS`` and pick the first variant with
#: non-zero forecast_count, so v1-era reports anchor on ``ugh`` and v2-era
#: reports anchor on whichever variant has data first.
UGH_KINDS: tuple[str, ...] = (
    "ugh",
    "ugh_v2_alpha",
    "ugh_v2_beta",
    "ugh_v2_gamma",
    "ugh_v2_delta",
)

STRATEGY_KINDS: tuple[str, ...] = (
    *UGH_KINDS,
    "baseline_random_walk",
    "baseline_prev_day_direction",
    "baseline_simple_technical",
)


def _select_canonical_ugh_metrics(
    strategy_metrics: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Pick the canonical UGH metrics row for anchor comparisons.

    Returns the first metrics row in ``UGH_KINDS`` order whose
    ``forecast_count > 0``. If no UGH-class row has data, falls back to the
    legacy ``ugh`` row if present, else ``None``.
    """
    by_kind = {m["strategy_kind"]: m for m in strategy_metrics if m.get("strategy_kind")}
    for kind in UGH_KINDS:
        m = by_kind.get(kind)
        if m is not None and m.get("forecast_count", 0) > 0:
            return m
    return by_kind.get("ugh")


# ---------------------------------------------------------------------------
# Pure helpers (no I/O)
# ---------------------------------------------------------------------------


def _resolve_month_window(
    review_date_jst: datetime,
    business_day_count: int = 20,
) -> tuple[str, str]:
    """Return (start_date_str, end_date_str) YYYYMMDD for the month window.

    Walks backwards from the day *before* review_date_jst collecting
    business_day_count Mon-Fri dates.
    """
    if review_date_jst.tzinfo is not None:
        ts = review_date_jst.astimezone(_JST)
    else:
        ts = review_date_jst.replace(tzinfo=_JST)

    dates: list[datetime] = []
    candidate = ts.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    while len(dates) < business_day_count:
        if candidate.isoweekday() in range(1, 6):
            dates.append(candidate)
        candidate -= timedelta(days=1)

    dates.reverse()
    return dates[0].strftime("%Y%m%d"), dates[-1].strftime("%Y%m%d")


def _is_in_window(date_str: str, start: str, end: str) -> bool:
    """Check if a YYYYMMDD date string falls within [start, end]."""
    return start <= date_str <= end


# ---------------------------------------------------------------------------
# Strategy metrics computation
# ---------------------------------------------------------------------------


def compute_monthly_strategy_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute per-strategy metrics from monthly observations.

    For each strategy, computes:
    - forecast_count, direction_hit_count, direction_hit_rate
    - range_hit_count, range_hit_rate
    - state_proxy_hit_count, state_proxy_hit_rate
    - mean_abs_close_error_bp, median_abs_close_error_bp
    - mean_abs_magnitude_error_bp, median_abs_magnitude_error_bp
    """
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in observations:
        sk = row.get("strategy_kind", "")
        if sk:
            groups[sk].append(row)

    result: list[dict[str, Any]] = []
    for sk in STRATEGY_KINDS:
        rows = groups.get(sk, [])
        n = len(rows)
        dir_hits = count_bool_rows(rows, "direction_hit")
        range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
        range_hits = count_bool_rows(range_evaluable, "range_hit")
        state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
        state_hits = count_bool_rows(state_evaluable, "state_proxy_hit")
        close_errors = [abs(v) for v in collect_floats(rows, "close_error_bp")]
        mag_errors = [abs(v) for v in collect_floats(rows, "magnitude_error_bp")]

        result.append({
            "strategy_kind": sk,
            "forecast_count": n,
            "direction_hit_count": dir_hits,
            "direction_hit_rate": safe_rate(dir_hits, n),
            "range_hit_count": range_hits,
            "range_hit_rate": safe_rate(range_hits, len(range_evaluable))
            if range_evaluable
            else None,
            "state_proxy_hit_count": state_hits,
            "state_proxy_hit_rate": safe_rate(state_hits, len(state_evaluable))
            if state_evaluable
            else None,
            "mean_abs_close_error_bp": safe_mean(close_errors),
            "median_abs_close_error_bp": safe_median(close_errors),
            "mean_abs_magnitude_error_bp": safe_mean(mag_errors),
            "median_abs_magnitude_error_bp": safe_median(mag_errors),
        })

    # Also include any extra strategies present in data but not in STRATEGY_KINDS
    for sk in sorted(groups.keys()):
        if sk not in STRATEGY_KINDS:
            rows = groups[sk]
            n = len(rows)
            dir_hits = count_bool_rows(rows, "direction_hit")
            range_evaluable = [r for r in rows if r.get("range_hit", "") != ""]
            range_hits = count_bool_rows(range_evaluable, "range_hit")
            state_evaluable = [r for r in rows if r.get("state_proxy_hit", "") != ""]
            state_hits = count_bool_rows(state_evaluable, "state_proxy_hit")
            close_errors = [abs(v) for v in collect_floats(rows, "close_error_bp")]
            mag_errors = [abs(v) for v in collect_floats(rows, "magnitude_error_bp")]

            result.append({
                "strategy_kind": sk,
                "forecast_count": n,
                "direction_hit_count": dir_hits,
                "direction_hit_rate": safe_rate(dir_hits, n),
                "range_hit_count": range_hits,
                "range_hit_rate": safe_rate(range_hits, len(range_evaluable))
                if range_evaluable
                else None,
                "state_proxy_hit_count": state_hits,
                "state_proxy_hit_rate": safe_rate(state_hits, len(state_evaluable))
                if state_evaluable
                else None,
                "mean_abs_close_error_bp": safe_mean(close_errors),
                "median_abs_close_error_bp": safe_median(close_errors),
                "mean_abs_magnitude_error_bp": safe_mean(mag_errors),
                "median_abs_magnitude_error_bp": safe_median(mag_errors),
            })

    return result


# ---------------------------------------------------------------------------
# Baseline comparisons
# ---------------------------------------------------------------------------


def compute_monthly_baseline_comparisons(
    strategy_metrics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute monthly UGH vs baseline deltas.

    For each baseline, computes:
    - direction_accuracy_delta_vs_ugh (baseline - UGH, negative = UGH better)
    - mean_abs_close_error_bp_delta_vs_ugh (baseline - UGH, positive = UGH better)
    - mean_abs_magnitude_error_bp_delta_vs_ugh
    - state_proxy_hit_rate_delta_vs_ugh (if computable)
    """
    ugh = _select_canonical_ugh_metrics(strategy_metrics)

    result: list[dict[str, Any]] = []
    for m in strategy_metrics:
        sk = m["strategy_kind"]
        if is_ugh_kind(sk):
            continue

        dir_delta: float | None = None
        close_delta: float | None = None
        mag_delta: float | None = None
        state_delta: float | None = None

        if ugh is not None:
            if m["direction_hit_rate"] is not None and ugh["direction_hit_rate"] is not None:
                dir_delta = round(m["direction_hit_rate"] - ugh["direction_hit_rate"], 4)
            if (
                m["mean_abs_close_error_bp"] is not None
                and ugh["mean_abs_close_error_bp"] is not None
            ):
                close_delta = round(
                    m["mean_abs_close_error_bp"] - ugh["mean_abs_close_error_bp"], 2
                )
            if (
                m["mean_abs_magnitude_error_bp"] is not None
                and ugh["mean_abs_magnitude_error_bp"] is not None
            ):
                mag_delta = round(
                    m["mean_abs_magnitude_error_bp"] - ugh["mean_abs_magnitude_error_bp"], 2
                )
            if (
                m["state_proxy_hit_rate"] is not None
                and ugh["state_proxy_hit_rate"] is not None
            ):
                state_delta = round(
                    m["state_proxy_hit_rate"] - ugh["state_proxy_hit_rate"], 4
                )

        result.append({
            "baseline_strategy_kind": sk,
            "direction_accuracy_delta_vs_ugh": dir_delta,
            "mean_abs_close_error_bp_delta_vs_ugh": close_delta,
            "mean_abs_magnitude_error_bp_delta_vs_ugh": mag_delta,
            "state_proxy_hit_rate_delta_vs_ugh": state_delta,
        })

    return result


# ---------------------------------------------------------------------------
# Annotation-aware monthly metrics
# ---------------------------------------------------------------------------


def compute_monthly_state_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute UGH performance grouped by dominant_state (from labeled observations).

    Pools all UGH-class rows (legacy ``ugh`` + v2 variants); state-engine
    diagnostics are shared across variants.
    """
    ugh_rows = [r for r in observations if is_ugh_kind(r.get("strategy_kind", ""))]
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ugh_rows:
        state = row.get("dominant_state", "") or "unknown"
        groups[state].append(row)

    result: list[dict[str, Any]] = []
    for state in sorted(groups.keys()):
        rows = groups[state]
        n = len(rows)
        dir_hits = count_bool_rows(rows, "direction_hit")
        close_errors = [abs(v) for v in collect_floats(rows, "close_error_bp")]
        result.append({
            "dominant_state": state,
            "forecast_count": n,
            "direction_hit_rate": safe_rate(dir_hits, n),
            "mean_abs_close_error_bp": safe_mean(close_errors),
        })
    return result


def compute_monthly_regime_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute UGH performance grouped by regime_label (confirmed annotations)."""
    return _compute_slice_metrics_for_ugh(observations, "regime_label")


def compute_monthly_volatility_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute UGH performance grouped by volatility_label (confirmed annotations)."""
    return _compute_slice_metrics_for_ugh(observations, "volatility_label")


def compute_monthly_intervention_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute UGH performance grouped by intervention_risk (confirmed annotations)."""
    return _compute_slice_metrics_for_ugh(observations, "intervention_risk")


def compute_monthly_event_tag_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute UGH performance grouped by event_tag (confirmed annotations, expanded).

    Pools all UGH-class rows (legacy ``ugh`` + v2 variants).
    """
    confirmed = [
        r
        for r in observations
        if r.get("annotation_status", "").strip().lower() == "confirmed"
        and is_ugh_kind(r.get("strategy_kind", ""))
    ]
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in confirmed:
        tags_str = row.get("event_tags", "")
        if not tags_str:
            continue
        for tag in tags_str.split("|"):
            tag = tag.strip()
            if tag:
                groups[tag].append(row)

    result: list[dict[str, Any]] = []
    for tag in sorted(groups.keys()):
        rows = groups[tag]
        n = len(rows)
        dir_hits = count_bool_rows(rows, "direction_hit")
        close_errors = [abs(v) for v in collect_floats(rows, "close_error_bp")]
        result.append({
            "event_tag": tag,
            "observation_count": n,
            "direction_hit_rate": safe_rate(dir_hits, n),
            "mean_abs_close_error_bp": safe_mean(close_errors),
        })
    return result


def _compute_slice_metrics_for_ugh(
    observations: list[dict[str, str]],
    field: str,
) -> list[dict[str, Any]]:
    """Compute UGH performance sliced by a labeled dimension (confirmed only)."""
    confirmed = [
        r
        for r in observations
        if r.get("annotation_status", "").strip().lower() == "confirmed"
        and is_ugh_kind(r.get("strategy_kind", ""))
    ]
    non_confirmed = [
        r
        for r in observations
        if r.get("annotation_status", "").strip().lower() != "confirmed"
        and is_ugh_kind(r.get("strategy_kind", ""))
    ]

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in confirmed:
        label = row.get(field, "") or "unknown"
        groups[label].append(row)
    if non_confirmed:
        groups["unlabeled"].extend(non_confirmed)

    result: list[dict[str, Any]] = []
    for label in sorted(groups.keys()):
        rows = groups[label]
        n = len(rows)
        dir_hits = count_bool_rows(rows, "direction_hit")
        close_errors = [abs(v) for v in collect_floats(rows, "close_error_bp")]
        result.append({
            field: label,
            "observation_count": n,
            "direction_hit_rate": safe_rate(dir_hits, n),
            "mean_abs_close_error_bp": safe_mean(close_errors),
        })
    return result


# ---------------------------------------------------------------------------
# Annotation coverage
# ---------------------------------------------------------------------------


def compute_annotation_coverage_summary(
    observations: list[dict[str, str]],
) -> dict[str, Any]:
    """Compute annotation coverage summary for the monthly window."""
    total = len(observations)
    if total == 0:
        return {
            "total_observations": 0,
            "confirmed_count": 0,
            "pending_count": 0,
            "unlabeled_count": 0,
            "annotation_coverage_rate": 0.0,
        }

    confirmed = sum(
        1
        for r in observations
        if r.get("annotation_status", "").strip().lower() == "confirmed"
    )
    pending = sum(
        1
        for r in observations
        if r.get("annotation_status", "").strip().lower() == "pending"
    )
    unlabeled = total - confirmed - pending

    return {
        "total_observations": total,
        "confirmed_count": confirmed,
        "pending_count": pending,
        "unlabeled_count": unlabeled,
        "annotation_coverage_rate": round(confirmed / total, 4) if total > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Provider health monthly summary
# ---------------------------------------------------------------------------


def compute_provider_health_summary(
    health_rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Summarize provider health for the monthly window."""
    if not health_rows:
        return {
            "total_runs": 0,
            "providers": {},
            "provider_usage_count": 0,
            "fallback_adjustment_count": 0,
            "lagged_snapshot_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "provider_mix_summary": [],
        }

    total = len(health_rows)
    providers: dict[str, int] = defaultdict(int)
    fallback_count = 0
    lag_count = 0
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for row in health_rows:
        provider = row.get("provider_name", "unknown")
        providers[provider] += 1

        fb = row.get("used_fallback_adjustment", "").lower()
        if fb in ("true", "1", "yes"):
            fallback_count += 1

        try:
            lag = int(row.get("snapshot_lag_business_days", "0"))
            if lag > 0:
                lag_count += 1
        except (ValueError, TypeError):
            pass

        status = row.get("run_status", "").lower()
        if status in ("success", "ok"):
            success_count += 1
        elif status in ("failed", "error"):
            failed_count += 1
        elif status in ("skipped", "skip", "idempotent_skip"):
            skipped_count += 1

    provider_mix = [
        {"provider": k, "count": v, "share": round(v / total, 4)}
        for k, v in sorted(providers.items())
    ]

    return {
        "total_runs": total,
        "providers": dict(sorted(providers.items())),
        "provider_usage_count": len(providers),
        "fallback_adjustment_count": fallback_count,
        "lagged_snapshot_count": lag_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "provider_mix_summary": provider_mix,
    }


# ---------------------------------------------------------------------------
# Representative cases
# ---------------------------------------------------------------------------


def select_representative_cases(
    observations: list[dict[str, str]],
    max_examples: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select representative success and failure case examples (UGH only).

    Returns (successes, failures) each as a list of case dicts. Pools all
    UGH-class rows (legacy ``ugh`` + v2 variants).
    """
    ugh_rows = [r for r in observations if is_ugh_kind(r.get("strategy_kind", ""))]

    successes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for row in ugh_rows:
        case = {
            "as_of_jst": row.get("as_of_jst", ""),
            "forecast_direction": row.get("forecast_direction", ""),
            "realized_direction": row.get("realized_direction", ""),
            "expected_close_change_bp": row.get("expected_close_change_bp", ""),
            "realized_close_change_bp": row.get("realized_close_change_bp", ""),
            "close_error_bp": row.get("close_error_bp", ""),
            "direction_hit": row.get("direction_hit", ""),
            "dominant_state": row.get("dominant_state", ""),
        }
        if row.get("direction_hit", "").lower() in ("true", "1", "yes"):
            successes.append(case)
        else:
            failures.append(case)

    # Sort successes by smallest close_error (best performance)
    def _sort_key(c: dict[str, Any]) -> float:
        try:
            return abs(float(c.get("close_error_bp", "9999")))
        except (ValueError, TypeError):
            return 9999.0

    successes.sort(key=_sort_key)
    # Sort failures by largest close_error (worst performance)
    failures.sort(key=_sort_key, reverse=True)

    return successes[:max_examples], failures[:max_examples]


# ---------------------------------------------------------------------------
# Review flags
# ---------------------------------------------------------------------------


def compute_review_flags(
    strategy_metrics: list[dict[str, Any]],
    baseline_comparisons: list[dict[str, Any]],
    annotation_coverage: dict[str, Any],
    provider_health: dict[str, Any],
    requested_window_count: int,
    missing_window_count: int,
) -> list[dict[str, str]]:
    """Compute rule-based review flags for the monthly review.

    Each flag is a dict with:
    - flag: the flag identifier
    - reason: human-readable explanation of why the flag was raised

    Flag conditions (thresholds defined as module-level constants):
    1. insufficient_data: UGH forecast_count < THRESHOLD_MINIMUM_OBSERVATIONS
    2. close_error_vs_random_walk: UGH mean close error exceeds random walk by threshold
    3. direction_deficit_vs_technical: UGH direction accuracy is much worse than simple technical
    4. state_hit_but_magnitude_bad: state_proxy_hit_rate is high but magnitude error is also high
    5. low_annotation_coverage: confirmed annotation coverage below threshold
    6. provider_lag_issue: too many lagged snapshots
    7. provider_fallback_issue: too many fallback adjustments
    8. missing_windows: too many missing windows
    """
    flags: list[dict[str, str]] = []

    ugh = _select_canonical_ugh_metrics(strategy_metrics)

    # 1. Insufficient data
    if ugh is None or ugh["forecast_count"] < THRESHOLD_MINIMUM_OBSERVATIONS:
        count = ugh["forecast_count"] if ugh else 0
        flags.append({
            "flag": "insufficient_data",
            "reason": (
                f"UGH forecast count ({count}) is below the minimum threshold "
                f"({THRESHOLD_MINIMUM_OBSERVATIONS}). Review conclusions may be unreliable."
            ),
        })
        # Return early — other flags are not meaningful with insufficient data
        return flags

    # 2. Close error vs random walk
    rw = next(
        (c for c in baseline_comparisons if c["baseline_strategy_kind"] == "baseline_random_walk"),
        None,
    )
    if rw is not None and rw["mean_abs_close_error_bp_delta_vs_ugh"] is not None:
        delta = rw["mean_abs_close_error_bp_delta_vs_ugh"]
        # delta = baseline - UGH; if negative, UGH has higher error (worse)
        if delta < -THRESHOLD_CLOSE_ERROR_VS_RANDOM_WALK_BP:
            flags.append({
                "flag": "inspect_magnitude_mapping",
                "reason": (
                    f"UGH mean abs close error is {abs(delta):.1f} bp worse than "
                    f"baseline_random_walk (threshold: {THRESHOLD_CLOSE_ERROR_VS_RANDOM_WALK_BP} bp). "
                    f"Magnitude mapping may need review."
                ),
            })

    # 3. Direction deficit vs simple technical
    tech = next(
        (
            c
            for c in baseline_comparisons
            if c["baseline_strategy_kind"] == "baseline_simple_technical"
        ),
        None,
    )
    if tech is not None and tech["direction_accuracy_delta_vs_ugh"] is not None:
        delta = tech["direction_accuracy_delta_vs_ugh"]
        # delta = baseline - UGH; if positive, baseline is better
        if delta > THRESHOLD_DIRECTION_DEFICIT_VS_TECHNICAL_PCT:
            flags.append({
                "flag": "inspect_direction_logic",
                "reason": (
                    f"UGH direction accuracy is {delta * 100:.1f} pct points below "
                    f"baseline_simple_technical (threshold: "
                    f"{THRESHOLD_DIRECTION_DEFICIT_VS_TECHNICAL_PCT * 100:.0f}%). "
                    f"Direction logic may need review."
                ),
            })

    # 4. State hit but magnitude bad
    if ugh["state_proxy_hit_rate"] is not None and ugh["mean_abs_magnitude_error_bp"] is not None:
        if (
            ugh["state_proxy_hit_rate"] >= THRESHOLD_STATE_HIT_HIGH
            and ugh["mean_abs_magnitude_error_bp"] > THRESHOLD_MAGNITUDE_ERROR_DESPITE_STATE_HIT_BP
        ):
            flags.append({
                "flag": "inspect_state_mapping",
                "reason": (
                    f"State proxy hit rate ({ugh['state_proxy_hit_rate']:.1%}) is high but "
                    f"magnitude error ({ugh['mean_abs_magnitude_error_bp']:.1f} bp) "
                    f"exceeds threshold ({THRESHOLD_MAGNITUDE_ERROR_DESPITE_STATE_HIT_BP} bp). "
                    f"State-to-magnitude mapping may need review."
                ),
            })

    # 5. Low annotation coverage
    cov_rate = annotation_coverage.get("annotation_coverage_rate", 0.0)
    if cov_rate < THRESHOLD_ANNOTATION_COVERAGE_LOW:
        flags.append({
            "flag": "low_annotation_coverage",
            "reason": (
                f"Confirmed annotation coverage ({cov_rate:.1%}) is below threshold "
                f"({THRESHOLD_ANNOTATION_COVERAGE_LOW:.0%}). "
                f"Regime/volatility/intervention analysis may be unreliable."
            ),
        })

    # 6. Provider lag issue
    total_runs = provider_health.get("total_runs", 0)
    if total_runs > 0:
        lag_rate = provider_health.get("lagged_snapshot_count", 0) / total_runs
        if lag_rate > THRESHOLD_PROVIDER_LAG_RATE:
            flags.append({
                "flag": "provider_quality_issue",
                "reason": (
                    f"Provider lag rate ({lag_rate:.1%}) exceeds threshold "
                    f"({THRESHOLD_PROVIDER_LAG_RATE:.0%}). "
                    f"Lagged snapshots: {provider_health.get('lagged_snapshot_count', 0)}/{total_runs}."
                ),
            })

        # 7. Provider fallback issue
        fb_rate = provider_health.get("fallback_adjustment_count", 0) / total_runs
        if fb_rate > THRESHOLD_PROVIDER_FALLBACK_RATE:
            flags.append({
                "flag": "provider_quality_issue",
                "reason": (
                    f"Provider fallback rate ({fb_rate:.1%}) exceeds threshold "
                    f"({THRESHOLD_PROVIDER_FALLBACK_RATE:.0%}). "
                    f"Fallback adjustments: "
                    f"{provider_health.get('fallback_adjustment_count', 0)}/{total_runs}."
                ),
            })

    # 8. Missing windows
    if requested_window_count > 0:
        missing_rate = missing_window_count / requested_window_count
        if missing_rate > THRESHOLD_MISSING_WINDOW_RATE:
            flags.append({
                "flag": "missing_windows",
                "reason": (
                    f"Missing window rate ({missing_rate:.1%}) exceeds threshold "
                    f"({THRESHOLD_MISSING_WINDOW_RATE:.0%}). "
                    f"Missing: {missing_window_count}/{requested_window_count}."
                ),
            })

    # If no flags fired, the current logic is considered adequate
    if not flags:
        flags.append({
            "flag": "keep_current_logic",
            "reason": (
                "No review flags triggered. "
                "Current logic performance is within acceptable thresholds."
            ),
        })

    return flags


def build_recommendation_summary(
    flags: list[dict[str, str]],
) -> str:
    """Build a structured recommendation summary from review flags.

    Returns a human-readable summary string.
    """
    if not flags:
        return "No review flags. Current logic performance is adequate."

    flag_ids = [f["flag"] for f in flags]

    if flag_ids == ["keep_current_logic"]:
        return (
            "All monthly metrics are within acceptable thresholds. "
            "Recommend keeping current logic unchanged for next period."
        )

    if "insufficient_data" in flag_ids:
        return (
            "Insufficient observation data for reliable monthly assessment. "
            "Recommend continuing data collection before drawing conclusions."
        )

    parts: list[str] = []
    for f in flags:
        fid = f["flag"]
        if fid == "inspect_magnitude_mapping":
            parts.append("Review magnitude/close-error mapping in UGH engine.")
        elif fid == "inspect_direction_logic":
            parts.append("Review direction prediction logic — baseline outperforming.")
        elif fid == "inspect_state_mapping":
            parts.append("Review state-to-magnitude mapping — state hits are good but errors high.")
        elif fid == "low_annotation_coverage":
            parts.append("Increase annotation coverage for reliable regime/volatility analysis.")
        elif fid == "provider_quality_issue":
            parts.append("Investigate provider data quality (lag/fallback rates too high).")
        elif fid == "missing_windows":
            parts.append("Investigate missing protocol windows.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Slice metrics (annotation-aware, all strategies)
# ---------------------------------------------------------------------------


def compute_monthly_slice_metrics(
    observations: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Compute metrics sliced by (strategy_kind x annotation dimension) for monthly review.

    Same structure as weekly slice metrics but over the monthly window.
    """
    from ugh_quantamental.fx_protocol.weekly_reports_v2 import build_slice_metrics

    return build_slice_metrics(observations)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def _stratify_observations_by_versions(
    rows: list[dict[str, str]],
    *,
    theory_version_filter: str | None = None,
    engine_version_filter: str | None = None,
) -> list[dict[str, str]]:
    """Spec §7.5 stratification: filter monthly observations by version columns.

    Auto-detect mode (both filters ``None``): if rows contain more than one
    distinct ``theory_version``, the latest one is selected and a warning
    is logged. Single-version data is returned unchanged. Explicit-filter
    mode drops rows whose column does not match the filter (or whose
    column is missing).
    """
    if theory_version_filter is None and engine_version_filter is None:
        present = {row.get("theory_version", "") for row in rows} - {""}
        if len(present) <= 1:
            return rows
        latest = max(present)
        logger.warning(
            "monthly_review: auto-stratifying mixed theory_versions %s; "
            "filtering to latest=%s",
            sorted(present),
            latest,
        )
        return [r for r in rows if r.get("theory_version", "") == latest]

    filtered = rows
    if theory_version_filter is not None:
        filtered = [
            r for r in filtered if r.get("theory_version", "") == theory_version_filter
        ]
    if engine_version_filter is not None:
        filtered = [
            r for r in filtered if r.get("engine_version", "") == engine_version_filter
        ]
    return filtered


def run_monthly_review(
    observations: list[dict[str, str]],
    health_rows: list[dict[str, str]],
    *,
    pair: str = "USDJPY",
    review_generated_at_jst: datetime | None = None,
    business_day_count: int = 20,
    max_examples: int = 3,
    include_annotations: bool = True,
    theory_version_filter: str | None = None,
    engine_version_filter: str | None = None,
) -> dict[str, Any]:
    """Generate a monthly review from pre-loaded observations and provider health data.

    This is the pure entry point — no file I/O, no engine re-execution.
    All data must be pre-loaded and passed in.

    Parameters
    ----------
    observations:
        Labeled observation rows filtered to the monthly window.
    health_rows:
        Provider health rows filtered to the monthly window.
    pair:
        Currency pair (default: USDJPY).
    review_generated_at_jst:
        Timestamp for the review. Defaults to now(JST).
    business_day_count:
        Number of business days in the monthly window (default: 20).
    max_examples:
        Maximum representative success/failure examples to include.
    include_annotations:
        Whether to include annotation-aware metrics (default: True).
    theory_version_filter:
        Optional ``theory_version`` filter; ``None`` auto-detects (filters
        a mixed-version window to its latest version with a warning).
        Spec §7.5: required to keep v1 and v2 records from being mixed
        under shared ``strategy_kind`` values across the boundary month.
    engine_version_filter:
        Optional ``engine_version`` filter; same behavior as above.

    Returns
    -------
    dict[str, Any]
        The full monthly review result, suitable for JSON serialization.
    """
    if review_generated_at_jst is None:
        review_generated_at_jst = datetime.now(_JST)

    # Spec §7.5 stratification — applied before any per-strategy aggregation
    # so version mixing cannot leak into baseline-vs-UGH deltas or review flags.
    observations = _stratify_observations_by_versions(
        observations,
        theory_version_filter=theory_version_filter,
        engine_version_filter=engine_version_filter,
    )

    # Count unique as_of dates in observations to determine included/missing windows
    seen_dates: set[str] = set()
    for row in observations:
        as_of = row.get("as_of_jst", "")
        date_str = as_of[:10].replace("-", "") if len(as_of) >= 10 else ""
        if date_str:
            seen_dates.add(date_str)

    included_window_count = len(seen_dates)
    missing_window_count = max(0, business_day_count - included_window_count)

    # Strategy metrics
    strategy_metrics = compute_monthly_strategy_metrics(observations)

    # Baseline comparisons
    baseline_comparisons = compute_monthly_baseline_comparisons(strategy_metrics)

    # State metrics
    state_metrics = compute_monthly_state_metrics(observations)

    # Annotation-aware metrics
    regime_metrics: list[dict[str, Any]] = []
    volatility_metrics: list[dict[str, Any]] = []
    intervention_metrics: list[dict[str, Any]] = []
    event_tag_metrics: list[dict[str, Any]] = []
    annotation_coverage: dict[str, Any] = compute_annotation_coverage_summary(observations)

    if include_annotations:
        regime_metrics = compute_monthly_regime_metrics(observations)
        volatility_metrics = compute_monthly_volatility_metrics(observations)
        intervention_metrics = compute_monthly_intervention_metrics(observations)
        event_tag_metrics = compute_monthly_event_tag_metrics(observations)

    # Provider health
    provider_health = compute_provider_health_summary(health_rows)

    # Representative cases
    successes, failures = select_representative_cases(observations, max_examples)

    # Review flags
    review_flags = compute_review_flags(
        strategy_metrics,
        baseline_comparisons,
        annotation_coverage,
        provider_health,
        requested_window_count=business_day_count,
        missing_window_count=missing_window_count,
    )

    # Recommendation summary
    recommendation = build_recommendation_summary(review_flags)

    # Stratification audit fields: which version values survived the filter.
    theory_versions_in_window = sorted(
        {row.get("theory_version", "") for row in observations} - {""}
    )
    engine_versions_in_window = sorted(
        {row.get("engine_version", "") for row in observations} - {""}
    )

    return {
        "review_version": "v1",
        "pair": pair,
        "review_generated_at_jst": review_generated_at_jst.isoformat(),
        "requested_window_count": business_day_count,
        "included_window_count": included_window_count,
        "missing_window_count": missing_window_count,
        "theory_versions_in_window": theory_versions_in_window,
        "engine_versions_in_window": engine_versions_in_window,
        "monthly_strategy_metrics": strategy_metrics,
        "monthly_baseline_comparisons": baseline_comparisons,
        "monthly_state_metrics": state_metrics,
        "monthly_regime_metrics": regime_metrics,
        "monthly_volatility_metrics": volatility_metrics,
        "monthly_intervention_metrics": intervention_metrics,
        "monthly_event_tag_metrics": event_tag_metrics,
        "provider_health_summary": provider_health,
        "annotation_coverage_summary": annotation_coverage,
        "recommendation_summary": recommendation,
        "review_flags": review_flags,
        "representative_successes": successes,
        "representative_failures": failures,
        "generated_artifact_paths": [],
    }
