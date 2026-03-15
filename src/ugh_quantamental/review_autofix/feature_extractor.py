"""Deterministic feature extraction pipeline for PR review semantic audit.

Three-layer extraction:
  ReviewContext -> ReviewObservation (symbolic) -> ReviewIntentFeatures ([0,1] floats)

These local Pydantic model definitions are intended to be moved to
``engine/review_audit_models.py`` in Milestone 3. Naming and docstrings are
written to survive that migration without changes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .classifier import _AUTO_KEYWORDS, _SKIP_KEYWORDS, extract_priority
from .models import ReviewContext

# ---------------------------------------------------------------------------
# Symbolic-layer model (will migrate to engine/review_audit_models.py in M13)
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


class ReviewObservation(BaseModel):
    """Symbolic representation of a raw ``ReviewContext``.

    All fields are derived deterministically from ``ReviewContext`` without
    any external I/O or randomness.  Intended as the intermediate layer
    between raw GitHub event data and the numeric ``ReviewIntentFeatures``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    has_path_hint: bool
    """True when ``context.path`` is not ``None``."""

    has_line_anchor: bool
    """True when at least one of ``context.line`` or ``context.start_line`` is set."""

    has_diff_hunk: bool
    """True when ``context.diff_hunk`` is not ``None``."""

    priority: str
    """Priority extracted from the review body — one of P0/P1/P2/P3."""

    mechanical_keyword_hits: int = Field(ge=0)
    """Number of distinct ``_AUTO_KEYWORDS`` found in the lower-cased body."""

    skip_keyword_hits: int = Field(ge=0)
    """Number of distinct ``_SKIP_KEYWORDS`` found in the lower-cased body."""

    behavior_preservation_signal: bool
    """True when the body contains any behavior-preservation keyword."""

    scope_limit_signal: bool
    """True when the body contains any scope-limiting keyword."""

    ambiguity_signal_count: int = Field(ge=0)
    """Number of distinct ambiguity keywords found in the body."""

    target_file_present: bool
    """True when ``context.path`` is not ``None`` (alias of ``has_path_hint``)."""

    review_kind: str
    """String value of ``context.kind`` — ``"diff_comment"`` or ``"review_body"``."""


# ---------------------------------------------------------------------------
# Numeric-layer model (will migrate to engine/review_audit_models.py in M13)
# ---------------------------------------------------------------------------


class ReviewIntentFeatures(BaseModel):
    """Normalised [0, 1] feature vector for the review audit engine.

    All fields are derived deterministically from a ``ReviewObservation``
    without any external I/O or randomness.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_clarity: float = Field(ge=0.0, le=1.0)
    """Weighted average of structural signals and extracted priority."""

    locality_strength: float = Field(ge=0.0, le=1.0)
    """How precisely the comment targets a specific code location."""

    mechanicalness: float = Field(ge=0.0, le=1.0)
    """Degree to which the comment requests a mechanical / automatable change."""

    scope_boundness: float = Field(ge=0.0, le=1.0)
    """How well-scoped / contained the requested change appears to be."""

    semantic_change_risk: float = Field(ge=0.0, le=1.0)
    """Estimated risk of semantic drift from applying the suggested change."""

    validation_intensity: float = Field(ge=0.0, le=1.0)
    """Suggested depth of validation needed before accepting the change."""


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
