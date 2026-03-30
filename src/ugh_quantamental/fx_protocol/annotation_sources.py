"""Annotation source precedence and effective-label resolution.

Defines the AI-first label precedence:
  1. AI annotation labels (primary)
  2. Deterministic auto-derived labels (calendar, outcome tags)
  3. Manual compatibility labels (optional, lowest priority)

Importable without SQLAlchemy.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Annotation source constants
# ---------------------------------------------------------------------------

SOURCE_AI: str = "ai"
SOURCE_AI_PLUS_AUTO: str = "ai_plus_auto"
SOURCE_AUTO_ONLY: str = "auto_only"
SOURCE_MANUAL_COMPAT: str = "manual_compat"
SOURCE_NONE: str = "none"

ANNOTATION_SOURCE_VALUES: tuple[str, ...] = (
    SOURCE_AI, SOURCE_AI_PLUS_AUTO, SOURCE_AUTO_ONLY,
    SOURCE_MANUAL_COMPAT, SOURCE_NONE,
)


# ---------------------------------------------------------------------------
# Effective label resolution
# ---------------------------------------------------------------------------


def resolve_effective_label(
    *,
    ai_value: str,
    auto_value: str,
    manual_value: str,
) -> tuple[str, str]:
    """Return (effective_value, source) using AI-first precedence.

    Priority: ai > auto > manual.
    """
    if ai_value:
        return ai_value, SOURCE_AI
    if auto_value:
        return auto_value, SOURCE_AUTO_ONLY
    if manual_value:
        return manual_value, SOURCE_MANUAL_COMPAT
    return "", SOURCE_NONE


def resolve_effective_event_tags(
    *,
    ai_tags: list[str],
    auto_tags: list[str],
    manual_tags: list[str],
) -> tuple[str, str]:
    """Return (effective_event_tags_str, source) using AI-first precedence.

    For event tags the union is used when AI tags exist, combined with auto.
    Manual tags are only used alone when neither AI nor auto provides any.
    """
    ai_set = set(ai_tags)
    auto_set = set(auto_tags)
    manual_set = set(manual_tags)

    if ai_set and auto_set:
        effective = sorted(ai_set | auto_set)
        source = SOURCE_AI_PLUS_AUTO
    elif ai_set:
        effective = sorted(ai_set)
        source = SOURCE_AI
    elif auto_set:
        effective = sorted(auto_set)
        source = SOURCE_AUTO_ONLY
    elif manual_set:
        effective = sorted(manual_set)
        source = SOURCE_MANUAL_COMPAT
    else:
        effective = []
        source = SOURCE_NONE

    return "|".join(effective), source


def build_annotation_source_summary(
    observations: list[dict[str, str]],
) -> dict[str, Any]:
    """Build annotation_source summary counts from labeled observations."""
    counts: dict[str, int] = {s: 0 for s in ANNOTATION_SOURCE_VALUES}
    model_versions: set[str] = set()
    prompt_versions: set[str] = set()
    evidence_ref_count = 0

    for row in observations:
        src = row.get("annotation_source", SOURCE_NONE).strip()
        if src in counts:
            counts[src] += 1
        else:
            counts[SOURCE_NONE] += 1

        mv = row.get("ai_annotation_model_version", "").strip()
        if mv:
            model_versions.add(mv)
        pv = row.get("ai_annotation_prompt_version", "").strip()
        if pv:
            prompt_versions.add(pv)

        # Count evidence refs (pipe-delimited)
        refs = row.get("ai_evidence_refs", "").strip()
        if refs:
            evidence_ref_count += len([r for r in refs.split("|") if r.strip()])

    total = len(observations)
    ai_count = counts[SOURCE_AI] + counts[SOURCE_AI_PLUS_AUTO]
    auto_count = counts[SOURCE_AUTO_ONLY]
    manual_count = counts[SOURCE_MANUAL_COMPAT]
    unannotated = counts[SOURCE_NONE]

    return {
        "total_observations": total,
        "ai_annotated_count": ai_count,
        "auto_annotated_count": auto_count,
        "manual_annotated_count": manual_count,
        "unannotated_count": unannotated,
        "model_versions": sorted(model_versions),
        "prompt_versions": sorted(prompt_versions),
        "evidence_ref_count": evidence_ref_count,
    }
