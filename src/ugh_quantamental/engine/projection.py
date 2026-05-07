"""Deterministic projection engine using explicit normalized feature contracts.

The pipeline structure (compute_u → compute_alignment → compute_e_raw →
compute_gravity_bias → compute_e_star → mismatch / conviction / urgency)
matches v1. ``compute_e_raw`` and the upstream ``fire_probability`` builder
are redesigned for v2 (see ``docs/specs/fx_ugh_engine_v2.md`` §6.1 / §5.3).
All other functions remain byte-identical to v1.
"""

import math

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.schemas.projection import ProjectionSnapshot


def _clamp(value: float, lower: float, upper: float) -> float:
    if not math.isfinite(value):
        raise ValueError("clamp value must be finite")
    return max(lower, min(upper, value))


def compute_u(
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
    config: ProjectionConfig,
) -> float:
    """Compute directional utility score U in [-1, 1]."""
    directional_component = (
        question_features.question_direction.sign
        * question_features.q_strength
        * question_features.s_q
    )
    context_scale = signal_features.context_score / 2.0
    signal_blend = (
        config.f_weight * signal_features.fundamental_score
        + config.t_weight * signal_features.technical_score
    )
    raw_u = directional_component * (0.5 + 0.5 * question_features.temporal_score)
    raw_u += signal_blend * context_scale
    return _clamp(raw_u, -1.0, 1.0)


def compute_alignment(
    alignment_inputs: AlignmentInputs,
    config: ProjectionConfig,
) -> float:
    """Compute weighted pairwise alignment score in [0, 1]."""
    weighted_gaps = [
        alignment_inputs.d_qf * alignment_inputs.w_qf * config.pair_weight_qf,
        alignment_inputs.d_qt * alignment_inputs.w_qt * config.pair_weight_qt,
        alignment_inputs.d_qp * alignment_inputs.w_qp * config.pair_weight_qp,
        alignment_inputs.d_ft * alignment_inputs.w_ft * config.pair_weight_ft,
        alignment_inputs.d_fp * alignment_inputs.w_fp * config.pair_weight_fp,
        alignment_inputs.d_tp * alignment_inputs.w_tp * config.pair_weight_tp,
    ]
    weights = [
        alignment_inputs.w_qf * config.pair_weight_qf,
        alignment_inputs.w_qt * config.pair_weight_qt,
        alignment_inputs.w_qp * config.pair_weight_qp,
        alignment_inputs.w_ft * config.pair_weight_ft,
        alignment_inputs.w_fp * config.pair_weight_fp,
        alignment_inputs.w_tp * config.pair_weight_tp,
    ]
    total_weight = sum(weights)
    if total_weight == 0.0:
        return 1.0

    average_gap = sum(weighted_gaps) / total_weight
    return _clamp(1.0 - average_gap, 0.0, 1.0)


def compute_e_raw(
    u_score: float,
    signal_features: SignalFeatures,
    alignment: float,
    config: ProjectionConfig,
) -> float:
    """Compute pre-bias projection signal E_raw in [-1, 1] (v2).

    v2 form: ``e_raw = clamp(direction_signal × conviction_multiplier ×
    alignment, -1, 1)`` where:

    * ``direction_signal`` = weighted sum of three independent directional
      inputs (``u_score``, ``technical_score``, ``price_implied_score``)
      normalized by the sum of the three direction weights.
    * ``conviction_multiplier`` = ``conviction_floor + (1 -
      conviction_floor) * fire_probability`` ∈ ``[conviction_floor, 1.0]``.
      Maps fire monotonically to a magnitude shrink — never inverts the
      direction signal.

    See spec §6.1 for the full rationale and §9A for why fire is treated as
    a conviction multiplier (Framing A) rather than a directional confirmer
    in v2.
    """
    direction_weight_total = config.u_weight + config.t_weight + config.p_weight
    if direction_weight_total == 0.0:
        # Preserve v1's zero-denominator guard. Pydantic field constraints
        # allow ge=0.0 on each weight, so a caller may legitimately set all
        # three direction weights to zero (e.g. to disable the direction
        # layer while keeping fire/alignment plumbing). Return 0.0 to keep
        # the bounded / no-NaN invariant.
        return 0.0

    direction_signal = (
        config.u_weight * u_score
        + config.t_weight * signal_features.technical_score
        + config.p_weight * signal_features.price_implied_score
    ) / direction_weight_total

    # fire_probability ∈ [0, 1]; conviction_multiplier ∈ [floor, 1.0].
    conviction_multiplier = (
        config.conviction_floor
        + (1.0 - config.conviction_floor) * signal_features.fire_probability
    )

    return _clamp(direction_signal * conviction_multiplier * alignment, -1.0, 1.0)


def compute_gravity_bias(signal_features: SignalFeatures, config: ProjectionConfig) -> float:
    """Compute deterministic gravity bias adjustment."""
    bias = (
        config.gravity_lock_coef * signal_features.grv_lock
        + config.gravity_regime_coef * signal_features.regime_fit
        - config.gravity_dispersion_coef * signal_features.narrative_dispersion
    )
    return _clamp(bias, -1.0, 1.0)


def compute_e_star(e_raw: float, gravity_bias: float) -> float:
    """Compute post-bias point estimate E* in [-1, 1]."""
    return _clamp(e_raw + gravity_bias, -1.0, 1.0)


def compute_mismatch_px(e_star: float, signal_features: SignalFeatures) -> float:
    """Compute signed price mismatch (model minus price-implied)."""
    return _clamp(e_star - signal_features.price_implied_score, -2.0, 2.0)


def compute_mismatch_sem(
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
) -> float:
    """Compute signed semantic mismatch (question intent minus semantic signal anchor)."""
    intent = question_features.question_direction.sign * question_features.q_strength
    semantic_anchor = 0.5 * (
        signal_features.fundamental_score + signal_features.technical_score
    )
    return _clamp(intent - semantic_anchor, -2.0, 2.0)


def compute_conviction(
    signal_features: SignalFeatures,
    alignment: float,
    mismatch_px: float,
    mismatch_sem: float,
) -> float:
    """Compute confidence-like conviction score in [0, 1]."""
    mismatch_penalty = 0.5 * (abs(mismatch_px) + abs(mismatch_sem))
    raw = signal_features.evidence_confidence * alignment * (1.0 - 0.5 * mismatch_penalty)
    return _clamp(raw, 0.0, 1.0)


def compute_urgency(
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
    conviction: float,
) -> float:
    """Compute urgency score increasing with temporal/fire pressure."""
    raw = (
        0.45 * question_features.temporal_score
        + 0.45 * signal_features.fire_probability
        + 0.10 * (1.0 - conviction)
    )
    return _clamp(raw, 0.0, 1.0)


def build_projection_snapshot(
    projection_id: str,
    horizon_days: int,
    e_star: float,
    conviction: float,
    urgency: float,
    mismatch_px: float,
    mismatch_sem: float,
    config: ProjectionConfig,
) -> ProjectionSnapshot:
    """Build a bounded outward-facing ProjectionSnapshot using provisional v1 width policy."""
    mismatch_magnitude = 0.5 * (abs(mismatch_px) + abs(mismatch_sem))
    width = (
        config.bounds_base_width
        + config.bounds_mismatch_coef * mismatch_magnitude
        + config.bounds_low_conf_coef * (1.0 - conviction)
        + config.bounds_urgency_coef * urgency
    )
    width = _clamp(width, 0.0, config.bounds_max_width)

    lower_bound = e_star - width
    upper_bound = e_star + width

    return ProjectionSnapshot(
        projection_id=projection_id,
        horizon_days=horizon_days,
        point_estimate=e_star,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        confidence=conviction,
    )


def run_projection_engine(
    projection_id: str,
    horizon_days: int,
    question_features: QuestionFeatures,
    signal_features: SignalFeatures,
    alignment_inputs: AlignmentInputs,
    config: ProjectionConfig | None = None,
) -> ProjectionEngineResult:
    """Run the pure deterministic v1 projection engine end-to-end."""
    cfg = config or ProjectionConfig()
    u_score = compute_u(question_features, signal_features, cfg)
    alignment = compute_alignment(alignment_inputs, cfg)
    e_raw = compute_e_raw(u_score, signal_features, alignment, cfg)
    gravity_bias = compute_gravity_bias(signal_features, cfg)
    e_star = compute_e_star(e_raw, gravity_bias)
    mismatch_px = compute_mismatch_px(e_star, signal_features)
    mismatch_sem = compute_mismatch_sem(question_features, signal_features)
    conviction = compute_conviction(signal_features, alignment, mismatch_px, mismatch_sem)
    urgency = compute_urgency(question_features, signal_features, conviction)
    snapshot = build_projection_snapshot(
        projection_id=projection_id,
        horizon_days=horizon_days,
        e_star=e_star,
        conviction=conviction,
        urgency=urgency,
        mismatch_px=mismatch_px,
        mismatch_sem=mismatch_sem,
        config=cfg,
    )

    return ProjectionEngineResult(
        u_score=u_score,
        alignment=alignment,
        e_raw=e_raw,
        gravity_bias=gravity_bias,
        e_star=e_star,
        mismatch_px=mismatch_px,
        mismatch_sem=mismatch_sem,
        conviction=conviction,
        urgency=urgency,
        projection_snapshot=snapshot,
    )
