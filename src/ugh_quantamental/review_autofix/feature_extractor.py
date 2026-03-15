"""Deterministic feature extraction pipeline for PR review semantic audit.

Three-layer extraction:
  ReviewContext -> ReviewObservation (symbolic) -> ReviewIntentFeatures ([0,1] floats)

The canonical ``ReviewObservation`` and ``ReviewIntentFeatures`` models now live
in ``engine/review_audit_models.py`` (added in Milestone 3).  They are
re-exported from this module so that existing callers continue to work without
modification.
"""
from __future__ import annotations

from ugh_quantamental.engine.review_audit_models import (
    ReviewIntentFeatures,
    ReviewObservation,
)

from .classifier import _AUTO_KEYWORDS, _SKIP_KEYWORDS, extract_priority
from .models import ReviewContext

# Re-export canonical models for backwards-compatible imports.
__all__ = [
    "ReviewObservation",
    "ReviewIntentFeatures",
    "extract_review_observation",
    "extract_review_intent_features",
    "extract_review_features",
]

# ---------------------------------------------------------------------------
# Keyword lookup tables used by extract_review_observation
# ---------------------------------------------------------------------------

_BEHAVIOR_PRESERVATION_KEYWORDS: tuple[str, ...] = (
    "preserve",
    "behavior",
    "existing",
    "compat",
    "backward",
    "既存",
    "互換",
)

_SCOPE_LIMIT_KEYWORDS: tuple[str, ...] = (
    "minimal",
    "only",
    "scope",
    "small",
    "limited",
    "最小",
    "のみ",
    "限定",
)

_AMBIGUITY_KEYWORDS: tuple[str, ...] = (
    "should",
    "consider",
    "suggest",
    "maybe",
    "提案",
    "検討",
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _contains_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    """Return True if *text* contains at least one keyword (substring match)."""
    return any(kw in text for kw in keywords)


def _count_keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    """Return the number of distinct keywords found in *text* (0 or 1 each)."""
    return sum(1 for kw in keywords if kw in text)


def _priority_score(priority: str) -> float:
    """Map a priority string to a [0, 1] score."""
    return {"P0": 1.00, "P1": 0.75, "P2": 0.50, "P3": 0.25}.get(priority, 0.50)


def _clamp01(value: float) -> float:
    """Clamp *value* to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------


def extract_review_observation(context: ReviewContext) -> ReviewObservation:
    """Convert a raw ``ReviewContext`` into a symbolic ``ReviewObservation``.

    All mappings are deterministic substring / attribute checks; no I/O or
    randomness is involved.
    """
    # Normalise body for ASCII keywords; Japanese keywords are unaffected.
    body_lower = context.body.lower()

    priority = extract_priority(context.body)

    mechanical_keyword_hits = _count_keyword_hits(body_lower, _AUTO_KEYWORDS)
    skip_keyword_hits = _count_keyword_hits(body_lower, _SKIP_KEYWORDS)

    # Behavior/scope/ambiguity signals use the lower-cased body for ASCII
    # keywords; Japanese keywords work on the original too (lower() is no-op).
    behavior_preservation_signal = _contains_any_keyword(
        body_lower, _BEHAVIOR_PRESERVATION_KEYWORDS
    )
    scope_limit_signal = _contains_any_keyword(body_lower, _SCOPE_LIMIT_KEYWORDS)
    ambiguity_signal_count = _count_keyword_hits(body_lower, _AMBIGUITY_KEYWORDS)

    return ReviewObservation(
        has_path_hint=context.path is not None,
        has_line_anchor=context.line is not None or context.start_line is not None,
        has_diff_hunk=context.diff_hunk is not None,
        priority=priority,
        mechanical_keyword_hits=mechanical_keyword_hits,
        skip_keyword_hits=skip_keyword_hits,
        behavior_preservation_signal=behavior_preservation_signal,
        scope_limit_signal=scope_limit_signal,
        ambiguity_signal_count=ambiguity_signal_count,
        target_file_present=context.path is not None,
        review_kind=context.kind.value,
    )


def extract_review_intent_features(obs: ReviewObservation) -> ReviewIntentFeatures:
    """Convert a ``ReviewObservation`` into normalised ``ReviewIntentFeatures``.

    All formulas are deterministic and produce values in [0, 1].
    """
    path_bit = 1.0 if obs.has_path_hint else 0.0
    line_bit = 1.0 if obs.has_line_anchor else 0.0
    hunk_bit = 1.0 if obs.has_diff_hunk else 0.0
    p_score = _priority_score(obs.priority)

    # intent_clarity: weighted average of four structural signals
    intent_clarity = _clamp01(
        path_bit * 0.35 + line_bit * 0.25 + hunk_bit * 0.20 + p_score * 0.20
    )

    # locality_strength: how precisely the comment is anchored to a location
    locality_strength = _clamp01(line_bit * 0.60 + hunk_bit * 0.40)

    # mechanicalness: keyword density minus skip-keyword penalty
    mech_base = min(1.0, obs.mechanical_keyword_hits / 3.0)
    mech_penalty = min(0.5, obs.skip_keyword_hits / 4.0)
    mechanicalness = _clamp01(mech_base - mech_penalty)

    # scope_boundness: structural + scope signals minus ambiguity / skip drag
    scope_raw = (
        0.0
        + (0.5 if obs.scope_limit_signal else 0.0)
        + (0.3 if obs.has_line_anchor else 0.0)
        + (0.2 if obs.has_diff_hunk else 0.0)
        - 0.15 * min(obs.ambiguity_signal_count, 2)
        - 0.10 * min(obs.skip_keyword_hits, 2)
    )
    scope_boundness = _clamp01(scope_raw)

    # semantic_change_risk: ambiguity + skip pressure, modest reduction for
    # behavior-preservation signal (preservation = safer, not zero-risk)
    risk_raw = (
        0.20 * min(obs.ambiguity_signal_count, 3) / 3.0
        + 0.30 * min(obs.skip_keyword_hits, 2) / 2.0
        + (0.30 if obs.skip_keyword_hits > 0 else 0.10)
        - (0.10 if obs.behavior_preservation_signal else 0.0)
    )
    semantic_change_risk = _clamp01(risk_raw)

    # validation_intensity: driven by risk and inversely by mechanicalness
    val_raw = (
        semantic_change_risk * 0.50
        + (1.0 - scope_boundness) * 0.25
        + (1.0 - mechanicalness) * 0.25
    )
    validation_intensity = _clamp01(val_raw)

    return ReviewIntentFeatures(
        intent_clarity=intent_clarity,
        locality_strength=locality_strength,
        mechanicalness=mechanicalness,
        scope_boundness=scope_boundness,
        semantic_change_risk=semantic_change_risk,
        validation_intensity=validation_intensity,
    )


def extract_review_features(
    context: ReviewContext,
) -> tuple[ReviewObservation, ReviewIntentFeatures]:
    """Convenience wrapper: extract both observation and features in one call.

    Returns ``(ReviewObservation, ReviewIntentFeatures)`` deterministically
    from the supplied ``ReviewContext``.
    """
    obs = extract_review_observation(context)
    features = extract_review_intent_features(obs)
    return obs, features
