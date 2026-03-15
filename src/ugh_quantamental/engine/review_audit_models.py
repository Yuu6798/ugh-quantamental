"""Typed model contracts for the PR Review Semantic Audit Engine (Milestone 13).

These are the canonical Pydantic models consumed and produced by
``engine/review_audit.py``.  The extractor in
``review_autofix/feature_extractor.py`` imports ``ReviewObservation`` and
``ReviewIntentFeatures`` from here rather than defining them locally.

All models use ``extra="forbid", frozen=True`` to enforce immutability and
prevent accidental field additions.
"""
from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewObservation(BaseModel):
    """Symbolic intermediate layer produced by ``extract_review_observation``.

    Stored in ``observation_json`` for extractor replay.  Never passed directly
    into the engine — it is first normalised into ``ReviewIntentFeatures``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    has_path_hint: bool
    """True when ``context.path`` is not ``None``."""

    has_line_anchor: bool
    """True when at least one of ``context.line`` / ``context.start_line`` is set."""

    has_diff_hunk: bool
    """True when ``context.diff_hunk`` is not ``None``."""

    priority: str
    """Priority extracted from the review body — one of ``P0 | P1 | P2 | P3``."""

    mechanical_keyword_hits: int = Field(ge=0)
    """Number of distinct ``_AUTO_KEYWORDS`` tokens found in the (lowercased) body."""

    skip_keyword_hits: int = Field(ge=0)
    """Number of distinct ``_SKIP_KEYWORDS`` tokens found in the (lowercased) body."""

    behavior_preservation_signal: bool
    """True when the body contains any behavior-preservation keyword."""

    scope_limit_signal: bool
    """True when the body contains any scope-limiting keyword."""

    ambiguity_signal_count: int = Field(ge=0)
    """Number of distinct ambiguity-indicating keywords found in the body."""

    target_file_present: bool
    """True when ``context.path`` is not ``None`` (alias of ``has_path_hint``)."""

    review_kind: str
    """String value of ``context.kind`` — ``"diff_comment"`` or ``"review_body"``."""


class ReviewIntentFeatures(BaseModel):
    """Normalised ``[0, 1]`` feature vector derived from ``ReviewObservation``.

    Consumed by ``compute_por`` and ``compute_delta_e`` as the *intent* side of
    the audit computation.  All fields are clamped to ``[0.0, 1.0]`` by the
    extractor before construction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_clarity: float = Field(ge=0.0, le=1.0)
    """Weighted combination of priority, path hint, line anchor, and diff hunk presence."""

    locality_strength: float = Field(ge=0.0, le=1.0)
    """How precisely the comment targets a specific code location."""

    mechanicalness: float = Field(ge=0.0, le=1.0)
    """Degree to which the comment requests a mechanical / automatable change."""

    scope_boundness: float = Field(ge=0.0, le=1.0)
    """How well-scoped / contained the requested change appears to be."""

    semantic_change_risk: float = Field(ge=0.0, le=1.0)
    """Estimated risk of unintended behavioural change from applying the fix."""

    validation_intensity: float = Field(ge=0.0, le=1.0)
    """Implied depth of validation the fix requires."""


class FixActionFeatures(BaseModel):
    """Post-execution feature vector describing what the bot actually applied.

    Absent (``None``) in detect_only / propose_only modes and in any pre-action
    audit invocation.  When absent, ``delta_e`` and ``mismatch_score`` are
    ``None`` and the verdict is ``"insufficient_data"``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    changed: bool
    """Whether the executor produced any change to the working tree."""

    validation_ok: bool
    """Whether the post-fix validation pass succeeded."""

    lines_changed: int = Field(ge=0)
    """Raw number of lines changed by the applied fix."""

    files_changed: int = Field(ge=0)
    """Raw number of files touched by the applied fix."""

    target_file_match: float = Field(ge=0.0, le=1.0)
    """Degree to which the fix touched the file the reviewer referenced."""

    line_anchor_touched: float = Field(ge=0.0, le=1.0)
    """Degree to which the fix touched the line / hunk the reviewer referenced."""

    diff_hunk_overlap: float = Field(ge=0.0, le=1.0)
    """Overlap between the applied diff and the reviewer's diff hunk."""

    scope_ratio: float = Field(ge=0.0, le=1.0)
    """Fix scope relative to intent (0.0 = tight / focused, 1.0 = broad)."""

    validation_scope_executed: float = Field(ge=0.0, le=1.0)
    """Breadth of validation actually run after the fix."""

    behavior_preservation_proxy: float = Field(ge=0.0, le=1.0)
    """Estimated probability that existing behaviour was preserved."""

    execution_status: str
    """Outcome of the executor: ``"succeeded" | "no_op" | "failed" | "timeout" | "skipped"``."""


class ReviewAuditConfig(BaseModel):
    """Configuration governing ``compute_por`` weight normalisation.

    The four weights are not required to sum to exactly 1.0; ``compute_por``
    normalises by their total internally.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    w_clarity: float = Field(default=0.30, gt=0.0)
    """Weight applied to ``intent_clarity`` in PoR computation."""

    w_locality: float = Field(default=0.25, gt=0.0)
    """Weight applied to ``locality_strength`` in PoR computation."""

    w_mechanical: float = Field(default=0.20, gt=0.0)
    """Weight applied to ``mechanicalness`` in PoR computation."""

    w_scope: float = Field(default=0.25, gt=0.0)
    """Weight applied to ``scope_boundness`` in PoR computation."""

    @field_validator("w_clarity", "w_locality", "w_mechanical", "w_scope")
    @classmethod
    def _weight_must_be_finite(cls, v: float) -> float:
        """Reject ``inf`` and ``nan`` weights.

        ``gt=0.0`` already blocks non-positive values; this validator
        additionally blocks non-finite ones so that ``compute_por`` cannot
        produce ``inf / inf = nan`` (which ``_clamp01`` would silently convert
        to ``1.0``, corrupting downstream audit metrics).
        """
        if not math.isfinite(v):
            raise ValueError(f"PoR weight must be a finite positive number, got {v!r}")
        return v

    extractor_version: str = "v1"
    """Tracks which keyword / rule set was active when the observation was produced."""

    feature_spec_version: str = "v1"
    """Tracks which normalization formula set was active when intent features were computed."""


class ReviewAuditSnapshot(BaseModel):
    """Output contract of the review audit engine — one record per audit run.

    ``delta_e`` and ``mismatch_score`` are ``None`` when ``FixActionFeatures``
    was absent (detect_only / propose_only / pre-action modes).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    audit_id: str
    """Unique identifier for this audit run."""

    por: float = Field(ge=0.0, le=1.0)
    """Probability of Relevance — likelihood the bot can address the reviewer's intent."""

    delta_e: float | None = Field(default=None, ge=0.0, le=1.0)
    """Semantic divergence between intent and applied action.  ``None`` when action absent."""

    mismatch_score: float | None = Field(default=None, ge=0.0, le=1.0)
    """Composite mismatch score derived from PoR and ΔE.  ``None`` when action absent."""

    verdict: str
    """Audit outcome: ``"aligned" | "marginal" | "misaligned" | "insufficient_data"``."""


class ReviewAuditEngineResult(BaseModel):
    """Full engine result bundle returned by ``run_review_audit_engine``.

    Stored in ``engine_result_json`` for engine replay.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    audit_snapshot: ReviewAuditSnapshot
    """The computed audit output contract."""

    intent_features: ReviewIntentFeatures
    """The intent feature vector used as engine input."""

    action_features: FixActionFeatures | None
    """The action feature vector used as engine input, or ``None`` if absent."""

    config: ReviewAuditConfig
    """The config under which the engine was run."""
