"""Pure deterministic review audit engine (Milestone 13).

Implements the six engine functions defined in ``docs/specs/ugh_review_audit_v1.md``:

  compute_por → compute_delta_e → compute_mismatch_score →
  compute_verdict → build_audit_snapshot → run_review_audit_engine

No raw review text enters any function.  All inputs are bounded ``[0, 1]``
floats from ``ReviewIntentFeatures`` / ``FixActionFeatures``.  All outputs are
deterministic: identical inputs always produce identical outputs.
"""
from __future__ import annotations

from .review_audit_models import (
    FixActionFeatures,
    ReviewAuditConfig,
    ReviewAuditEngineResult,
    ReviewAuditSnapshot,
    ReviewIntentFeatures,
)

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _clamp01(value: float) -> float:
    """Clamp *value* to ``[0.0, 1.0]``."""
    return max(0.0, min(1.0, value))


def _safe_weight_total(config: ReviewAuditConfig) -> float:
    """Return the sum of all four PoR weights.

    Always positive because each weight has ``gt=0.0`` validation on the model.
    """
    return config.w_clarity + config.w_locality + config.w_mechanical + config.w_scope


def _weighted_l1_distance(
    intent_vector: list[float],
    action_vector: list[float],
    weights: list[float],
) -> float:
    """Compute the weighted L1 distance between two equal-length float vectors.

    The result is **not** normalised here; callers must clamp if needed.
    """
    return sum(w * abs(iv - av) for w, iv, av in zip(weights, intent_vector, action_vector))


# ---------------------------------------------------------------------------
# Engine functions (spec §§ 1–6)
# ---------------------------------------------------------------------------


def compute_por(intent: ReviewIntentFeatures, config: ReviewAuditConfig) -> float:
    """Compute the Probability of Relevance (PoR).

    PoR measures the probability that the bot can perform a semantically
    relevant fix, integrating clarity, locality, mechanicalness, and
    scope-boundness.

    Formula (spec §1)::

        w_total = w_clarity + w_locality + w_mechanical + w_scope
        por = (  w_clarity    * intent_clarity
               + w_locality   * locality_strength
               + w_mechanical * mechanicalness
               + w_scope      * scope_boundness
             ) / w_total
        por = clamp(por, 0.0, 1.0)

    Returns:
        PoR value in ``[0.0, 1.0]``.
    """
    w_total = _safe_weight_total(config)
    raw = (
        config.w_clarity * intent.intent_clarity
        + config.w_locality * intent.locality_strength
        + config.w_mechanical * intent.mechanicalness
        + config.w_scope * intent.scope_boundness
    ) / w_total
    return _clamp01(raw)


def compute_delta_e(
    intent: ReviewIntentFeatures,
    action: FixActionFeatures | None,
    config: ReviewAuditConfig,  # noqa: ARG001 — reserved for future per-component weights
) -> float | None:
    """Compute ΔE (semantic divergence between intent and applied action).

    **If ``action is None``**: returns ``None``.  Absence of action data is not
    the same as zero divergence; ``None`` is distinct from ``0.0``.

    Formula (spec §2)::

        intent_vector = [
            intent.locality_strength,
            intent.mechanicalness,
            intent.scope_boundness,
            intent.validation_intensity,
        ]
        action_vector = [
            action.target_file_match,
            action.diff_hunk_overlap,
            1.0 - min(1.0, action.scope_ratio),   # inverted
            action.validation_scope_executed,
        ]
        weights = [0.25, 0.25, 0.25, 0.25]        # uniform in v1
        delta_e = clamp(weighted_L1(intent, action, weights), 0.0, 1.0)

    Returns:
        ΔE in ``[0.0, 1.0]``, or ``None`` when *action* is absent.
    """
    if action is None:
        return None

    intent_vector: list[float] = [
        intent.locality_strength,
        intent.mechanicalness,
        intent.scope_boundness,
        intent.validation_intensity,
    ]
    action_vector: list[float] = [
        action.target_file_match,
        action.diff_hunk_overlap,
        1.0 - min(1.0, action.scope_ratio),  # inverted: tight scope = more aligned
        action.validation_scope_executed,
    ]
    weights: list[float] = [0.25, 0.25, 0.25, 0.25]

    return _clamp01(_weighted_l1_distance(intent_vector, action_vector, weights))


def compute_mismatch_score(por: float, delta_e: float | None) -> float | None:
    """Compute the composite mismatch score.

    Formula (spec §3)::

        if delta_e is None:
            return None
        return clamp(0.5 * (1.0 - por) + 0.5 * delta_e, 0.0, 1.0)

    Returns:
        Mismatch score in ``[0.0, 1.0]``, or ``None`` when *delta_e* is absent.
    """
    if delta_e is None:
        return None
    return _clamp01(0.5 * (1.0 - por) + 0.5 * delta_e)


def compute_verdict(
    por: float,
    delta_e: float | None,
    action: FixActionFeatures | None,
) -> str:
    """Compute the audit verdict.

    Rules are evaluated top-to-bottom; the first matching rule wins (spec §4):

    +-----------------------------------+---------------------+
    | Condition                         | Verdict             |
    +===================================+=====================+
    | ``action is None``                | ``insufficient_data``|
    +-----------------------------------+---------------------+
    | ``por >= 0.7 and delta_e <= 0.2`` | ``aligned``         |
    +-----------------------------------+---------------------+
    | ``por < 0.4 or delta_e > 0.6``   | ``misaligned``      |
    +-----------------------------------+---------------------+
    | otherwise                         | ``marginal``        |
    +-----------------------------------+---------------------+

    Returns:
        One of ``"aligned"``, ``"marginal"``, ``"misaligned"``,
        ``"insufficient_data"``.
    """
    if action is None:
        return "insufficient_data"
    # delta_e is guaranteed to be float (not None) here because action is not None
    assert delta_e is not None  # guarded by action is not None invariant
    if por >= 0.7 and delta_e <= 0.2:
        return "aligned"
    if por < 0.4 or delta_e > 0.6:
        return "misaligned"
    return "marginal"


def build_audit_snapshot(
    audit_id: str,
    por: float,
    delta_e: float | None,
    mismatch_score: float | None,
    verdict: str,
) -> ReviewAuditSnapshot:
    """Assemble a bounds-safe ``ReviewAuditSnapshot``.

    All scalar fields are clamped to their declared ranges before construction.
    ``delta_e`` and ``mismatch_score`` are passed through as-is when ``None``.

    Returns:
        A frozen ``ReviewAuditSnapshot`` instance.
    """
    return ReviewAuditSnapshot(
        audit_id=audit_id,
        por=_clamp01(por),
        delta_e=_clamp01(delta_e) if delta_e is not None else None,
        mismatch_score=_clamp01(mismatch_score) if mismatch_score is not None else None,
        verdict=verdict,
    )


def run_review_audit_engine(
    audit_id: str,
    intent: ReviewIntentFeatures,
    action: FixActionFeatures | None,
    config: ReviewAuditConfig,
) -> ReviewAuditEngineResult:
    """Pure deterministic end-to-end composition of the review audit engine.

    Executes the full pipeline (spec §6)::

        por            = compute_por(intent, config)
        delta_e        = compute_delta_e(intent, action, config)
        mismatch_score = compute_mismatch_score(por, delta_e)
        verdict        = compute_verdict(por, delta_e, action)
        snapshot       = build_audit_snapshot(audit_id, por, delta_e, mismatch_score, verdict)
        return ReviewAuditEngineResult(
            audit_snapshot  = snapshot,
            intent_features = intent,
            action_features = action,
            config          = config,
        )

    No raw review text is consumed.  Same inputs always produce the same output.

    Args:
        audit_id: Unique identifier for this audit run.
        intent:   Pre-computed intent feature vector from the extractor.
        action:   Post-execution action feature vector, or ``None``.
        config:   Weight and version configuration.

    Returns:
        A frozen ``ReviewAuditEngineResult`` bundle.
    """
    por = compute_por(intent, config)
    delta_e = compute_delta_e(intent, action, config)
    mismatch_score = compute_mismatch_score(por, delta_e)
    verdict = compute_verdict(por, delta_e, action)
    snapshot = build_audit_snapshot(audit_id, por, delta_e, mismatch_score, verdict)
    return ReviewAuditEngineResult(
        audit_snapshot=snapshot,
        intent_features=intent,
        action_features=action,
        config=config,
    )
