"""Tests for engine.review_audit_models — schema validation and immutability."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from ugh_quantamental.engine.review_audit_models import (
    FixActionFeatures,
    ReviewAuditConfig,
    ReviewAuditEngineResult,
    ReviewAuditSnapshot,
    ReviewIntentFeatures,
    ReviewObservation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _intent(
    intent_clarity: float = 0.5,
    locality_strength: float = 0.5,
    mechanicalness: float = 0.5,
    scope_boundness: float = 0.5,
    semantic_change_risk: float = 0.2,
    validation_intensity: float = 0.3,
) -> ReviewIntentFeatures:
    return ReviewIntentFeatures(
        intent_clarity=intent_clarity,
        locality_strength=locality_strength,
        mechanicalness=mechanicalness,
        scope_boundness=scope_boundness,
        semantic_change_risk=semantic_change_risk,
        validation_intensity=validation_intensity,
    )


def _action(
    target_file_match: float = 0.8,
    diff_hunk_overlap: float = 0.7,
    scope_ratio: float = 0.2,
    validation_scope_executed: float = 0.6,
) -> FixActionFeatures:
    return FixActionFeatures(
        changed=True,
        validation_ok=True,
        lines_changed=5,
        files_changed=1,
        target_file_match=target_file_match,
        line_anchor_touched=0.9,
        diff_hunk_overlap=diff_hunk_overlap,
        scope_ratio=scope_ratio,
        validation_scope_executed=validation_scope_executed,
        behavior_preservation_proxy=0.8,
        execution_status="succeeded",
    )


# ---------------------------------------------------------------------------
# 1. ReviewIntentFeatures — boundary validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("intent_clarity", 0.0),
        ("intent_clarity", 1.0),
        ("locality_strength", 0.0),
        ("locality_strength", 1.0),
        ("mechanicalness", 0.0),
        ("mechanicalness", 1.0),
        ("scope_boundness", 0.0),
        ("scope_boundness", 1.0),
        ("semantic_change_risk", 0.0),
        ("semantic_change_risk", 1.0),
        ("validation_intensity", 0.0),
        ("validation_intensity", 1.0),
    ],
)
def test_intent_features_boundary_accepts_valid(field: str, value: float) -> None:
    kwargs = {
        "intent_clarity": 0.5,
        "locality_strength": 0.5,
        "mechanicalness": 0.5,
        "scope_boundness": 0.5,
        "semantic_change_risk": 0.5,
        "validation_intensity": 0.5,
    }
    kwargs[field] = value
    features = ReviewIntentFeatures(**kwargs)
    assert getattr(features, field) == value


@pytest.mark.parametrize(
    "field,value",
    [
        ("intent_clarity", -0.01),
        ("intent_clarity", 1.01),
        ("locality_strength", -0.01),
        ("locality_strength", 1.01),
        ("mechanicalness", -0.01),
        ("mechanicalness", 1.01),
        ("scope_boundness", -0.01),
        ("scope_boundness", 1.01),
        ("semantic_change_risk", -0.01),
        ("semantic_change_risk", 1.01),
        ("validation_intensity", -0.01),
        ("validation_intensity", 1.01),
    ],
)
def test_intent_features_boundary_rejects_invalid(field: str, value: float) -> None:
    kwargs = {
        "intent_clarity": 0.5,
        "locality_strength": 0.5,
        "mechanicalness": 0.5,
        "scope_boundness": 0.5,
        "semantic_change_risk": 0.5,
        "validation_intensity": 0.5,
    }
    kwargs[field] = value
    with pytest.raises(ValidationError):
        ReviewIntentFeatures(**kwargs)


# ---------------------------------------------------------------------------
# 2. FixActionFeatures — boundary validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_file_match", 0.0),
        ("target_file_match", 1.0),
        ("diff_hunk_overlap", 0.0),
        ("diff_hunk_overlap", 1.0),
        ("scope_ratio", 0.0),
        ("scope_ratio", 1.0),
        ("validation_scope_executed", 0.0),
        ("validation_scope_executed", 1.0),
        ("behavior_preservation_proxy", 0.0),
        ("behavior_preservation_proxy", 1.0),
        ("line_anchor_touched", 0.0),
        ("line_anchor_touched", 1.0),
    ],
)
def test_fix_action_float_boundary_accepts_valid(field: str, value: float) -> None:
    kwargs = {
        "changed": True,
        "validation_ok": True,
        "lines_changed": 1,
        "files_changed": 1,
        "target_file_match": 0.5,
        "line_anchor_touched": 0.5,
        "diff_hunk_overlap": 0.5,
        "scope_ratio": 0.5,
        "validation_scope_executed": 0.5,
        "behavior_preservation_proxy": 0.5,
        "execution_status": "succeeded",
    }
    kwargs[field] = value
    action = FixActionFeatures(**kwargs)
    assert getattr(action, field) == value


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_file_match", -0.01),
        ("target_file_match", 1.01),
        ("diff_hunk_overlap", -0.01),
        ("scope_ratio", -0.01),
        ("validation_scope_executed", 1.01),
    ],
)
def test_fix_action_float_boundary_rejects_invalid(field: str, value: float) -> None:
    kwargs = {
        "changed": True,
        "validation_ok": True,
        "lines_changed": 1,
        "files_changed": 1,
        "target_file_match": 0.5,
        "line_anchor_touched": 0.5,
        "diff_hunk_overlap": 0.5,
        "scope_ratio": 0.5,
        "validation_scope_executed": 0.5,
        "behavior_preservation_proxy": 0.5,
        "execution_status": "succeeded",
    }
    kwargs[field] = value
    with pytest.raises(ValidationError):
        FixActionFeatures(**kwargs)


def test_fix_action_negative_int_rejected() -> None:
    with pytest.raises(ValidationError):
        FixActionFeatures(
            changed=True,
            validation_ok=True,
            lines_changed=-1,
            files_changed=0,
            target_file_match=0.5,
            line_anchor_touched=0.5,
            diff_hunk_overlap=0.5,
            scope_ratio=0.5,
            validation_scope_executed=0.5,
            behavior_preservation_proxy=0.5,
            execution_status="succeeded",
        )


# ---------------------------------------------------------------------------
# 3. ReviewAuditConfig — defaults and constraints
# ---------------------------------------------------------------------------


def test_config_default_weights() -> None:
    cfg = ReviewAuditConfig()
    assert cfg.w_clarity == pytest.approx(0.30)
    assert cfg.w_locality == pytest.approx(0.25)
    assert cfg.w_mechanical == pytest.approx(0.20)
    assert cfg.w_scope == pytest.approx(0.25)


def test_config_default_versions() -> None:
    cfg = ReviewAuditConfig()
    assert cfg.extractor_version == "v1"
    assert cfg.feature_spec_version == "v1"


def test_config_custom_weights() -> None:
    cfg = ReviewAuditConfig(w_clarity=0.40, w_locality=0.30, w_mechanical=0.10, w_scope=0.20)
    assert cfg.w_clarity == pytest.approx(0.40)


def test_config_zero_weight_rejected() -> None:
    with pytest.raises(ValidationError):
        ReviewAuditConfig(w_clarity=0.0)


# ---------------------------------------------------------------------------
# 4. Frozen invariant
# ---------------------------------------------------------------------------


def test_intent_features_frozen() -> None:
    f = _intent()
    with pytest.raises((TypeError, Exception)):
        f.intent_clarity = 0.9  # type: ignore[misc]


def test_fix_action_frozen() -> None:
    a = _action()
    with pytest.raises((TypeError, Exception)):
        a.changed = False  # type: ignore[misc]


def test_config_frozen() -> None:
    cfg = ReviewAuditConfig()
    with pytest.raises((TypeError, Exception)):
        cfg.w_clarity = 0.9  # type: ignore[misc]


def test_snapshot_frozen() -> None:
    snap = ReviewAuditSnapshot(
        audit_id="test-01",
        por=0.7,
        verdict="aligned",
    )
    with pytest.raises((TypeError, Exception)):
        snap.por = 0.5  # type: ignore[misc]


def test_observation_frozen() -> None:
    obs = ReviewObservation(
        has_path_hint=True,
        has_line_anchor=True,
        has_diff_hunk=False,
        priority="P2",
        mechanical_keyword_hits=0,
        skip_keyword_hits=0,
        behavior_preservation_signal=False,
        scope_limit_signal=False,
        ambiguity_signal_count=0,
        target_file_present=True,
        review_kind="diff_comment",
    )
    with pytest.raises((TypeError, Exception)):
        obs.has_path_hint = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 5. ReviewAuditSnapshot — None-tolerant optional fields
# ---------------------------------------------------------------------------


def test_snapshot_delta_e_none() -> None:
    snap = ReviewAuditSnapshot(
        audit_id="snap-01",
        por=0.6,
        delta_e=None,
        mismatch_score=None,
        verdict="insufficient_data",
    )
    assert snap.delta_e is None
    assert snap.mismatch_score is None


def test_snapshot_delta_e_present() -> None:
    snap = ReviewAuditSnapshot(
        audit_id="snap-02",
        por=0.8,
        delta_e=0.15,
        mismatch_score=0.175,
        verdict="aligned",
    )
    assert snap.delta_e == pytest.approx(0.15)
    assert snap.mismatch_score == pytest.approx(0.175)


def test_snapshot_delta_e_boundary_rejected() -> None:
    with pytest.raises(ValidationError):
        ReviewAuditSnapshot(
            audit_id="snap-03",
            por=0.5,
            delta_e=1.01,
            verdict="marginal",
        )


# ---------------------------------------------------------------------------
# 6. ReviewAuditEngineResult structure
# ---------------------------------------------------------------------------


def test_engine_result_fields() -> None:
    snap = ReviewAuditSnapshot(audit_id="r-01", por=0.5, verdict="insufficient_data")
    result = ReviewAuditEngineResult(
        audit_snapshot=snap,
        intent_features=_intent(),
        action_features=None,
        config=ReviewAuditConfig(),
    )
    assert result.audit_snapshot.audit_id == "r-01"
    assert result.action_features is None


def test_engine_result_extra_field_rejected() -> None:
    snap = ReviewAuditSnapshot(audit_id="r-02", por=0.5, verdict="insufficient_data")
    with pytest.raises(ValidationError):
        ReviewAuditEngineResult(
            audit_snapshot=snap,
            intent_features=_intent(),
            action_features=None,
            config=ReviewAuditConfig(),
            extra_unknown_field="oops",  # type: ignore[call-arg]
        )
