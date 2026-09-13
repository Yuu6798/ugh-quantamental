#!/usr/bin/env python3
"""Replay-based post-shock ``e_star`` transition-lag analysis (FX-ESTAR-LAG).

Read-only, deterministic, no network calls. Replays the persisted
``history/{date}/{batch_id}/input_snapshot.json`` artifacts of the
``fx-daily-data`` branch through the existing, unmodified
``compute_snapshot_statistics`` -> ``derive_*`` -> projection-engine pipeline
to locate what rate-limits the post-shock ``e_star`` sign transition, per
UGH v2 variant.

Every date window is a CLI argument; the defaults reproduce the 2026-08 run.

Two outputs:

1. A descriptive daily feature/score/engine-output series over the analysis
   window (``daily_series.csv`` / ``.md``), one row per (variant, day) with
   every v2 variant replayed under its own config, plus per-variant baseline
   ``e_star`` transition dates (``variant_baseline.csv``,
   ``transitions_baseline.csv``).

   Each row carries ``pre_expansion_close_change_bp`` and its three factors
   (``e_star``, ``trailing_mean_abs_change_bp``, ``conviction_factor``).
   That product, not raw ``e_star``, is what the FLAT epsilon is compared
   against in ``forecasting.py``, so a direction collapsing to flat can be
   attributed to whichever factor actually moved.
2. An ablation grid (``ablation.csv`` / ``.md``) over three axes, for variants
   alpha / beta / delta and two reference values (pre-shock mean, neutral
   0.0), recording each transition-date shift versus the unablated baseline:

   - ``statistic``: one raw statistic (``spot_vs_sma20``, ``momentum_5d``,
     ``prev_close_change_bp`` numerator) is held at the reference value and
     the whole statistics -> request path is rebuilt.
   - ``estar_term``: one argument ``compute_e_raw`` or ``compute_gravity_bias``
     actually consumes -- ``u_score``, ``technical_score``,
     ``price_implied_score``, ``fire_probability``, ``alignment`` and the three
     gravity terms. **This is the axis that isolates a single term of
     ``e_star``.** ``u_score`` and ``alignment`` are engine intermediates, so
     they are substituted after the engine derives them.
   - ``signal_feature``: ``fundamental_score`` / ``technical_score``, which are
     upstream of those terms rather than terms themselves -- both feed
     ``compute_u``, and ``technical_score`` also appears directly in
     ``direction_signal``, so overriding either moves more than one term. Read
     it as "which signal did the engine see differently", never as an
     isolation.

   Candidates are ranked within an axis, never across them.

``summary.json`` also reports clamp-saturation day counts and the missing
snapshot dates (2026-08-28 is expected to be missing; it is skipped and
noted, never backfilled).

Never reconstructs inputs from OHLC history CSVs: ``current_spot`` in
``input_snapshot.json`` is a separate feed (``data_sources.py``'s spot path)
from the completed-window closes, so a CSV-based reconstruction would not
match what production actually forecast on.

Usage
-----
    python scripts/analyze_estar_lag.py \\
        --fxdata-dir /path/to/fxdata/csv \\
        --out-dir /path/to/output

``--fxdata-dir`` must contain a ``history/`` directory in the
``history/{YYYYMMDD}/{batch_id}/input_snapshot.json`` layout produced by
``observability.publish_observability_to_layout``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

# ---------------------------------------------------------------------------
# Analysis window constants (spec: docs/briefs/2026-08_FX-ESTAR-LAG.md)
# ---------------------------------------------------------------------------

#: Defaults reproduce the 2026-08 run (brief: docs/briefs/2026-08_FX-ESTAR-LAG.md).
#: Every one of them is overridable from the CLI so a later month can be
#: analysed without editing this file.
#:
#: Descriptive / stats-collection window. 2026-08-28 is expected missing.
DEFAULT_ANALYSIS_START = date(2026, 7, 22)
DEFAULT_ANALYSIS_END = date(2026, 8, 28)

#: Transition-search window: lower bound is the shock day itself; a positive
#: value on or before this date is never a valid transition candidate.
DEFAULT_SEARCH_START = date(2026, 7, 30)
DEFAULT_SEARCH_END = DEFAULT_ANALYSIS_END

#: Pre-shock reference window: last 5 business days before the shock.
DEFAULT_PRE_SHOCK_REF_DATES = (
    date(2026, 7, 23),
    date(2026, 7, 24),
    date(2026, 7, 27),
    date(2026, 7, 28),
    date(2026, 7, 29),
)

#: The shock day itself. Used both as the transition-search lower bound and to
#: flag whether a day's trailing-20 window still contains the shock.
DEFAULT_SHOCK_DAY = DEFAULT_SEARCH_START


@dataclass(frozen=True)
class AnalysisWindows:
    """The date windows one analysis run operates over.

    Held together rather than passed as loose dates because they are mutually
    constrained: the search window must sit inside the analysis window, the
    pre-shock reference days must precede the shock, and the shock day is the
    search window's lower bound in the default configuration.
    """

    analysis_start: date = DEFAULT_ANALYSIS_START
    analysis_end: date = DEFAULT_ANALYSIS_END
    search_start: date = DEFAULT_SEARCH_START
    search_end: date = DEFAULT_SEARCH_END
    shock_day: date = DEFAULT_SHOCK_DAY
    pre_shock_ref_dates: tuple[date, ...] = DEFAULT_PRE_SHOCK_REF_DATES

    def validate(self) -> None:
        """Raise ``ValueError`` if the windows are not mutually consistent."""
        if self.analysis_start > self.analysis_end:
            raise ValueError("analysis_start must not be after analysis_end")
        if self.search_start > self.search_end:
            raise ValueError("search_start must not be after search_end")
        if self.search_start < self.analysis_start or self.search_end > self.analysis_end:
            raise ValueError("the search window must lie within the analysis window")
        if not self.pre_shock_ref_dates:
            raise ValueError("at least one pre-shock reference date is required")
        late = [d for d in self.pre_shock_ref_dates if d >= self.shock_day]
        if late:
            raise ValueError(
                "pre-shock reference dates must precede the shock day: "
                f"{[d.isoformat() for d in late]}"
            )
        early = [d for d in self.pre_shock_ref_dates if d < self.analysis_start]
        if early:
            raise ValueError(
                "pre-shock reference dates must lie within the analysis window: "
                f"{[d.isoformat() for d in early]}"
            )

#: Raw statistics eligible for ablation, and which downstream score each
#: nominally maps to (documentation only — the ablation always rebuilds the
#: full statistics -> request path, not just the named score).
ABLATION_STATS: tuple[str, ...] = (
    "spot_vs_sma20",
    "momentum_5d",
    "prev_close_change_bp",
)

#: The arguments ``compute_e_raw`` and ``compute_gravity_bias`` actually
#: consume, each held at a reference value one at a time. This is the axis that
#: answers "which term of e_star carried the move".
#:
#: ``u_score`` and ``alignment`` are engine intermediates rather than
#: ``SignalFeatures`` fields, so they are overridden after the engine computes
#: them (see ``_replay_projection``):
#:
#:  - direction_signal = (u_weight*u_score + t_weight*technical_score
#:    + p_weight*price_implied_score) / sum(weights);
#:  - conviction_multiplier is driven by fire_probability;
#:  - alignment multiplies the whole product, and also feeds conviction;
#:  - grv_lock / regime_fit / narrative_dispersion are the gravity terms.
ABLATION_ESTAR_TERMS: tuple[str, ...] = (
    "u_score",
    "technical_score",
    "price_implied_score",
    "fire_probability",
    "alignment",
    "grv_lock",
    "regime_fit",
    "narrative_dispersion",
)

#: Terms above that are engine intermediates, not SignalFeatures fields.
_ESTAR_INTERMEDIATE_TERMS: frozenset[str] = frozenset({"u_score", "alignment"})

#: SignalFeatures fields read by compute_e_raw, and by compute_gravity_bias.
_E_RAW_SIGNAL_TERMS: frozenset[str] = frozenset(
    {"technical_score", "price_implied_score", "fire_probability"}
)
_GRAVITY_SIGNAL_TERMS: frozenset[str] = frozenset(
    {"grv_lock", "regime_fit", "narrative_dispersion"}
)

#: The "neutral" reference is per term, because these terms are not all signed
#: quantities whose no-contribution value is zero:
#:
#:  - ``alignment`` multiplies the whole directional product and lives in
#:    [0, 1]; zero means total disagreement and forces e_raw to 0 on every
#:    day, which mechanically ranks it as the rate limiter instead of
#:    measuring what carried the transition. Its identity is 1.0, which is
#:    also what compute_alignment returns when no pair carries weight.
#:  - ``fire_probability`` is a probability; its no-information value is 0.5.
#:
#: Everything else contributes additively and is genuinely neutral at 0.0.
NEUTRAL_TERM_REFERENCES: dict[str, float] = {
    "alignment": 1.0,
    "fire_probability": 0.5,
}

#: ``SignalFeatures`` fields that are upstream of the terms above rather than
#: terms themselves. ``fundamental_score`` and ``technical_score`` both feed
#: ``compute_u``, and ``technical_score`` additionally appears directly in
#: ``direction_signal``, so overriding either one moves more than a single
#: e_star term. Kept as a separate, separately-ranked axis: useful for "which
#: signal did the engine read differently", never read as an isolation.
ABLATION_SIGNAL_FEATURES: tuple[str, ...] = (
    "fundamental_score",
    "technical_score",
)

#: Variants included in the ablation grid (brief: alpha, beta, delta — gamma
#: is included in the descriptive baseline table only, for the full 4-variant
#: picture, since alpha and gamma share direction weights and only differ in
#: conviction_floor).
ABLATION_VARIANT_NAMES: tuple[str, ...] = ("ugh_v2_alpha", "ugh_v2_beta", "ugh_v2_delta")

#: All four v2 variants, for the descriptive baseline table.
ALL_VARIANT_NAMES: tuple[str, ...] = (
    "ugh_v2_alpha",
    "ugh_v2_beta",
    "ugh_v2_gamma",
    "ugh_v2_delta",
)

REFERENCE_KINDS: tuple[str, ...] = ("pre_shock_mean", "neutral")

_MIN_TRAILING_WINDOWS = 20


# ---------------------------------------------------------------------------
# Transition extraction (pure function; unit-tested with synthetic series)
# ---------------------------------------------------------------------------

ALWAYS_POSITIVE_POST_SHOCK = "ALWAYS_POSITIVE_POST_SHOCK"
NO_POST_SHOCK_RECOVERY = "NO_POST_SHOCK_RECOVERY"
SUSTAINED_POSITIVE = "SUSTAINED_POSITIVE"
CROSSED_POSITIVE = "CROSSED_POSITIVE"


@dataclass(frozen=True)
class Transition:
    """One extracted transition-date result.

    ``date`` is an ISO ``YYYY-MM-DD`` string, or ``None`` for the two special
    outcomes (``label`` explains why).
    """

    label: str
    date: str | None


def extract_transitions(series: list[tuple[str, float]]) -> tuple[Transition, Transition]:
    """Extract (primary, secondary) transition dates from an ``e_star`` series.

    ``series`` must already be restricted to the search window
    ``[SEARCH_START, SEARCH_END]`` (inclusive), sorted ascending by date, with
    dates before the search window excluded — pre-shock positive values are
    never eligible as a fallback transition.

    Primary = "first sustained positive crossing": the first day satisfying
    the crossing condition (positive value, with at least one ``<= 0``
    observation strictly earlier in the window) after which the series
    stays positive for every remaining day through the window end.

    Secondary = "first crossing" (single-day OK): the first day satisfying
    the crossing condition, regardless of what happens afterward. In a
    multi-crossing series (e.g. an intermittent positive turn followed by a
    reversion, then a later sustained turn) primary and secondary diverge.

    Special outcomes (both primary and secondary share the label, date=None):

    - ``ALWAYS_POSITIVE_POST_SHOCK``: no day in the window is ``<= 0`` at
      all — there is nothing to transition away from; the lag is reported as
      eliminated, not as a (falsely early) transition date.
    - ``NO_POST_SHOCK_RECOVERY``: the series is ``<= 0`` for the window's
      final day — it dipped ``<= 0`` at some point (with or without an
      intervening crossing) and never held positive through the window end.

    Parameters
    ----------
    series:
        Ascending ``(iso_date, value)`` pairs, already filtered to the
        search window.

    Returns
    -------
    tuple[Transition, Transition]
        ``(primary, secondary)``.
    """
    if not series:
        raise ValueError("series must not be empty")

    any_non_positive = any(value <= 0 for _, value in series)
    if not any_non_positive:
        t = Transition(ALWAYS_POSITIVE_POST_SHOCK, None)
        return t, t

    final_value = series[-1][1]
    if final_value <= 0:
        t = Transition(NO_POST_SHOCK_RECOVERY, None)
        return t, t

    # Secondary: first day that is positive with >=1 strictly-earlier <=0
    # observation in the window (single-day crossing is acceptable).
    seen_non_positive = False
    secondary_date: str | None = None
    for iso_date, value in series:
        if value > 0:
            if seen_non_positive:
                secondary_date = iso_date
                break
        else:
            seen_non_positive = True
    secondary = Transition(CROSSED_POSITIVE, secondary_date)

    # Primary: the start of the final contiguous positive run. Guaranteed to
    # be preceded by a <=0 observation because any_non_positive is True and
    # final_value > 0 (the dip cannot be *after* the final run).
    idx = len(series) - 1
    while idx > 0 and series[idx - 1][1] > 0:
        idx -= 1
    primary = Transition(SUSTAINED_POSITIVE, series[idx][0])

    return primary, secondary


def business_day_shift(
    baseline: Transition, ablated: Transition, dates_in_order: list[str]
) -> int | None:
    """Shift (in business days, +earlier is negative) of *ablated* vs *baseline*.

    Both transitions must be resolved to an actual date (not a special
    label) to compute a numeric shift; otherwise returns ``None`` — the
    caller reports the special-label combination as text instead.
    """
    if baseline.date is None or ablated.date is None:
        return None
    return dates_in_order.index(ablated.date) - dates_in_order.index(baseline.date)


# ---------------------------------------------------------------------------
# Business-day / snapshot I/O helpers
# ---------------------------------------------------------------------------


def business_days(start: date, end: date) -> list[date]:
    """Return every Mon-Fri calendar date in ``[start, end]`` inclusive."""
    days: list[date] = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def find_snapshot_path(fxdata_dir: str, day: date) -> str | None:
    """Locate ``history/{YYYYMMDD}/{batch_id}/input_snapshot.json`` for *day*.

    Returns ``None`` if the date directory does not exist (missing snapshot —
    caller must skip and note, never backfill from OHLC CSVs).
    """
    date_dir = os.path.join(fxdata_dir, "history", day.strftime("%Y%m%d"))
    if not os.path.isdir(date_dir):
        return None
    batch_dirs = sorted(
        entry for entry in os.listdir(date_dir) if os.path.isdir(os.path.join(date_dir, entry))
    )
    if not batch_dirs:
        return None
    # A date can hold more than one batch directory: outcome catch-up
    # republishes a recovered PRIOR batch (whose dir has no
    # input_snapshot.json) alongside the day's own batch. Search every batch
    # dir for the snapshot instead of taking batch_dirs[0], preferring the
    # batch whose id embeds this date (the day's own forecast batch).
    candidates = [
        os.path.join(date_dir, entry, "input_snapshot.json")
        for entry in batch_dirs
        if os.path.isfile(os.path.join(date_dir, entry, "input_snapshot.json"))
    ]
    if not candidates:
        return None
    date_token = os.path.basename(date_dir)
    for path in candidates:
        if date_token in os.path.basename(os.path.dirname(path)):
            return path
    return candidates[0]


def load_market_snapshot(path: str) -> Any:
    """Read back ``input_snapshot.json`` into an ``FxProtocolMarketSnapshot``.

    This is the read-back counterpart of ``observability.build_input_snapshot``:
    every field written there is consumed here, with no OHLC-CSV
    reconstruction and no recomputation of engine values.
    """
    from ugh_quantamental.fx_protocol.data_models import (
        FxCompletedWindow,
        FxProtocolMarketSnapshot,
    )
    from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    windows = tuple(
        FxCompletedWindow(
            window_start_jst=w["window_start_jst"],
            window_end_jst=w["window_end_jst"],
            open_price=w["open_price"],
            high_price=w["high_price"],
            low_price=w["low_price"],
            close_price=w["close_price"],
        )
        for w in raw["completed_windows"]
    )
    prov = raw["market_data_provenance"]
    provenance = MarketDataProvenance(
        vendor=prov["vendor"],
        feed_name=prov["feed_name"],
        price_type=prov["price_type"],
        resolution=prov["resolution"],
        timezone=prov["timezone"],
        retrieved_at_utc=prov["retrieved_at_utc"],
    )
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair(raw["pair"]),
        as_of_jst=raw["as_of_jst"],
        current_spot=raw["current_spot"],
        completed_windows=windows,
        market_data_provenance=provenance,
    )


# ---------------------------------------------------------------------------
# Per-day replay
# ---------------------------------------------------------------------------


@dataclass
class DayReplay:
    """One day's replay result: raw stats, derived scores, engine output."""

    day: date
    stats: dict[str, float]
    fundamental_score: float
    technical_score: float
    price_implied_score: float
    fire_probability: float
    #: The full SignalFeatures actually handed to the engine (after any
    #: override).  Held whole so every e_star input term is reachable for
    #: reference means, not just the handful mirrored above.
    signal_features: Any
    #: Engine intermediates, not SignalFeatures fields: compute_e_raw consumes
    #: both directly, so both are ablation terms in their own right.
    u_score: float
    alignment: float
    e_raw: float
    gravity_bias: float
    e_star: float
    conviction: float
    #: mean |close change| over the trailing 20 windows, in bp.  Production
    #: names this trailing_mean_abs_close_change_bp on BaselineContext; the
    #: statistics dict calls the same quantity trailing_mean_abs_change_bp.
    trailing_mean_abs_close_change_bp: float
    #: 0.5 + 0.5 * conviction -- the magnitude shrink applied before expansion.
    conviction_factor: float
    #: e_star * trailing_mean_abs_close_change_bp * conviction_factor.  This,
    #: not raw e_star, is what the FLAT epsilon is compared against
    #: (forecasting.py); a direction collapses to flat when its absolute value
    #: falls to or below the epsilon, a fixed 3.0bp under v2.6.
    pre_expansion_close_change_bp: float
    shock_window_in_trailing20: bool


def _estar_term_value(replay: DayReplay, name: str) -> float:
    """Return one e_star term's value from a replay.

    ``u_score`` and ``alignment`` are engine intermediates recorded on the
    replay; every other term is a ``SignalFeatures`` field.
    """
    if name in _ESTAR_INTERMEDIATE_TERMS:
        return float(getattr(replay, name))
    return float(getattr(replay.signal_features, name))


def _replay_projection(req: Any, config: Any, term_override: dict[str, float] | None):
    """Run the projection engine, optionally overriding one term of e_star.

    ``run_projection_engine`` takes features, not the terms it derives from
    them, so an e_star term cannot be substituted through its signature. With
    no override this delegates to the engine outright.

    With one, the same published engine functions are recomposed in the same
    order and the override is applied **at the point each term is consumed**,
    never on the request:

    * ``u_score`` and ``alignment`` replace the engine's own intermediates;
    * ``technical_score`` / ``price_implied_score`` / ``fire_probability``
      replace the values ``compute_e_raw`` reads, while ``compute_u`` still
      sees the original features -- otherwise overriding ``technical_score``
      would move ``u_score`` too and the result would not isolate one term;
    * the three gravity terms replace what ``compute_gravity_bias`` reads.

    The unablated recomposition is checked against the engine on every call, so
    a change to the engine's composition fails here rather than quietly
    producing a different analysis.
    """
    from ugh_quantamental.engine.projection import (
        compute_alignment,
        compute_conviction,
        compute_e_raw,
        compute_e_star,
        compute_gravity_bias,
        compute_mismatch_px,
        compute_mismatch_sem,
        compute_u,
        run_projection_engine,
    )

    proj = req.projection
    engine_result = run_projection_engine(
        projection_id=proj.projection_id,
        horizon_days=proj.horizon_days,
        question_features=proj.question_features,
        signal_features=proj.signal_features,
        alignment_inputs=proj.alignment_inputs,
        config=config,
    )
    if not term_override:
        return engine_result

    qf, sf, cfg = proj.question_features, proj.signal_features, config

    # compute_u always reads the ORIGINAL features: the direction terms are
    # overridden only where compute_e_raw consumes them.
    u_score = term_override.get("u_score", compute_u(qf, sf, cfg))
    alignment = term_override.get(
        "alignment", compute_alignment(proj.alignment_inputs, cfg)
    )

    e_raw_fields = {
        name: value
        for name, value in term_override.items()
        if name in _E_RAW_SIGNAL_TERMS
    }
    sf_for_e_raw = sf.model_copy(update=e_raw_fields) if e_raw_fields else sf

    gravity_fields = {
        name: value
        for name, value in term_override.items()
        if name in _GRAVITY_SIGNAL_TERMS
    }
    sf_for_gravity = sf.model_copy(update=gravity_fields) if gravity_fields else sf

    e_raw = compute_e_raw(u_score, sf_for_e_raw, alignment, cfg)
    gravity_bias = compute_gravity_bias(sf_for_gravity, cfg)
    e_star = compute_e_star(e_raw, gravity_bias)
    mismatch_px = compute_mismatch_px(e_star, sf)
    mismatch_sem = compute_mismatch_sem(qf, sf)
    conviction = compute_conviction(sf, alignment, mismatch_px, mismatch_sem)

    # Same inputs as the engine except for the override: the un-overridden
    # path must reproduce it, or this recomposition has drifted.
    check_e_star = compute_e_star(
        compute_e_raw(
            compute_u(qf, sf, cfg), sf, compute_alignment(proj.alignment_inputs, cfg), cfg
        ),
        compute_gravity_bias(sf, cfg),
    )
    if abs(check_e_star - engine_result.e_star) > 1e-12:
        raise RuntimeError(
            "the ablation recomposition no longer matches run_projection_engine "
            f"({check_e_star} vs {engine_result.e_star}); update _replay_projection"
        )

    return SimpleNamespace(
        u_score=u_score,
        alignment=alignment,
        e_raw=e_raw,
        gravity_bias=gravity_bias,
        e_star=e_star,
        conviction=conviction,
    )


def compute_day_replay(
    snapshot: Any,
    *,
    snapshot_ref: str,
    config: Any,
    shock_day: date,
    stats_override: dict[str, float] | None = None,
    signal_feature_override: dict[str, float] | None = None,
    estar_term_override: dict[str, float] | None = None,
) -> DayReplay:
    """Rebuild the full statistics -> request -> projection path for one day.

    When *stats_override* is given, the named raw statistics are substituted
    before any derivation happens, and the entire path — including
    ``derive_question_features`` (the second consumer of ``momentum_5d``) —
    is rebuilt from the overridden dict via
    ``market_ugh_builder.build_ugh_request_from_snapshot``'s ``stats``
    injection point. No partially-built request is patched afterward.

    When *signal_feature_override* is given, the named ``SignalFeatures``
    fields are replaced on the built request instead. That is a strictly later
    injection point than ``stats_override`` and is deliberately so: these are
    the terms ``compute_e_raw`` and ``compute_gravity_bias`` consume directly,
    so overriding them isolates one input to e_star rather than one raw
    statistic that several derived scores share. Use the statistics axis to
    ask "which market measurement moved the call", and the signal-feature axis
    to ask "which signal did the engine read differently".

    When *estar_term_override* is given, one argument that ``compute_e_raw`` or
    ``compute_gravity_bias`` actually consumes is substituted -- including
    ``u_score`` and ``alignment``, which the engine derives internally and so
    cannot be reached through the request. That is the axis that isolates a
    single term of e_star; the two SignalFeatures above do not, because both
    feed ``compute_u`` and ``technical_score`` additionally appears in
    ``direction_signal``.
    """
    from ugh_quantamental.fx_protocol.market_ugh_builder import (
        build_ugh_request_from_snapshot,
        compute_snapshot_statistics,
    )

    base_stats = compute_snapshot_statistics(snapshot)
    stats = dict(base_stats)
    if stats_override:
        stats.update(stats_override)

    req = build_ugh_request_from_snapshot(snapshot, snapshot_ref=snapshot_ref, stats=stats)

    sf = req.projection.signal_features
    if signal_feature_override:
        unknown = set(signal_feature_override) - set(type(sf).model_fields)
        if unknown:
            raise ValueError(f"Unknown SignalFeatures field(s): {sorted(unknown)}")
        sf = sf.model_copy(update=dict(signal_feature_override))

    if sf is not req.projection.signal_features:
        req = req.model_copy(
            update={"projection": req.projection.model_copy(update={"signal_features": sf})}
        )
    result = _replay_projection(req, config, estar_term_override)

    trailing = snapshot.completed_windows[-_MIN_TRAILING_WINDOWS:]
    shock_in_window = any(
        w.window_start_jst.date() == shock_day for w in trailing
    )

    # Reproduce the pre-expansion magnitude exactly as forecasting.py does, so
    # the FLAT decision can be decomposed into its three factors.
    trailing_mean_abs = float(stats["trailing_mean_abs_change_bp"])
    conviction_factor = 0.5 + 0.5 * result.conviction
    return DayReplay(
        day=snapshot.as_of_jst.date(),
        stats=stats,
        fundamental_score=sf.fundamental_score,
        technical_score=sf.technical_score,
        price_implied_score=sf.price_implied_score,
        fire_probability=sf.fire_probability,
        signal_features=sf,
        u_score=result.u_score,
        alignment=result.alignment,
        e_raw=result.e_raw,
        gravity_bias=result.gravity_bias,
        e_star=result.e_star,
        conviction=result.conviction,
        trailing_mean_abs_close_change_bp=trailing_mean_abs,
        conviction_factor=conviction_factor,
        pre_expansion_close_change_bp=(
            result.e_star * trailing_mean_abs * conviction_factor
        ),
        shock_window_in_trailing20=shock_in_window,
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _variant_config(variant_name: str) -> Any:
    from ugh_quantamental.engine.projection_models import ProjectionConfig
    from ugh_quantamental.fx_protocol.forecasting import _UGH_V2_VARIANT_CONFIGS
    from ugh_quantamental.fx_protocol.models import StrategyKind

    overrides = _UGH_V2_VARIANT_CONFIGS[StrategyKind(variant_name)]
    return ProjectionConfig(**overrides)


def run_analysis(
    fxdata_dir: str,
    out_dir: str,
    windows: AnalysisWindows | None = None,
) -> dict[str, Any]:
    """Run the full FX-ESTAR-LAG replay analysis and write outputs to *out_dir*.

    Returns the summary dict that is also written to ``summary.json``.
    """
    from ugh_quantamental.fx_protocol.csv_utils import write_csv_rows

    windows = windows or AnalysisWindows()
    windows.validate()

    all_days = business_days(windows.analysis_start, windows.analysis_end)

    snapshots: dict[date, Any] = {}
    missing_dates: list[str] = []
    for day in all_days:
        path = find_snapshot_path(fxdata_dir, day)
        if path is None:
            missing_dates.append(day.isoformat())
            continue
        snapshots[day] = load_market_snapshot(path)

    present_days = [d for d in all_days if d in snapshots]
    if not present_days:
        raise RuntimeError(f"No input_snapshot.json files found under {fxdata_dir}")

    # ------------------------------------------------------------------
    # 1. Descriptive daily series, one row per (variant, day).
    #
    # This used to emit alpha only, under the default ProjectionConfig. That
    # cannot show a day where the variants disagree -- 2026-09-11, where
    # alpha/gamma stayed down while beta/delta went flat, is exactly the case
    # the decomposition needs to follow -- so every variant is replayed under
    # its own config and the rows carry the variant.
    # ------------------------------------------------------------------
    daily_rows: list[dict[str, Any]] = []
    #: Keyed by variant then day. The pre-shock reference means below are
    #: taken from alpha, whose config is the default one, keeping those
    #: reference values identical to the previous behaviour.
    daily_replays_by_variant: dict[str, dict[date, DayReplay]] = {}
    for variant_name in ALL_VARIANT_NAMES:
        cfg = _variant_config(variant_name)
        per_day: dict[date, DayReplay] = {}
        for day in present_days:
            replay = compute_day_replay(
                snapshots[day],
                snapshot_ref=f"{variant_name}-{day.isoformat()}",
                config=cfg,
                shock_day=windows.shock_day,
            )
            per_day[day] = replay
            saturated = abs(replay.stats["spot_vs_sma20"] * 100.0) >= 1.0
            daily_rows.append(
                {
                    "variant": variant_name,
                    "date": day.isoformat(),
                    "spot_vs_sma20": replay.stats["spot_vs_sma20"],
                    "momentum_5d": replay.stats["momentum_5d"],
                    "prev_close_change_bp": replay.stats["prev_close_change_bp"],
                    "trailing_mean_abs_change_bp": (
                        replay.stats["trailing_mean_abs_change_bp"]
                    ),
                    "fundamental_score": replay.fundamental_score,
                    "technical_score": replay.technical_score,
                    "price_implied_score": replay.price_implied_score,
                    "fire_probability": replay.fire_probability,
                    "u_score": replay.u_score,
                    "alignment": replay.alignment,
                    "e_raw": replay.e_raw,
                    "gravity_bias": replay.gravity_bias,
                    "e_star": replay.e_star,
                    "conviction": replay.conviction,
                    "conviction_factor": replay.conviction_factor,
                    "pre_expansion_close_change_bp": (
                        replay.pre_expansion_close_change_bp
                    ),
                    "fundamental_score_clamp_saturated": saturated,
                    "shock_window_in_trailing20": replay.shock_window_in_trailing20,
                }
            )
        daily_replays_by_variant[variant_name] = per_day

    daily_replays = daily_replays_by_variant["ugh_v2_alpha"]

    daily_fieldnames = (
        "variant",
        "date",
        "spot_vs_sma20",
        "momentum_5d",
        "prev_close_change_bp",
        "trailing_mean_abs_change_bp",
        "fundamental_score",
        "technical_score",
        "price_implied_score",
        "fire_probability",
        "u_score",
        "alignment",
        "e_raw",
        "gravity_bias",
        "e_star",
        "conviction",
        "conviction_factor",
        "pre_expansion_close_change_bp",
        "fundamental_score_clamp_saturated",
        "shock_window_in_trailing20",
    )
    write_csv_rows(os.path.join(out_dir, "daily_series.csv"), daily_rows, daily_fieldnames)
    _write_markdown_table(
        os.path.join(out_dir, "daily_series.md"),
        "Daily feature / engine-output series (all v2 variants, each under its own config)",
        daily_fieldnames,
        daily_rows,
        missing_dates,
    )

    # Both aggregations below read a single chronological series, so they take
    # the alpha rows rather than daily_rows: the latter is now grouped by
    # variant, and walking it would jump back in time at each variant boundary
    # (fabricating sign changes) and repeat every saturated date four times.
    # Alpha also keeps these two summary fields identical to the values the
    # 2026-08 single-variant run produced.
    alpha_rows = [row for row in daily_rows if row["variant"] == "ugh_v2_alpha"]

    # Sign-change (negative<->positive) day lists per raw feature series.
    sign_changes = {
        name: _sign_change_days(alpha_rows, name)
        for name in ("fundamental_score", "technical_score", "price_implied_score", "e_star")
    }

    clamp_saturated_dates = [
        row["date"] for row in alpha_rows if row["fundamental_score_clamp_saturated"]
    ]

    # ------------------------------------------------------------------
    # 2. Pre-shock reference means (raw statistics, actual replayed values).
    # ------------------------------------------------------------------
    pre_shock_days = [d for d in windows.pre_shock_ref_dates if d in daily_replays]
    if len(pre_shock_days) != len(windows.pre_shock_ref_dates):
        missing_ref = sorted(set(windows.pre_shock_ref_dates) - set(pre_shock_days))
        raise RuntimeError(
            "Pre-shock reference window is missing snapshot(s): "
            f"{[d.isoformat() for d in missing_ref]}"
        )
    pre_shock_means = {
        stat: sum(daily_replays[d].stats[stat] for d in pre_shock_days) / len(pre_shock_days)
        for stat in ABLATION_STATS
    }

    # ------------------------------------------------------------------
    # 3. Per-variant baseline (unablated) e_star series + transitions.
    # ------------------------------------------------------------------
    search_days = [d for d in present_days if windows.search_start <= d <= windows.search_end]
    # The shift calendar is the COMPLETE business-day sequence of the search
    # window, not just the days that have snapshots.  business_day_shift
    # subtracts list indices, so leaving a missing day out would silently
    # collapse the distance across it -- a Friday-to-Tuesday move would read as
    # one business day when Monday's snapshot is absent.  Missing snapshots are
    # explicitly supported and skipped, so this is reachable by construction.
    search_dates_iso = [
        d.isoformat() for d in business_days(windows.search_start, windows.search_end)
    ]

    variant_baseline_rows: list[dict[str, Any]] = []
    baseline_transitions: dict[str, tuple[Transition, Transition]] = {}
    baseline_series_by_variant: dict[str, list[tuple[str, float]]] = {}
    for variant_name in ALL_VARIANT_NAMES:
        cfg = _variant_config(variant_name)
        series: list[tuple[str, float]] = []
        for day in search_days:
            replay = compute_day_replay(
                snapshots[day],
                snapshot_ref=f"{variant_name}-{day.isoformat()}",
                config=cfg,
                shock_day=windows.shock_day,
            )
            series.append((day.isoformat(), replay.e_star))
            variant_baseline_rows.append(
                {"variant": variant_name, "date": day.isoformat(), "e_star": replay.e_star}
            )
        baseline_series_by_variant[variant_name] = series
        baseline_transitions[variant_name] = extract_transitions(series)

    write_csv_rows(
        os.path.join(out_dir, "variant_baseline.csv"),
        variant_baseline_rows,
        ("variant", "date", "e_star"),
    )

    transitions_baseline_rows = [
        {
            "variant": variant_name,
            "primary_label": primary.label,
            "primary_date": primary.date,
            "secondary_label": secondary.label,
            "secondary_date": secondary.date,
        }
        for variant_name, (primary, secondary) in baseline_transitions.items()
    ]
    write_csv_rows(
        os.path.join(out_dir, "transitions_baseline.csv"),
        transitions_baseline_rows,
        ("variant", "primary_label", "primary_date", "secondary_label", "secondary_date"),
    )
    _write_markdown_table(
        os.path.join(out_dir, "transitions_baseline.md"),
        "Baseline (unablated) e_star transition dates per variant",
        ("variant", "primary_label", "primary_date", "secondary_label", "secondary_date"),
        transitions_baseline_rows,
        [],
    )

    # ------------------------------------------------------------------
    # 4. Ablation grid: variants alpha/beta/delta x axes x references.
    #
    # Three axes, distinguished by the "axis" column:
    #   "statistic"      -- a raw market measurement, substituted before any
    #                       derivation, as in the original 2026-08 run.
    #   "estar_term"     -- an argument compute_e_raw / compute_gravity_bias
    #                       actually consumes.  This is the axis that isolates
    #                       one term of e_star.
    #   "signal_feature" -- a SignalFeatures field that is upstream of those
    #                       terms rather than one of them: fundamental_score
    #                       and technical_score both feed compute_u, and
    #                       technical_score also appears in direction_signal,
    #                       so neither override moves a single term.  Useful,
    #                       but never read as an isolation.
    #
    # All reference means come from the same alpha replays over the same
    # pre-shock days, so the axes are comparable to each other.
    # ------------------------------------------------------------------
    pre_shock_feature_means = {
        name: (
            sum(getattr(daily_replays[d].signal_features, name) for d in pre_shock_days)
            / len(pre_shock_days)
        )
        for name in ABLATION_SIGNAL_FEATURES
    }
    # e_star terms are referenced PER VARIANT, unlike the statistics and the
    # SignalFeatures: compute_u reads config.t_weight, which the variants
    # override (beta 0.20 against alpha's 0.30), so alpha's historical u_score
    # is not beta's. Injecting it would conflate "restore this term to its
    # pre-shock level" with "give this variant a different baseline".
    pre_shock_term_means_by_variant = {
        variant_name: {
            name: (
                sum(
                    _estar_term_value(daily_replays_by_variant[variant_name][d], name)
                    for d in pre_shock_days
                )
                / len(pre_shock_days)
            )
            for name in ABLATION_ESTAR_TERMS
        }
        for variant_name in ABLATION_VARIANT_NAMES
    }


    ablation_rows: list[dict[str, Any]] = []
    for variant_name in ABLATION_VARIANT_NAMES:
        cfg = _variant_config(variant_name)
        baseline_primary, baseline_secondary = baseline_transitions[variant_name]
        # Rebuilt per variant so the e_star-term references are that
        # variant's own; the other two axes are variant-independent.
        ablation_axes: tuple[tuple[str, tuple[str, ...], dict[str, float]], ...] = (
            ("statistic", ABLATION_STATS, pre_shock_means),
            (
                "estar_term",
                ABLATION_ESTAR_TERMS,
                pre_shock_term_means_by_variant[variant_name],
            ),
            ("signal_feature", ABLATION_SIGNAL_FEATURES, pre_shock_feature_means),
        )
        for axis, names, ref_means in ablation_axes:
            for stat_name in names:
                for ref_kind in REFERENCE_KINDS:
                    if ref_kind == "neutral":
                        ref_value = NEUTRAL_TERM_REFERENCES.get(stat_name, 0.0)
                    else:
                        ref_value = ref_means[stat_name]
                    override = {stat_name: ref_value}
                    series: list[tuple[str, float]] = []
                    for day in search_days:
                        replay = compute_day_replay(
                            snapshots[day],
                            snapshot_ref=(
                                f"{variant_name}-{axis}-{stat_name}-{ref_kind}-"
                                f"{day.isoformat()}"
                            ),
                            config=cfg,
                            shock_day=windows.shock_day,
                            stats_override=(
                                override if axis == "statistic" else None
                            ),
                            signal_feature_override=(
                                override if axis == "signal_feature" else None
                            ),
                            # Every estar_term override goes through the
                            # recomposition, which applies it where the term is
                            # consumed. Routing the SignalFeatures-backed ones
                            # through the request instead would let compute_u
                            # read them too.
                            estar_term_override=(
                                override if axis == "estar_term" else None
                            ),
                        )
                        series.append((day.isoformat(), replay.e_star))
                    primary, secondary = extract_transitions(series)
                    primary_shift = business_day_shift(
                        baseline_primary, primary, search_dates_iso
                    )
                    secondary_shift = business_day_shift(
                        baseline_secondary, secondary, search_dates_iso
                    )
                    ablation_rows.append(
                        {
                            "variant": variant_name,
                            "axis": axis,
                            "stat": stat_name,
                            "reference_kind": ref_kind,
                            "reference_value": ref_value,
                            "baseline_primary_label": baseline_primary.label,
                            "baseline_primary_date": baseline_primary.date,
                            "primary_label": primary.label,
                            "primary_date": primary.date,
                            "primary_shift_business_days": primary_shift,
                            "baseline_secondary_label": baseline_secondary.label,
                            "baseline_secondary_date": baseline_secondary.date,
                            "secondary_label": secondary.label,
                            "secondary_date": secondary.date,
                            "secondary_shift_business_days": secondary_shift,
                        }
                    )

    ablation_fieldnames = (
        "variant",
        "axis",
        "stat",
        "reference_kind",
        "reference_value",
        "baseline_primary_label",
        "baseline_primary_date",
        "primary_label",
        "primary_date",
        "primary_shift_business_days",
        "baseline_secondary_label",
        "baseline_secondary_date",
        "secondary_label",
        "secondary_date",
        "secondary_shift_business_days",
    )
    write_csv_rows(os.path.join(out_dir, "ablation.csv"), ablation_rows, ablation_fieldnames)
    _write_markdown_table(
        os.path.join(out_dir, "ablation.md"),
        "Ablation grid (alpha/beta/delta x axis x name x reference)",
        ablation_fieldnames,
        ablation_rows,
        [],
    )

    # Rate-limiting candidate per (variant, reference): the ablated stat whose
    # primary transition moved earliest (most negative shift; a special-label
    # "lag eliminated" outcome ranks as maximally early).
    def _rank_key(row: dict[str, Any]) -> tuple[int, int]:
        if row["primary_label"] == ALWAYS_POSITIVE_POST_SHOCK:
            return (0, 0)
        if row["primary_shift_business_days"] is not None:
            return (1, row["primary_shift_business_days"])
        return (2, 0)

    def _rate_limiting_for(axis: str) -> dict[str, dict[str, list[str] | None]]:
        out: dict[str, dict[str, list[str] | None]] = {}
        for variant_name in ABLATION_VARIANT_NAMES:
            out[variant_name] = {}
            baseline_primary, _ = baseline_transitions[variant_name]
            # With no baseline transition date there is no lag to attribute, and
            # every ablation's shift is None: _rank_key would tie them all and
            # min() would report whichever term happens to be configured first.
            # The CLI makes these windows ordinary (the September window is
            # NO_POST_SHOCK_RECOVERY for three of four variants), so say
            # nothing rather than emit an arbitrary causal attribution.
            if baseline_primary.date is None:
                for ref_kind in REFERENCE_KINDS:
                    out[variant_name][ref_kind] = None
                continue
            for ref_kind in REFERENCE_KINDS:
                candidates = [
                    row
                    for row in ablation_rows
                    if row["variant"] == variant_name
                    and row["reference_kind"] == ref_kind
                    and row["axis"] == axis
                ]
                if not candidates:
                    out[variant_name][ref_kind] = None
                    continue
                best = min(_rank_key(row) for row in candidates)
                # Only an intervention that actually moved the transition
                # earlier -- or removed the lag outright -- is evidence of a
                # rate limiter. A best rank of "resolved but not earlier" means
                # nothing here carried it.
                if best[0] == 1 and best[1] >= 0:
                    out[variant_name][ref_kind] = None
                    continue
                if best[0] == 2:
                    out[variant_name][ref_kind] = None
                    continue
                # Report every candidate sharing the best rank. Taking min()'s
                # single winner would make the answer depend on the order the
                # terms happen to be listed in, not on the evidence.
                out[variant_name][ref_kind] = sorted(
                    row["stat"] for row in candidates if _rank_key(row) == best
                )
        return out

    # Ranked within an axis, never across them: a statistic and a signal
    # feature are not substitutable explanations, and mixing them would let
    # the larger family decide the answer.
    rate_limiting = _rate_limiting_for("statistic")
    rate_limiting_estar_term = _rate_limiting_for("estar_term")
    rate_limiting_signal_feature = _rate_limiting_for("signal_feature")

    summary = {
        "analysis_window": {
            "start": windows.analysis_start.isoformat(),
            "end": windows.analysis_end.isoformat(),
        },
        "search_window": {
            "start": windows.search_start.isoformat(),
            "end": windows.search_end.isoformat(),
        },
        "shock_day": windows.shock_day.isoformat(),
        "missing_dates": missing_dates,
        "rate_limiting_estar_term": rate_limiting_estar_term,
        "rate_limiting_signal_feature": rate_limiting_signal_feature,
        "clamp_saturated_day_count": len(clamp_saturated_dates),
        "clamp_saturated_dates": clamp_saturated_dates,
        "pre_shock_reference_means": pre_shock_means,
        "sign_change_days": sign_changes,
        "baseline_transitions": {
            variant_name: {
                "primary_label": primary.label,
                "primary_date": primary.date,
                "secondary_label": secondary.label,
                "secondary_date": secondary.date,
            }
            for variant_name, (primary, secondary) in baseline_transitions.items()
        },
        "rate_limiting_candidate_by_variant_and_reference": rate_limiting,
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    return summary


def _sign_change_days(rows: list[dict[str, Any]], field: str) -> dict[str, list[str]]:
    """Return dates where *field* went negative->positive or positive->negative."""
    turned_positive: list[str] = []
    turned_negative: list[str] = []
    prev_value: float | None = None
    for row in rows:
        value = row[field]
        if prev_value is not None:
            if prev_value <= 0 and value > 0:
                turned_positive.append(row["date"])
            elif prev_value > 0 and value <= 0:
                turned_negative.append(row["date"])
        prev_value = value
    return {"turned_positive": turned_positive, "turned_negative": turned_negative}


def _write_markdown_table(
    path: str,
    title: str,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, Any]],
    missing_dates: list[str],
) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lines = [f"# {title}", ""]
    if missing_dates:
        lines.append(f"Missing snapshot dates (skipped, not backfilled): {missing_dates}")
        lines.append("")
    lines.append("| " + " | ".join(fieldnames) + " |")
    lines.append("|" + "|".join(["---"] * len(fieldnames)) + "|")
    for row in rows:
        cells = []
        for name in fieldnames:
            value = row[name]
            if isinstance(value, float):
                cells.append(f"{value:.6g}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _parse_cli_date(value: str) -> date:
    """Parse a ``YYYY-MM-DD`` CLI argument into a ``date``."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - argparse renders the message
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value!r}") from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fxdata-dir",
        required=True,
        help="Path to the fx-daily-data CSV root (contains history/{date}/{batch_id}/...).",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Directory to write daily_series.csv/.md, ablation.csv/.md, summary.json, etc.",
    )
    parser.add_argument(
        "--analysis-start",
        type=_parse_cli_date,
        default=DEFAULT_ANALYSIS_START,
        help="First business day of the descriptive window (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--analysis-end",
        type=_parse_cli_date,
        default=DEFAULT_ANALYSIS_END,
        help="Last business day of the descriptive window (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--search-start",
        type=_parse_cli_date,
        default=None,
        help=(
            "First day of the transition-search window (YYYY-MM-DD). "
            "Defaults to the shock day."
        ),
    )
    parser.add_argument(
        "--search-end",
        type=_parse_cli_date,
        default=None,
        help=(
            "Last day of the transition-search window (YYYY-MM-DD). "
            "Defaults to --analysis-end."
        ),
    )
    parser.add_argument(
        "--shock-day",
        type=_parse_cli_date,
        default=DEFAULT_SHOCK_DAY,
        help="The shock day (YYYY-MM-DD). Also the default --search-start.",
    )
    parser.add_argument(
        "--pre-shock-ref-dates",
        type=_parse_cli_date,
        nargs="+",
        default=list(DEFAULT_PRE_SHOCK_REF_DATES),
        help=(
            "Business days forming the pre-shock reference window "
            "(space-separated YYYY-MM-DD). All must precede --shock-day."
        ),
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.fxdata_dir):
        print(f"[ERROR] --fxdata-dir does not exist: {args.fxdata_dir}", file=sys.stderr)
        sys.exit(1)

    windows = AnalysisWindows(
        analysis_start=args.analysis_start,
        analysis_end=args.analysis_end,
        search_start=args.search_start or args.shock_day,
        search_end=args.search_end or args.analysis_end,
        shock_day=args.shock_day,
        pre_shock_ref_dates=tuple(args.pre_shock_ref_dates),
    )
    try:
        windows.validate()
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    summary = run_analysis(args.fxdata_dir, args.out_dir, windows)

    print(f"[OK] Analysis complete. Outputs written to {os.path.abspath(args.out_dir)}")
    print(f"  analysis_window: {summary['analysis_window']}")
    print(f"  missing_dates: {summary['missing_dates']}")
    print(f"  clamp_saturated_day_count: {summary['clamp_saturated_day_count']}")
    for variant_name, t in summary["baseline_transitions"].items():
        print(f"  {variant_name}: primary={t['primary_label']}/{t['primary_date']}")


if __name__ == "__main__":
    main()
