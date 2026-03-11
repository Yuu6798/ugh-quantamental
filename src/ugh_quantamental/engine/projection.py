"""Deterministic v1 projection engine using explicit normalized feature contracts."""

from ugh_quantamental.engine.projection_models import (
    AlignmentInputs,
    ProjectionConfig,
    ProjectionEngineResult,
    QuestionFeatures,
    SignalFeatures,
)
from ugh_quantamental.schemas.projection import ProjectionSnapshot


def _clamp(value: float, lower: float, upper: float) -> float:
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
    """Compute pre-bias projection signal E_raw in [-1, 1]."""
    fire_component = signal_features.fire_probability * 2.0 - 1.0
    temporal_component = signal_features.technical_score

    numerator = (
        config.u_weight * u_score
        + config.f_weight * fire_component
        + config.t_weight * temporal_component
    )
    denom = config.u_weight + config.f_weight + config.t_weight
    normalized = 0.0 if denom == 0 else numerator / denom
    return _clamp(normalized * alignment, -1.0, 1.0)


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
