"""Tests for engine.review_audit — pure deterministic engine functions."""
from __future__ import annotations

import pytest

from ugh_quantamental.engine.review_audit import (
    compute_delta_e,
    compute_mismatch_score,
    compute_por,
    compute_verdict,
    run_review_audit_engine,
)
from ugh_quantamental.engine.review_audit_models import (
    FixActionFeatures,
    ReviewAuditConfig,
    ReviewAuditEngineResult,
    ReviewIntentFeatures,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_CFG = ReviewAuditConfig()


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
    line_anchor_touched: float = 0.9,
    diff_hunk_overlap: float = 0.7,
    scope_ratio: float = 0.2,
    validation_scope_executed: float = 0.6,
    changed: bool = True,
    validation_ok: bool = True,
    execution_status: str = "succeeded",
) -> FixActionFeatures:
    return FixActionFeatures(
        changed=changed,
        validation_ok=validation_ok,
        lines_changed=5,
        files_changed=1,
        target_file_match=target_file_match,
        line_anchor_touched=line_anchor_touched,
        diff_hunk_overlap=diff_hunk_overlap,
        scope_ratio=scope_ratio,
        validation_scope_executed=validation_scope_executed,
        behavior_preservation_proxy=0.8,
        execution_status=execution_status,
    )


# ---------------------------------------------------------------------------
# compute_por
# ---------------------------------------------------------------------------


def test_compute_por_uniform_features() -> None:
    """All features = 0.5 with default weights -> PoR = 0.5."""
    intent = _intent(
        intent_clarity=0.5,
        locality_strength=0.5,
        mechanicalness=0.5,
        scope_boundness=0.5,
    )
    result = compute_por(intent, _DEFAULT_CFG)
    # w_total = 1.0; por = 0.3*0.5 + 0.25*0.5 + 0.20*0.5 + 0.25*0.5 = 0.5
    assert result == pytest.approx(0.5)


def test_compute_por_all_ones() -> None:
    intent = _intent(
        intent_clarity=1.0,
        locality_strength=1.0,
        mechanicalness=1.0,
        scope_boundness=1.0,
    )
    assert compute_por(intent, _DEFAULT_CFG) == pytest.approx(1.0)


def test_compute_por_all_zeros() -> None:
    intent = _intent(
        intent_clarity=0.0,
        locality_strength=0.0,
        mechanicalness=0.0,
        scope_boundness=0.0,
    )
    assert compute_por(intent, _DEFAULT_CFG) == pytest.approx(0.0)


def test_compute_por_expected_value() -> None:
    """Verify weighted sum formula with known inputs."""
    intent = _intent(
        intent_clarity=0.8,
        locality_strength=0.6,
        mechanicalness=0.4,
        scope_boundness=0.7,
    )
    # por = (0.30*0.8 + 0.25*0.6 + 0.20*0.4 + 0.25*0.7) / 1.0
    #     = (0.24 + 0.15 + 0.08 + 0.175) = 0.645
    assert compute_por(intent, _DEFAULT_CFG) == pytest.approx(0.645)


def test_compute_por_in_range() -> None:
    for v in [0.0, 0.1, 0.5, 0.9, 1.0]:
        result = compute_por(
            _intent(intent_clarity=v, locality_strength=v, mechanicalness=v, scope_boundness=v),
            _DEFAULT_CFG,
        )
        assert 0.0 <= result <= 1.0


def test_compute_por_custom_weights_normalised() -> None:
    """Non-unit-sum weights should produce the same result as a normalised version."""
    cfg_double = ReviewAuditConfig(w_clarity=0.60, w_locality=0.50, w_mechanical=0.40, w_scope=0.50)
    intent = _intent(
        intent_clarity=0.8,
        locality_strength=0.6,
        mechanicalness=0.4,
        scope_boundness=0.7,
    )
    # Scale by 2 -> same normalised result as default
    assert compute_por(intent, cfg_double) == pytest.approx(compute_por(intent, _DEFAULT_CFG))


# ---------------------------------------------------------------------------
# compute_delta_e
# ---------------------------------------------------------------------------


def test_compute_delta_e_none_when_action_is_none() -> None:
    result = compute_delta_e(_intent(), None, _DEFAULT_CFG)
    assert result is None


def test_compute_delta_e_aligned_case() -> None:
    """Action closely mirrors intent -> low ΔE."""
    intent = _intent(
        locality_strength=0.8,
        mechanicalness=0.8,
        scope_boundness=0.8,
        validation_intensity=0.8,
    )
    # action mirrors intent components:
    # target_file_match ≈ locality_strength, diff_hunk_overlap ≈ mechanicalness
    # scope_ratio=0.2 -> inverted=0.8 ≈ scope_boundness, validation≈validation_intensity
    act = _action(
        target_file_match=0.8,
        diff_hunk_overlap=0.8,
        scope_ratio=0.2,
        validation_scope_executed=0.8,
    )
    result = compute_delta_e(intent, act, _DEFAULT_CFG)
    assert result is not None
    assert result < 0.1


def test_compute_delta_e_divergent_case() -> None:
    """Action diverges from intent -> high ΔE."""
    intent = _intent(
        locality_strength=1.0,
        mechanicalness=1.0,
        scope_boundness=1.0,
        validation_intensity=1.0,
    )
    act = _action(
        target_file_match=0.0,
        diff_hunk_overlap=0.0,
        scope_ratio=1.0,   # inverted = 0.0
        validation_scope_executed=0.0,
    )
    result = compute_delta_e(intent, act, _DEFAULT_CFG)
    assert result is not None
    assert result > 0.7


def test_compute_delta_e_scope_inversion() -> None:
    """scope_ratio=0.0 (tight) is treated as 1.0 after inversion (aligned with high scope_boundness)."""
    intent = _intent(scope_boundness=1.0, locality_strength=0.5, mechanicalness=0.5, validation_intensity=0.5)
    act_tight = _action(scope_ratio=0.0, target_file_match=0.5, diff_hunk_overlap=0.5, validation_scope_executed=0.5)
    act_broad = _action(scope_ratio=1.0, target_file_match=0.5, diff_hunk_overlap=0.5, validation_scope_executed=0.5)
    de_tight = compute_delta_e(intent, act_tight, _DEFAULT_CFG)
    de_broad = compute_delta_e(intent, act_broad, _DEFAULT_CFG)
    assert de_tight is not None and de_broad is not None
    # tight scope_ratio -> inverted=1.0 ~ scope_boundness=1.0 -> small contribution to ΔE
    assert de_tight < de_broad


def test_compute_delta_e_in_range() -> None:
    act = _action()
    result = compute_delta_e(_intent(), act, _DEFAULT_CFG)
    assert result is not None
    assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# compute_mismatch_score
# ---------------------------------------------------------------------------


def test_compute_mismatch_score_none_when_delta_e_none() -> None:
    assert compute_mismatch_score(0.7, None) is None


def test_compute_mismatch_score_expected_value() -> None:
    # 0.5 * (1.0 - 0.8) + 0.5 * 0.1 = 0.5 * 0.2 + 0.05 = 0.10 + 0.05 = 0.15
    result = compute_mismatch_score(0.8, 0.1)
    assert result == pytest.approx(0.15)


def test_compute_mismatch_score_clamped() -> None:
    # por=0.0, delta_e=1.0 -> 0.5 * 1.0 + 0.5 * 1.0 = 1.0 (no clamping needed)
    assert compute_mismatch_score(0.0, 1.0) == pytest.approx(1.0)
    # por=1.0, delta_e=0.0 -> 0.5 * 0.0 + 0.5 * 0.0 = 0.0
    assert compute_mismatch_score(1.0, 0.0) == pytest.approx(0.0)


def test_compute_mismatch_score_in_range() -> None:
    for por, de in [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0), (0.3, 0.7), (0.9, 0.1)]:
        result = compute_mismatch_score(por, de)
        assert result is not None
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# compute_verdict
# ---------------------------------------------------------------------------


def test_verdict_insufficient_data_when_action_none() -> None:
    assert compute_verdict(0.9, None, None) == "insufficient_data"


def test_verdict_insufficient_data_even_with_high_por() -> None:
    # action=None always wins first rule
    assert compute_verdict(1.0, None, None) == "insufficient_data"


def test_verdict_aligned() -> None:
    act = _action()
    assert compute_verdict(0.7, 0.2, act) == "aligned"
    assert compute_verdict(0.9, 0.0, act) == "aligned"
    assert compute_verdict(0.75, 0.15, act) == "aligned"


def test_verdict_misaligned_low_por() -> None:
    act = _action()
    assert compute_verdict(0.3, 0.3, act) == "misaligned"
    assert compute_verdict(0.39, 0.5, act) == "misaligned"


def test_verdict_misaligned_high_delta_e() -> None:
    act = _action()
    assert compute_verdict(0.5, 0.7, act) == "misaligned"
    assert compute_verdict(0.6, 0.61, act) == "misaligned"


def test_verdict_marginal() -> None:
    act = _action()
    # por >= 0.4, por < 0.7, delta_e <= 0.6
    assert compute_verdict(0.5, 0.3, act) == "marginal"
    assert compute_verdict(0.6, 0.5, act) == "marginal"
    # por >= 0.7 but delta_e > 0.2 and delta_e <= 0.6
    assert compute_verdict(0.8, 0.4, act) == "marginal"


def test_verdict_boundary_aligned_edge() -> None:
    """Exact boundary: por=0.7 and delta_e=0.2 -> aligned."""
    act = _action()
    assert compute_verdict(0.7, 0.2, act) == "aligned"


def test_verdict_boundary_just_outside_aligned() -> None:
    """Just outside aligned: delta_e=0.201 -> marginal (assuming por >= 0.7)."""
    act = _action()
    # por=0.7, delta_e=0.21 -> not aligned (0.21 > 0.2), not misaligned (por>=0.4, de<=0.6)
    assert compute_verdict(0.7, 0.21, act) == "marginal"


# ---------------------------------------------------------------------------
# run_review_audit_engine
# ---------------------------------------------------------------------------


def test_run_engine_action_none_case() -> None:
    """With no action: delta_e=None, mismatch_score=None, verdict=insufficient_data."""
    result = run_review_audit_engine(
        audit_id="test-none-01",
        intent=_intent(),
        action=None,
        config=_DEFAULT_CFG,
    )
    assert isinstance(result, ReviewAuditEngineResult)
    snap = result.audit_snapshot
    assert snap.audit_id == "test-none-01"
    assert snap.delta_e is None
    assert snap.mismatch_score is None
    assert snap.verdict == "insufficient_data"
    assert result.action_features is None


def test_run_engine_aligned_case() -> None:
    """Clearly aligned case: snapshot should report aligned."""
    intent = _intent(
        intent_clarity=0.9,
        locality_strength=0.9,
        mechanicalness=0.9,
        scope_boundness=0.9,
    )
    act = _action(
        target_file_match=0.9,
        diff_hunk_overlap=0.9,
        scope_ratio=0.1,
        validation_scope_executed=0.9,
    )
    result = run_review_audit_engine(
        audit_id="test-aligned-01",
        intent=intent,
        action=act,
        config=_DEFAULT_CFG,
    )
    snap = result.audit_snapshot
    assert snap.por >= 0.7
    assert snap.delta_e is not None
    assert snap.delta_e <= 0.2
    assert snap.verdict == "aligned"
    assert snap.mismatch_score is not None


def test_run_engine_misaligned_case() -> None:
    """Clearly misaligned: low PoR and high ΔE."""
    intent = _intent(
        intent_clarity=0.1,
        locality_strength=0.1,
        mechanicalness=0.1,
        scope_boundness=0.1,
        validation_intensity=1.0,
    )
    act = _action(
        target_file_match=0.0,
        diff_hunk_overlap=0.0,
        scope_ratio=1.0,
        validation_scope_executed=0.0,
    )
    result = run_review_audit_engine(
        audit_id="test-mis-01",
        intent=intent,
        action=act,
        config=_DEFAULT_CFG,
    )
    snap = result.audit_snapshot
    assert snap.por < 0.4
    assert snap.verdict == "misaligned"


def test_run_engine_result_fields_populated() -> None:
    intent = _intent()
    act = _action()
    result = run_review_audit_engine(
        audit_id="test-full-01",
        intent=intent,
        action=act,
        config=_DEFAULT_CFG,
    )
    assert result.intent_features == intent
    assert result.action_features == act
    assert result.config == _DEFAULT_CFG
    assert isinstance(result.audit_snapshot.por, float)
    assert 0.0 <= result.audit_snapshot.por <= 1.0


def test_run_engine_deterministic() -> None:
    """Same inputs produce identical results on repeated calls."""
    intent = _intent(intent_clarity=0.7, locality_strength=0.6)
    act = _action(target_file_match=0.5)
    r1 = run_review_audit_engine("det-01", intent, act, _DEFAULT_CFG)
    r2 = run_review_audit_engine("det-01", intent, act, _DEFAULT_CFG)
    assert r1 == r2


def test_run_engine_snapshot_bounds() -> None:
    """All snapshot float fields are within [0, 1]."""
    for v in [0.0, 0.5, 1.0]:
        intent = _intent(
            intent_clarity=v,
            locality_strength=v,
            mechanicalness=v,
            scope_boundness=v,
            validation_intensity=v,
        )
        act = _action(
            target_file_match=v,
            diff_hunk_overlap=v,
            scope_ratio=v,
            validation_scope_executed=v,
        )
        result = run_review_audit_engine("bounds-test", intent, act, _DEFAULT_CFG)
        snap = result.audit_snapshot
        assert 0.0 <= snap.por <= 1.0
        assert snap.delta_e is not None and 0.0 <= snap.delta_e <= 1.0
        assert snap.mismatch_score is not None and 0.0 <= snap.mismatch_score <= 1.0
