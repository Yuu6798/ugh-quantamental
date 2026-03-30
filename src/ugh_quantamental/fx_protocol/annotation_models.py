"""Typed models for external evidence and AI annotation records.

All models are frozen Pydantic v2 models with ``extra="forbid"``
consistent with the repository's schema conventions.

Importable without SQLAlchemy.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ---------------------------------------------------------------------------
# External evidence models
# ---------------------------------------------------------------------------


class ExternalEvidenceItem(BaseModel):
    """A single piece of external evidence (news, release, calendar entry)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    source_kind: Literal[
        "macro_calendar", "news", "official_release",
        "market_note", "holiday_calendar", "other",
    ]
    title: str
    published_at_utc: datetime | None = None
    url: str | None = None
    text: str
    source_ref: str | None = None
    content_hash: str
    window_start_jst: datetime | None = None
    window_end_jst: datetime | None = None

    @field_validator("content_hash")
    @classmethod
    def _content_hash_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content_hash must not be empty")
        return v


def compute_content_hash(text: str) -> str:
    """Compute a deterministic SHA-256 hash prefix for evidence text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class ExternalEvidenceBundle(BaseModel):
    """A collection of evidence items for one or more observation windows."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_id: str
    created_at_utc: datetime
    items: tuple[ExternalEvidenceItem, ...] = ()

    @field_validator("items")
    @classmethod
    def _items_sorted(cls, v: tuple[ExternalEvidenceItem, ...]) -> tuple[ExternalEvidenceItem, ...]:
        return tuple(sorted(v, key=lambda i: i.source_id))


# ---------------------------------------------------------------------------
# AI annotation models
# ---------------------------------------------------------------------------


class AiAnnotationRecord(BaseModel):
    """A single AI-generated annotation for one forecast observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    forecast_id: str
    as_of_jst: datetime
    pair: str
    regime_label: str | None = None
    volatility_label: str | None = None
    intervention_risk: str | None = None
    event_tags: tuple[str, ...] = ()
    failure_reason: str | None = None
    annotation_confidence: float | None = None
    annotation_model_version: str
    annotation_prompt_version: str
    evidence_refs: tuple[str, ...] = ()
    annotation_generated_at_utc: datetime

    @field_validator("event_tags", "evidence_refs")
    @classmethod
    def _sorted_tuples(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(v))

    @field_validator("annotation_confidence")
    @classmethod
    def _confidence_bounded(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("annotation_confidence must be between 0.0 and 1.0")
        return v


class AiAnnotationBatch(BaseModel):
    """A batch of AI annotation records produced in a single run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    batch_id: str
    model_version: str
    prompt_version: str
    generated_at_utc: datetime
    records: tuple[AiAnnotationRecord, ...] = ()

    @field_validator("records")
    @classmethod
    def _records_sorted(cls, v: tuple[AiAnnotationRecord, ...]) -> tuple[AiAnnotationRecord, ...]:
        return tuple(sorted(v, key=lambda r: (r.as_of_jst, r.forecast_id)))


class AiAnnotationSourceSummary(BaseModel):
    """Summary of annotation sources for a weekly report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_observations: int = 0
    ai_annotated_count: int = 0
    auto_annotated_count: int = 0
    manual_annotated_count: int = 0
    unannotated_count: int = 0
    model_versions: tuple[str, ...] = ()
    prompt_versions: tuple[str, ...] = ()
    evidence_ref_count: int = 0

    @model_validator(mode="after")
    def _counts_consistent(self) -> AiAnnotationSourceSummary:
        total = (
            self.ai_annotated_count
            + self.auto_annotated_count
            + self.manual_annotated_count
            + self.unannotated_count
        )
        if total != self.total_observations:
            raise ValueError(
                f"Source counts ({total}) do not sum to total_observations "
                f"({self.total_observations})"
            )
        return self
