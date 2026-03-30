"""AI annotation execution boundary for the FX Daily Protocol.

Provides a narrow abstraction for AI-powered annotation generation.
Does NOT hard-code any vendor SDK — accepts an injected callable adapter.
Tests use a deterministic fake adapter.

The module defines:
- Request/response shapes for annotation generation
- Deterministic merge logic for AI annotations into observation rows
- Provenance tracking
- Output validation

Importable without SQLAlchemy.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from ugh_quantamental.fx_protocol.annotation_models import (
    AiAnnotationBatch,
    AiAnnotationRecord,
    ExternalEvidenceBundle,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type alias for the AI annotation adapter
# ---------------------------------------------------------------------------

AiAnnotationAdapter = Callable[
    [list[dict[str, str]], ExternalEvidenceBundle | None],
    AiAnnotationBatch,
]
"""Callable that takes observation rows + optional evidence and returns
an AI annotation batch.  Tests inject a deterministic fake."""


# ---------------------------------------------------------------------------
# Deterministic fake adapter (for testing and fallback)
# ---------------------------------------------------------------------------


def make_deterministic_adapter(
    *,
    model_version: str = "deterministic-v1",
    prompt_version: str = "deterministic-p1",
    generated_at_utc: datetime | None = None,
) -> AiAnnotationAdapter:
    """Create a deterministic fake AI adapter for testing.

    Derives labels from existing evaluation data in the observation rows:
    - regime_label: based on direction_hit rate of ugh forecasts per as_of_jst
    - volatility_label: based on close_error_bp magnitude
    - intervention_risk: based on realized_close_change_bp magnitude
    - event_tags: from effective_event_tags or auto_event_tags if present
    - failure_reason: set when direction_hit is False for ugh strategy
    """

    def _adapter(
        observations: list[dict[str, str]],
        evidence: ExternalEvidenceBundle | None,
    ) -> AiAnnotationBatch:
        from datetime import timezone

        ts = generated_at_utc or datetime.now(timezone.utc)
        records: list[AiAnnotationRecord] = []

        # One record per observation, keyed by forecast_id.
        # Skip rows without a distinct forecast_id to avoid key collisions.
        for obs in observations:
            forecast_id = obs.get("forecast_id", "")
            if not forecast_id:
                continue
            as_of_str = obs.get("as_of_jst", "")
            try:
                as_of = datetime.fromisoformat(as_of_str)
            except (ValueError, TypeError):
                continue

            # Derive regime from direction hit
            hit = obs.get("direction_hit", "").lower() in ("true", "1", "yes")
            regime = "trending" if hit else "choppy"

            # Derive volatility from close error
            try:
                err = abs(float(obs.get("close_error_bp", "0")))
            except (ValueError, TypeError):
                err = 0.0
            vol = "high" if err > 50 else ("normal" if err > 20 else "low")

            # Derive intervention risk from realized change
            try:
                change = abs(float(obs.get("realized_close_change_bp", "0")))
            except (ValueError, TypeError):
                change = 0.0
            ir = "high" if change > 100 else ("medium" if change > 50 else "low")

            # Event tags from existing effective tags
            existing_tags = obs.get("effective_event_tags", "") or obs.get("auto_event_tags", "")
            tags = tuple(sorted(t.strip() for t in existing_tags.split("|") if t.strip()))

            # Failure reason
            strategy = obs.get("strategy_kind", "")
            failure = None
            if strategy == "ugh" and not hit:
                failure = "direction_miss"

            # Evidence refs
            evidence_refs: tuple[str, ...] = ()
            if evidence and evidence.items:
                evidence_refs = tuple(sorted(i.source_id for i in evidence.items))

            records.append(AiAnnotationRecord(
                forecast_id=forecast_id,
                as_of_jst=as_of,
                pair=obs.get("pair", "USDJPY"),
                regime_label=regime,
                volatility_label=vol,
                intervention_risk=ir,
                event_tags=tags,
                failure_reason=failure,
                annotation_confidence=0.8,
                annotation_model_version=model_version,
                annotation_prompt_version=prompt_version,
                evidence_refs=evidence_refs,
                annotation_generated_at_utc=ts,
            ))

        return AiAnnotationBatch(
            batch_id=f"ai_batch_{ts.strftime('%Y%m%dT%H%M%S')}",
            model_version=model_version,
            prompt_version=prompt_version,
            generated_at_utc=ts,
            records=tuple(records),
        )

    return _adapter


# ---------------------------------------------------------------------------
# AI annotation batch to dict rows (for CSV merge)
# ---------------------------------------------------------------------------


def ai_batch_to_lookup(
    batch: AiAnnotationBatch,
) -> dict[str, dict[str, str]]:
    """Convert an AI annotation batch to a lookup keyed by forecast_id.

    Returns flat string dicts suitable for merging into labeled observation rows.
    """
    result: dict[str, dict[str, str]] = {}
    for rec in batch.records:
        result[rec.forecast_id] = {
            "ai_regime_label": rec.regime_label or "",
            "ai_volatility_label": rec.volatility_label or "",
            "ai_intervention_risk": rec.intervention_risk or "",
            "ai_event_tags": "|".join(rec.event_tags),
            "ai_failure_reason": rec.failure_reason or "",
            "ai_annotation_confidence": (
                str(rec.annotation_confidence) if rec.annotation_confidence is not None else ""
            ),
            "ai_annotation_model_version": rec.annotation_model_version,
            "ai_annotation_prompt_version": rec.annotation_prompt_version,
            "ai_evidence_refs": "|".join(rec.evidence_refs),
            "ai_annotation_status": "generated",
        }
    return result


def run_ai_annotation_pass(
    observations: list[dict[str, str]],
    adapter: AiAnnotationAdapter | None = None,
    evidence: ExternalEvidenceBundle | None = None,
    *,
    generated_at_utc: datetime | None = None,
) -> AiAnnotationBatch | None:
    """Run AI annotation on observation rows using the given adapter.

    If no adapter is provided, uses the deterministic fake.
    Returns the batch, or None on failure.
    """
    if adapter is None:
        adapter = make_deterministic_adapter(generated_at_utc=generated_at_utc)

    try:
        return adapter(observations, evidence)
    except Exception:
        logger.warning("AI annotation pass failed (non-fatal).", exc_info=True)
        return None
