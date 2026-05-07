"""Deterministic market-derived UGH request builder.

Converts an ``FxProtocolMarketSnapshot`` into a ``FullWorkflowRequest`` by
deriving all UGH engine inputs (QuestionFeatures, SignalFeatures,
AlignmentInputs, StateEventFeatures) from observable snapshot statistics.

Every formula is pure, bounded, and deterministic: the same snapshot always
produces the same UGH request. No randomness, no external calls, no mutable
state.

Feature mapping summary
-----------------------

**Intermediate statistics** (computed from ``completed_windows``):

- ``prev_close_change_bp``: close change of newest window in basis points.
- ``trailing_mean_abs_change_bp``: mean |close_change_bp| over last 20 windows.
- ``trailing_mean_range``: mean (high - low) over last 20 windows.
- ``recent_mean_range``: mean (high - low) over last 5 windows.
- ``sma5``, ``sma20``: simple moving averages of close prices.
- ``momentum_5d``: (sma5 - sma20) / sma20, normalized to [-1, 1].
- ``directional_consistency``: fraction of last 5 windows with same sign as
  the 5-window net change, in [0, 1].
- ``range_expansion``: recent_mean_range / trailing_mean_range, centered at 1.
- ``spot_vs_sma20``: (current_spot - sma20) / sma20, normalized.

**A. QuestionFeatures**

- ``question_direction``: positive if momentum_5d > +0.0005, negative if
  < -0.0005, else neutral.
- ``q_strength``: abs(momentum_5d) clamped to [0, 1].
- ``s_q``: directional_consistency.
- ``temporal_score``: observation_freshness (always 1.0 for daily data).

**B. SignalFeatures**

- ``fundamental_score``: spot_vs_sma20 clamped to [-1, 1].
- ``technical_score``: momentum_5d clamped to [-1, 1].
- ``price_implied_score``: prev_close_change_bp / trailing_mean_abs_change_bp,
  clamped to [-1, 1].
- ``context_score``: range_expansion clamped to [0, 2].
- ``grv_lock``: 1 - range_expansion, clamped to [0, 1] (high when range contracts).
- ``regime_fit``: directional_consistency.
- ``narrative_dispersion``: abs(fundamental_score - technical_score) / 2.
- ``evidence_confidence``: 1 - narrative_dispersion, clamped to [0, 1].
- ``fire_probability`` (v2): additive evidence model centered on 0.5.
  ``range_evidence = clamp((range_expansion - 1) * 2, -1, 1)``;
  ``momentum_evidence = clamp(abs(momentum_5d) * 200, 0, 1)``;
  ``thrust_score = 0.5 * range_evidence + 0.5 * momentum_evidence``;
  ``fire_probability = clamp(0.5 + 0.5 * thrust_score, 0, 1)``.
  Centered at 0.5 (no-information prior) so range contraction shifts fire
  below 0.5 and range expansion / momentum shift it above. Replaces v1's
  multiplicative ``range_exp * abs(momentum)`` which collapsed to 0 in
  choppy regimes and produced the structural anti-thrust bias documented
  in spec §3.

**C. AlignmentInputs**

Pairwise disagreement gaps derived from component scores:

- ``d_qf``: abs(q_signed - fundamental_score) / 2
- ``d_qt``: abs(q_signed - technical_score) / 2
- ``d_qp``: abs(q_signed - price_implied_score) / 2
- ``d_ft``: abs(fundamental_score - technical_score) / 2
- ``d_fp``: abs(fundamental_score - price_implied_score) / 2
- ``d_tp``: abs(technical_score - price_implied_score) / 2

where ``q_signed = direction.sign * q_strength``.

**D. StateEventFeatures**

- ``catalyst_strength``: abs(prev_close_change_bp) / trailing_mean_abs_change_bp,
  clamped to [0, 1].
- ``follow_through``: directional_consistency.
- ``pricing_saturation``: clamp(range_expansion - 1, 0, 1) — high when range
  is expanding beyond trailing average.
- ``disconfirmation_strength``: 1 if the newest close change opposes the 5-day
  momentum direction, scaled by magnitude. 0 otherwise. Clamped to [0, 1].
- ``regime_shock``: clamp(abs(range_expansion - 1) * 2, 0, 1) — high when
  range deviates from trailing average in either direction.
- ``observation_freshness``: 1.0 (daily protocol always uses the freshest data).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)

if TYPE_CHECKING:
    from ugh_quantamental.workflows.models import FullWorkflowRequest

_MIN_WINDOWS: int = 20


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to [lo, hi]."""
    return max(lo, min(hi, value))


def _close_change_bp(window: FxCompletedWindow) -> float:
    """Close change in basis points for a completed window."""
    return (window.close_price - window.open_price) / window.open_price * 10_000


def _range_price(window: FxCompletedWindow) -> float:
    """High − low range for a completed window."""
    return window.high_price - window.low_price


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide *numerator* by *denominator*; return *default* if denominator ≈ 0."""
    if abs(denominator) < 1e-12:
        return default
    return numerator / denominator


# ---------------------------------------------------------------------------
# Intermediate statistics
# ---------------------------------------------------------------------------


def compute_snapshot_statistics(snapshot: FxProtocolMarketSnapshot) -> dict[str, float]:
    """Compute all intermediate statistics from a market snapshot.

    Returns a flat dict of named statistics used by the feature derivation
    functions below.  Extracting this as a separate function makes the
    intermediate values inspectable and testable.

    Parameters
    ----------
    snapshot:
        Market snapshot with at least 20 completed windows ordered
        oldest → newest.

    Returns
    -------
    dict[str, float]
        Named intermediate statistics.

    Raises
    ------
    ValueError
        If fewer than 20 completed windows are present.
    """
    wins = snapshot.completed_windows
    if len(wins) < _MIN_WINDOWS:
        raise ValueError(
            f"Need at least {_MIN_WINDOWS} completed windows; got {len(wins)}"
        )

    trailing = wins[-_MIN_WINDOWS:]
    last5 = wins[-5:]

    # Close changes
    prev_close_change_bp = _close_change_bp(trailing[-1])
    trailing_mean_abs_change_bp = (
        sum(abs(_close_change_bp(w)) for w in trailing) / len(trailing)
    )

    # Ranges
    trailing_mean_range = sum(_range_price(w) for w in trailing) / len(trailing)
    recent_mean_range = sum(_range_price(w) for w in last5) / len(last5)

    # Moving averages
    sma5 = sum(w.close_price for w in last5) / len(last5)
    sma20 = sum(w.close_price for w in trailing) / len(trailing)

    # Momentum: SMA5-vs-SMA20 ratio, bounded
    momentum_5d = _safe_div(sma5 - sma20, sma20)

    # Directional consistency: fraction of last 5 windows whose close change
    # has the same sign as the 5-window net change.
    net_change_5 = last5[-1].close_price - last5[0].open_price
    net_sign = 1.0 if net_change_5 > 0 else (-1.0 if net_change_5 < 0 else 0.0)
    if abs(net_sign) < 0.5:
        # Net change is essentially zero — count as 50% consistent.
        directional_consistency = 0.5
    else:
        same_dir_count = sum(
            1
            for w in last5
            if (w.close_price - w.open_price) * net_sign > 0
        )
        directional_consistency = same_dir_count / len(last5)

    # Range expansion/contraction: recent vs trailing.
    range_expansion = _safe_div(recent_mean_range, trailing_mean_range, default=1.0)

    # Spot vs SMA20
    spot_vs_sma20 = _safe_div(snapshot.current_spot - sma20, sma20)

    return {
        "prev_close_change_bp": prev_close_change_bp,
        "trailing_mean_abs_change_bp": trailing_mean_abs_change_bp,
        "trailing_mean_range": trailing_mean_range,
        "recent_mean_range": recent_mean_range,
        "sma5": sma5,
        "sma20": sma20,
        "momentum_5d": momentum_5d,
        "directional_consistency": directional_consistency,
        "range_expansion": range_expansion,
        "spot_vs_sma20": spot_vs_sma20,
    }


# ---------------------------------------------------------------------------
# Feature derivation
# ---------------------------------------------------------------------------

_MOMENTUM_THRESHOLD: float = 0.0005  # ±5 bp SMA ratio for direction


def derive_question_features(stats: dict[str, float]) -> dict[str, object]:
    """Derive ``QuestionFeatures`` fields from intermediate statistics.

    Returns a dict suitable for unpacking into ``QuestionFeatures(**result)``.
    """
    momentum = stats["momentum_5d"]
    if momentum > _MOMENTUM_THRESHOLD:
        direction = "positive"
    elif momentum < -_MOMENTUM_THRESHOLD:
        direction = "negative"
    else:
        direction = "neutral"

    q_strength = _clamp(abs(momentum) * 100, 0.0, 1.0)  # scale to [0, 1]
    s_q = stats["directional_consistency"]
    temporal_score = 1.0  # daily protocol = always fresh

    return {
        "question_direction": direction,
        "q_strength": q_strength,
        "s_q": s_q,
        "temporal_score": temporal_score,
    }


def derive_signal_features(stats: dict[str, float]) -> dict[str, float]:
    """Derive ``SignalFeatures`` fields from intermediate statistics.

    Returns a dict suitable for unpacking into ``SignalFeatures(**result)``.
    """
    fundamental_score = _clamp(stats["spot_vs_sma20"] * 100, -1.0, 1.0)
    technical_score = _clamp(stats["momentum_5d"] * 100, -1.0, 1.0)

    prev_bp = stats["prev_close_change_bp"]
    mean_abs_bp = stats["trailing_mean_abs_change_bp"]
    price_implied_score = _clamp(_safe_div(prev_bp, mean_abs_bp), -1.0, 1.0)

    range_exp = stats["range_expansion"]
    context_score = _clamp(range_exp, 0.0, 2.0)

    grv_lock = _clamp(1.0 - range_exp, 0.0, 1.0)
    regime_fit = stats["directional_consistency"]

    narrative_dispersion = _clamp(abs(fundamental_score - technical_score) / 2.0, 0.0, 1.0)
    evidence_confidence = _clamp(1.0 - narrative_dispersion, 0.0, 1.0)

    # v2 additive evidence model (spec §5.3): range_evidence in [-1, 1] and
    # momentum_evidence in [0, 1] each contribute half-weight to a thrust
    # score, then map onto [0, 1] centered at 0.5 (no-info prior). Range
    # contraction (range_exp < 1) yields negative thrust evidence; momentum
    # is non-negative since |momentum_5d| has no sign.
    range_evidence = _clamp((range_exp - 1.0) * 2.0, -1.0, 1.0)
    momentum_evidence = _clamp(abs(stats["momentum_5d"]) * 200.0, 0.0, 1.0)
    thrust_score = 0.5 * range_evidence + 0.5 * momentum_evidence
    fire_probability = _clamp(0.5 + 0.5 * thrust_score, 0.0, 1.0)

    return {
        "fundamental_score": fundamental_score,
        "technical_score": technical_score,
        "price_implied_score": price_implied_score,
        "context_score": context_score,
        "grv_lock": grv_lock,
        "regime_fit": regime_fit,
        "narrative_dispersion": narrative_dispersion,
        "evidence_confidence": evidence_confidence,
        "fire_probability": fire_probability,
    }


def derive_alignment_inputs(
    direction_sign: int,
    q_strength: float,
    signal: dict[str, float],
) -> dict[str, float]:
    """Derive ``AlignmentInputs`` pairwise disagreement gaps.

    Parameters
    ----------
    direction_sign:
        +1, -1, or 0 from ``QuestionDirectionSign.sign``.
    q_strength:
        Derived question strength in [0, 1].
    signal:
        Dict of signal feature values as returned by ``derive_signal_features``.

    Returns
    -------
    dict[str, float]
        Pairwise gap values d_qf, d_qt, d_qp, d_ft, d_fp, d_tp, all in [0, 1].
    """
    q_signed = direction_sign * q_strength  # in [-1, 1]
    f = signal["fundamental_score"]
    t = signal["technical_score"]
    p = signal["price_implied_score"]

    return {
        "d_qf": _clamp(abs(q_signed - f) / 2.0, 0.0, 1.0),
        "d_qt": _clamp(abs(q_signed - t) / 2.0, 0.0, 1.0),
        "d_qp": _clamp(abs(q_signed - p) / 2.0, 0.0, 1.0),
        "d_ft": _clamp(abs(f - t) / 2.0, 0.0, 1.0),
        "d_fp": _clamp(abs(f - p) / 2.0, 0.0, 1.0),
        "d_tp": _clamp(abs(t - p) / 2.0, 0.0, 1.0),
    }


def derive_state_event_features(stats: dict[str, float]) -> dict[str, float]:
    """Derive ``StateEventFeatures`` fields from intermediate statistics.

    Returns a dict suitable for unpacking into ``StateEventFeatures(**result)``.
    """
    prev_bp = stats["prev_close_change_bp"]
    mean_abs_bp = stats["trailing_mean_abs_change_bp"]

    catalyst_strength = _clamp(_safe_div(abs(prev_bp), mean_abs_bp), 0.0, 1.0)

    follow_through = stats["directional_consistency"]

    range_exp = stats["range_expansion"]
    pricing_saturation = _clamp(range_exp - 1.0, 0.0, 1.0)

    # Disconfirmation: newest close opposes the 5-day momentum direction.
    momentum = stats["momentum_5d"]
    if abs(momentum) < 1e-9:
        disconfirmation_strength = 0.0
    else:
        momentum_sign = 1.0 if momentum > 0 else -1.0
        close_sign = 1.0 if prev_bp > 0 else (-1.0 if prev_bp < 0 else 0.0)
        if momentum_sign * close_sign < 0:
            # Opposing direction — scale by relative magnitude.
            disconfirmation_strength = _clamp(
                _safe_div(abs(prev_bp), mean_abs_bp), 0.0, 1.0
            )
        else:
            disconfirmation_strength = 0.0

    regime_shock = _clamp(abs(range_exp - 1.0) * 2.0, 0.0, 1.0)

    observation_freshness = 1.0  # daily protocol = always fresh

    return {
        "catalyst_strength": catalyst_strength,
        "follow_through": follow_through,
        "pricing_saturation": pricing_saturation,
        "disconfirmation_strength": disconfirmation_strength,
        "regime_shock": regime_shock,
        "observation_freshness": observation_freshness,
    }


# ---------------------------------------------------------------------------
# Full builder
# ---------------------------------------------------------------------------


def build_ugh_request_from_snapshot(
    snapshot: FxProtocolMarketSnapshot,
    *,
    snapshot_ref: str,
) -> "FullWorkflowRequest":
    """Build a deterministic ``FullWorkflowRequest`` from a market snapshot.

    This is the primary entry point for deriving UGH engine inputs from
    observable market data.  All intermediate statistics, feature derivations,
    and SSV / Omega scaffolding are computed deterministically from the
    snapshot alone.

    Parameters
    ----------
    snapshot:
        Market snapshot with at least 20 completed windows.
    snapshot_ref:
        Opaque reference identifier used for projection_id, snapshot_id,
        omega_id, and question_id.

    Returns
    -------
    FullWorkflowRequest
        Fully populated UGH engine request with market-derived inputs.
    """
    from ugh_quantamental.engine.projection_models import (
        AlignmentInputs,
        QuestionDirectionSign,
        QuestionFeatures,
        SignalFeatures,
    )
    from ugh_quantamental.engine.state_models import StateEventFeatures
    from ugh_quantamental.schemas.enums import LifecycleState, MacroCycleRegime, MarketRegime
    from ugh_quantamental.schemas.market_svp import MarketSVP, Phi, StateProbabilities
    from ugh_quantamental.schemas.omega import BlockObservability, EvidenceLineageRecord, Omega
    from ugh_quantamental.schemas.ssv import (
        FBlock,
        PBlock,
        QBlock,
        QuestionLedger,
        QuestionRecord,
        RBlock,
        SSVSnapshot,
        TBlock,
        XBlock,
    )
    from ugh_quantamental.workflows.models import (
        FullWorkflowRequest,
        FullWorkflowStateRequest,
        ProjectionWorkflowRequest,
    )

    # --- Intermediate statistics ---
    stats = compute_snapshot_statistics(snapshot)

    # --- Derive UGH feature blocks ---
    q_dict = derive_question_features(stats)
    s_dict = derive_signal_features(stats)

    direction_enum = QuestionDirectionSign(q_dict["question_direction"])
    q_strength = float(q_dict["q_strength"])

    a_dict = derive_alignment_inputs(direction_enum.sign, q_strength, s_dict)
    ef_dict = derive_state_event_features(stats)

    # --- Build SSV / Omega scaffolding from market-derived values ---
    # Derive lifecycle state probabilities from market statistics.
    # Range expansion and momentum jointly drive the probability distribution.
    range_exp = stats["range_expansion"]
    momentum_abs = abs(stats["momentum_5d"]) * 100  # same 0-1 scale

    # Base probabilities — shift weight based on market activity level.
    activity = _clamp((range_exp - 0.5) * 2.0, 0.0, 1.0)  # 0=low, 1=high
    trend = _clamp(momentum_abs, 0.0, 1.0)

    # Distribute across lifecycle states.
    dormant = _clamp(0.30 - 0.25 * activity, 0.02, 0.50)
    setup = _clamp(0.30 + 0.10 * activity - 0.10 * trend, 0.02, 0.50)
    fire = _clamp(0.10 + 0.20 * activity * trend, 0.02, 0.50)
    expansion = _clamp(0.10 + 0.15 * trend, 0.02, 0.50)
    exhaustion = _clamp(0.10 + 0.15 * activity * (1.0 - trend), 0.02, 0.50)
    failure = _clamp(0.10 - 0.05 * activity, 0.02, 0.50)

    # Normalize to sum to 1.
    total = dormant + setup + fire + expansion + exhaustion + failure
    dormant /= total
    setup /= total
    fire /= total
    expansion /= total
    exhaustion /= total
    failure /= total

    # Round to avoid floating-point noise in the sum-to-1 validator.
    vals = [dormant, setup, fire, expansion, exhaustion, failure]
    rounded = [round(v, 8) for v in vals]
    # Adjust the largest to absorb rounding residual.
    residual = 1.0 - sum(rounded)
    max_idx = max(range(6), key=lambda i: rounded[i])
    rounded[max_idx] = round(rounded[max_idx] + residual, 8)
    dormant, setup, fire, expansion, exhaustion, failure = rounded

    # Determine dominant state, breaking ties deterministically.
    # Phi requires a unique highest probability.  After rounding two states can
    # be equal (e.g. dormant and setup in a flat market).  We break ties by
    # nudging: subtract a tiny epsilon from each tied non-preferred state and
    # add it to the preferred one (the first in canonical LifecycleState order).
    _STATES_ORDER = [
        LifecycleState.dormant,
        LifecycleState.setup,
        LifecycleState.fire,
        LifecycleState.expansion,
        LifecycleState.exhaustion,
        LifecycleState.failure,
    ]
    prob_map = {
        LifecycleState.dormant: dormant,
        LifecycleState.setup: setup,
        LifecycleState.fire: fire,
        LifecycleState.expansion: expansion,
        LifecycleState.exhaustion: exhaustion,
        LifecycleState.failure: failure,
    }
    max_val = max(prob_map.values())
    tied = [s for s in _STATES_ORDER if math.isclose(prob_map[s], max_val, abs_tol=1e-12)]
    if len(tied) > 1:
        # Break tie: keep the first in canonical order as dominant,
        # transfer a small epsilon from each other tied state.
        eps = 1e-9
        winner = tied[0]
        for loser in tied[1:]:
            prob_map[loser] = prob_map[loser] - eps
            prob_map[winner] = prob_map[winner] + eps
        dormant = prob_map[LifecycleState.dormant]
        setup = prob_map[LifecycleState.setup]
        fire = prob_map[LifecycleState.fire]
        expansion = prob_map[LifecycleState.expansion]
        exhaustion = prob_map[LifecycleState.exhaustion]
        failure = prob_map[LifecycleState.failure]
    dominant_state = max(_STATES_ORDER, key=lambda s: prob_map[s])

    probs = StateProbabilities(
        dormant=dormant,
        setup=setup,
        fire=fire,
        expansion=expansion,
        exhaustion=exhaustion,
        failure=failure,
    )
    phi = Phi(dominant_state=dominant_state, probabilities=probs)

    # Market regime from momentum direction.
    if stats["momentum_5d"] > _MOMENTUM_THRESHOLD:
        regime = MarketRegime.risk_on
    elif stats["momentum_5d"] < -_MOMENTUM_THRESHOLD:
        regime = MarketRegime.risk_off
    else:
        regime = MarketRegime.neutral

    # Use snapshot as_of as timestamp string.
    as_of_str = snapshot.as_of_jst.isoformat()

    market_svp = MarketSVP(
        as_of=as_of_str,
        regime=regime,
        phi=phi,
        confidence=float(s_dict["evidence_confidence"]),
    )

    # Question record derived from direction/score.
    q_direction_map = {
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral",
    }
    question_record = QuestionRecord(
        question_id=snapshot_ref,
        direction=q_direction_map[q_dict["question_direction"]],
        score=_clamp(direction_enum.sign * q_strength, -1.0, 1.0),
        weight=1.0,
    )
    question_ledger = QuestionLedger(
        as_of=as_of_str[:10],  # date portion
        coverage_ratio=1.0,
        questions=[question_record],
    )

    # Block observability from evidence_confidence and range stats.
    obs_base = float(s_dict["evidence_confidence"])
    block_obs = BlockObservability(
        q=_clamp(obs_base, 0.0, 1.0),
        f=_clamp(obs_base, 0.0, 1.0),
        t=_clamp(obs_base + 0.05, 0.0, 1.0),  # technical slightly boosted (direct data)
        p=_clamp(obs_base, 0.0, 1.0),
        r=_clamp(obs_base - 0.05, 0.0, 1.0),  # regime slightly discounted
        x=_clamp(obs_base - 0.10, 0.0, 1.0),   # context most uncertain
    )

    omega = Omega(
        omega_id=f"omega-{snapshot_ref}",
        market_svp=market_svp,
        question_ledger=question_ledger,
        evidence_lineage=(
            EvidenceLineageRecord(
                source_id="market-snapshot",
                observed_at=as_of_str,
                source_type="fx_daily_protocol",
            ),
        ),
        block_confidence=block_obs,
        block_observability=block_obs,
        confidence=obs_base,
    )

    # Derive FBlock aggregate signal from fundamental_score.
    aggregate_signal = _clamp(float(s_dict["fundamental_score"]), -1.0, 1.0)

    # Derive PBlock implied move from trailing stats.
    # implied_move_30d ≈ trailing_mean_abs_change * sqrt(30) / 10000 (annualized-ish).
    mean_abs_bp = stats["trailing_mean_abs_change_bp"]
    implied_move_30d = mean_abs_bp * math.sqrt(30) / 10_000
    implied_volatility = _clamp(mean_abs_bp / 100.0, 0.0, 10.0)  # rough annualized
    skew_25d = float(s_dict["technical_score"]) * 0.01  # mild directional skew

    ssv_snapshot = SSVSnapshot(
        snapshot_id=snapshot_ref,
        q=QBlock(ledger=question_ledger),
        f=FBlock(factor_count=3, aggregate_signal=aggregate_signal),
        t=TBlock(timestamp=as_of_str, lookback_days=20),
        p=PBlock(
            implied_move_30d=implied_move_30d,
            implied_volatility=implied_volatility,
            skew_25d=skew_25d,
        ),
        phi=phi,
        r=RBlock(
            market_regime=regime,
            macro_cycle_regime=(
                MacroCycleRegime.expansion
                if stats["momentum_5d"] > 0
                else MacroCycleRegime.contraction
            ),
            conviction=_clamp(float(s_dict["evidence_confidence"]), 0.0, 1.0),
        ),
        x=XBlock(tags=["market_derived"]),
    )

    return FullWorkflowRequest(
        projection=ProjectionWorkflowRequest(
            projection_id=snapshot_ref,
            horizon_days=1,
            question_features=QuestionFeatures(**q_dict),
            signal_features=SignalFeatures(**s_dict),
            alignment_inputs=AlignmentInputs(**a_dict),
        ),
        state=FullWorkflowStateRequest(
            snapshot=ssv_snapshot,
            omega=omega,
            event_features=StateEventFeatures(**ef_dict),
        ),
    )
