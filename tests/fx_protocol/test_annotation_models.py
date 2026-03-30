"""Tests for annotation_models.py — typed evidence and AI annotation models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ugh_quantamental.fx_protocol.annotation_models import (
    AiAnnotationBatch,
    AiAnnotationRecord,
    AiAnnotationSourceSummary,
    ExternalEvidenceBundle,
    ExternalEvidenceItem,
    compute_content_hash,
)

_UTC = timezone.utc
_NOW = datetime(2026, 3, 20, 6, 0, 0, tzinfo=_UTC)
_AS_OF = datetime(2026, 3, 18, 8, 0, 0, tzinfo=_UTC)


class TestExternalEvidenceItem:
    def test_valid_item(self) -> None:
        item = ExternalEvidenceItem(
            source_id="news-001",
            source_kind="news",
            title="Fed holds rates",
            text="The Federal Reserve held rates steady.",
            content_hash="abc123",
        )
        assert item.source_id == "news-001"
        assert item.source_kind == "news"

    def test_empty_content_hash_rejected(self) -> None:
        with pytest.raises(ValueError, match="content_hash must not be empty"):
            ExternalEvidenceItem(
                source_id="x", source_kind="news", title="x",
                text="x", content_hash="  ",
            )

    def test_frozen(self) -> None:
        item = ExternalEvidenceItem(
            source_id="x", source_kind="other", title="x",
            text="x", content_hash="abc",
        )
        with pytest.raises(Exception):
            item.source_id = "y"  # type: ignore[misc]

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(Exception):
            ExternalEvidenceItem(
                source_id="x", source_kind="news", title="x",
                text="x", content_hash="abc", extra_field="bad",  # type: ignore[call-arg]
            )


class TestExternalEvidenceBundle:
    def test_items_sorted_by_source_id(self) -> None:
        b = ExternalEvidenceBundle(
            bundle_id="b1", created_at_utc=_NOW,
            items=(
                ExternalEvidenceItem(
                    source_id="z", source_kind="news", title="z",
                    text="z", content_hash="z1",
                ),
                ExternalEvidenceItem(
                    source_id="a", source_kind="news", title="a",
                    text="a", content_hash="a1",
                ),
            ),
        )
        assert b.items[0].source_id == "a"
        assert b.items[1].source_id == "z"


class TestComputeContentHash:
    def test_deterministic(self) -> None:
        h1 = compute_content_hash("hello")
        h2 = compute_content_hash("hello")
        assert h1 == h2
        assert len(h1) == 16

    def test_different_input(self) -> None:
        assert compute_content_hash("a") != compute_content_hash("b")


class TestAiAnnotationRecord:
    def test_valid_record(self) -> None:
        rec = AiAnnotationRecord(
            forecast_id="fc-001",
            as_of_jst=_AS_OF,
            pair="USDJPY",
            regime_label="trending",
            event_tags=("fomc", "cpi_us"),
            annotation_confidence=0.85,
            annotation_model_version="v1",
            annotation_prompt_version="p1",
            annotation_generated_at_utc=_NOW,
        )
        assert rec.event_tags == ("cpi_us", "fomc")  # sorted

    def test_confidence_bounded(self) -> None:
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            AiAnnotationRecord(
                forecast_id="fc-001", as_of_jst=_AS_OF, pair="USDJPY",
                annotation_confidence=1.5,
                annotation_model_version="v1", annotation_prompt_version="p1",
                annotation_generated_at_utc=_NOW,
            )

    def test_evidence_refs_sorted(self) -> None:
        rec = AiAnnotationRecord(
            forecast_id="fc-001", as_of_jst=_AS_OF, pair="USDJPY",
            evidence_refs=("ref-z", "ref-a"),
            annotation_model_version="v1", annotation_prompt_version="p1",
            annotation_generated_at_utc=_NOW,
        )
        assert rec.evidence_refs == ("ref-a", "ref-z")


class TestAiAnnotationBatch:
    def test_records_sorted(self) -> None:
        r1 = AiAnnotationRecord(
            forecast_id="fc-002", as_of_jst=_AS_OF, pair="USDJPY",
            annotation_model_version="v1", annotation_prompt_version="p1",
            annotation_generated_at_utc=_NOW,
        )
        r2 = AiAnnotationRecord(
            forecast_id="fc-001", as_of_jst=_AS_OF, pair="USDJPY",
            annotation_model_version="v1", annotation_prompt_version="p1",
            annotation_generated_at_utc=_NOW,
        )
        batch = AiAnnotationBatch(
            batch_id="b1", model_version="v1", prompt_version="p1",
            generated_at_utc=_NOW, records=(r1, r2),
        )
        assert batch.records[0].forecast_id == "fc-001"
        assert batch.records[1].forecast_id == "fc-002"


class TestAiAnnotationSourceSummary:
    def test_counts_must_sum(self) -> None:
        s = AiAnnotationSourceSummary(
            total_observations=10,
            ai_annotated_count=5,
            auto_annotated_count=3,
            manual_annotated_count=1,
            unannotated_count=1,
        )
        assert s.total_observations == 10

    def test_counts_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError, match="do not sum"):
            AiAnnotationSourceSummary(
                total_observations=10,
                ai_annotated_count=5,
                auto_annotated_count=3,
                manual_annotated_count=1,
                unannotated_count=0,
            )
