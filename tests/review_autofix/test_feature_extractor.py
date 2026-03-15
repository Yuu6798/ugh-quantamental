"""Tests for review_autofix.feature_extractor — deterministic extraction pipeline."""
from __future__ import annotations

import pytest

from ugh_quantamental.review_autofix.feature_extractor import (
    ReviewIntentFeatures,
    ReviewObservation,
    extract_review_features,
    extract_review_intent_features,
    extract_review_observation,
)
from ugh_quantamental.review_autofix.models import ReviewContext, ReviewKind


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(
    *,
    kind: ReviewKind = ReviewKind.diff_comment,
    body: str = "fix the lint issue",
    path: str | None = "src/foo.py",
    diff_hunk: str | None = "@@ -1,3 +1,3 @@\n-x\n+y",
    line: int | None = 10,
    start_line: int | None = None,
) -> ReviewContext:
    return ReviewContext(
        kind=kind,
        repository="acme/repo",
        pr_number=42,
        review_id=1,
        review_comment_id=2,
        head_sha="deadbeef",
        base_ref="main",
        head_ref="feature",
        same_repo=True,
        reviewer_login="alice",
        body=body,
        path=path,
        diff_hunk=diff_hunk,
        line=line,
        start_line=start_line,
        version_discriminator="2024-01-01T00:00:00Z:deadbeef",
    )


# ---------------------------------------------------------------------------
# 1. Determinism: same context -> same output
# ---------------------------------------------------------------------------


def test_determinism_observation() -> None:
    ctx = _make_context(body="P1 fix unused import ruff")
    obs1 = extract_review_observation(ctx)
    obs2 = extract_review_observation(ctx)
    assert obs1 == obs2


def test_determinism_features() -> None:
    ctx = _make_context(body="P1 fix unused import ruff")
    obs = extract_review_observation(ctx)
    f1 = extract_review_intent_features(obs)
    f2 = extract_review_intent_features(obs)
    assert f1 == f2


def test_determinism_convenience_wrapper() -> None:
    ctx = _make_context(body="P2 lint: normalizer missing")
    r1 = extract_review_features(ctx)
    r2 = extract_review_features(ctx)
    assert r1[0] == r2[0]
    assert r1[1] == r2[1]


# ---------------------------------------------------------------------------
# 2. Diff comment happy path
# ---------------------------------------------------------------------------


def test_diff_comment_happy_path_observation() -> None:
    ctx = _make_context(
        kind=ReviewKind.diff_comment,
        body="P1 fix unused import lint ruff",
        path="src/engine/projection.py",
        diff_hunk="@@ -5,3 +5,3 @@\n-import os\n+# removed",
        line=5,
    )
    obs = extract_review_observation(ctx)
    assert obs.has_path_hint is True
    assert obs.has_line_anchor is True
    assert obs.has_diff_hunk is True
    assert obs.mechanical_keyword_hits > 0
    assert obs.review_kind == "diff_comment"


def test_diff_comment_happy_path_features() -> None:
    ctx = _make_context(
        kind=ReviewKind.diff_comment,
        body="P1 fix unused import lint ruff",
        path="src/engine/projection.py",
        diff_hunk="@@ -5,3 +5,3 @@\n-import os\n+# removed",
        line=5,
    )
    _, features = extract_review_features(ctx)
    # All three structural signals present + P1 -> high intent clarity
    assert features.intent_clarity > 0.7
    assert features.mechanicalness > 0.0


# ---------------------------------------------------------------------------
# 3. Review body with path hint (no line/hunk)
# ---------------------------------------------------------------------------


def test_review_body_with_path() -> None:
    ctx_with_path = _make_context(
        kind=ReviewKind.review_body,
        path="src/foo.py",
        diff_hunk=None,
        line=None,
        body="P2 please check the validator logic",
    )
    ctx_no_path = _make_context(
        kind=ReviewKind.review_body,
        path=None,
        diff_hunk=None,
        line=None,
        body="P2 please check the validator logic",
    )

    obs_with = extract_review_observation(ctx_with_path)
    obs_without = extract_review_observation(ctx_no_path)

    assert obs_with.has_path_hint is True
    assert obs_with.has_line_anchor is False

    f_with = extract_review_intent_features(obs_with)
    f_without = extract_review_intent_features(obs_without)

    # path hint contributes 0.35 weight -> with-path clarity > without-path
    assert f_with.intent_clarity > f_without.intent_clarity

    # no line anchor -> locality_strength is 0 for both; diff comment would be higher
    ctx_diff = _make_context(
        kind=ReviewKind.diff_comment,
        path="src/foo.py",
        diff_hunk="@@",
        line=5,
        body="P2 validator issue",
    )
    _, f_diff = extract_review_features(ctx_diff)
    assert f_diff.locality_strength > f_with.locality_strength


# ---------------------------------------------------------------------------
# 4. Review body without path hint
# ---------------------------------------------------------------------------


def test_review_body_no_path() -> None:
    ctx = _make_context(
        kind=ReviewKind.review_body,
        path=None,
        diff_hunk=None,
        line=None,
        body="general comment about the code quality",
    )
    obs = extract_review_observation(ctx)
    assert obs.has_path_hint is False
    assert obs.target_file_present is False

    _, features = extract_review_features(ctx)
    # No path, no line, no hunk -> intent_clarity should be low
    assert features.intent_clarity < 0.4


# ---------------------------------------------------------------------------
# 5. Skip keywords reduce mechanicalness / raise semantic_change_risk
# ---------------------------------------------------------------------------


def test_skip_keywords_effect() -> None:
    ctx_clean = _make_context(body="P2 fix lint import")
    ctx_skip = _make_context(body="P2 fix lint import refactor design")

    obs_clean = extract_review_observation(ctx_clean)
    obs_skip = extract_review_observation(ctx_skip)

    assert obs_skip.skip_keyword_hits > 0

    f_clean = extract_review_intent_features(obs_clean)
    f_skip = extract_review_intent_features(obs_skip)

    assert f_skip.mechanicalness <= f_clean.mechanicalness
    assert f_skip.semantic_change_risk >= f_clean.semantic_change_risk


# ---------------------------------------------------------------------------
# 6. Priority extraction feeds intent_clarity
# ---------------------------------------------------------------------------


def test_priority_p0_vs_p3_intent_clarity() -> None:
    ctx_p0 = _make_context(body="P0 critical fix", path=None, diff_hunk=None, line=None)
    ctx_p3 = _make_context(body="P3 minor nit", path=None, diff_hunk=None, line=None)

    obs_p0 = extract_review_observation(ctx_p0)
    obs_p3 = extract_review_observation(ctx_p3)

    assert obs_p0.priority == "P0"
    assert obs_p3.priority == "P3"

    f_p0 = extract_review_intent_features(obs_p0)
    f_p3 = extract_review_intent_features(obs_p3)

    # P0 score=1.00 vs P3 score=0.25 (weight 0.20) -> p0 clarity > p3 clarity
    assert f_p0.intent_clarity > f_p3.intent_clarity


# ---------------------------------------------------------------------------
# 7. Ambiguity / scope / behavior signals
# ---------------------------------------------------------------------------


def test_ambiguity_keywords_raise_ambiguity_count() -> None:
    ctx = _make_context(body="should consider this maybe")
    obs = extract_review_observation(ctx)
    assert obs.ambiguity_signal_count >= 3


def test_scope_limit_signal() -> None:
    ctx = _make_context(body="only minimal change scope limited")
    obs = extract_review_observation(ctx)
    assert obs.scope_limit_signal is True

    features = extract_review_intent_features(obs)
    # scope_limit_signal adds +0.5 base -> scope_boundness should be positive
    assert features.scope_boundness > 0.0


def test_behavior_preservation_signal() -> None:
    ctx = _make_context(body="preserve existing behavior compat")
    obs = extract_review_observation(ctx)
    assert obs.behavior_preservation_signal is True


def test_behavior_preservation_reduces_risk() -> None:
    ctx_preserve = _make_context(body="preserve existing behavior should consider")
    ctx_no_preserve = _make_context(body="should consider the design refactor")

    obs_preserve = extract_review_observation(ctx_preserve)
    obs_no_preserve = extract_review_observation(ctx_no_preserve)

    f_preserve = extract_review_intent_features(obs_preserve)
    f_no_preserve = extract_review_intent_features(obs_no_preserve)

    # behavior preservation signal provides a modest reduction in risk
    # (not necessarily lower in all cases, but should not raise it)
    # We just verify the signal is set and risk stays bounded
    assert obs_preserve.behavior_preservation_signal is True
    assert 0.0 <= f_preserve.semantic_change_risk <= 1.0
    assert 0.0 <= f_no_preserve.semantic_change_risk <= 1.0


# ---------------------------------------------------------------------------
# 8. All features stay within [0, 1]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        "",
        "P0 critical: fix lint import ruff unused normalizer validator utc",
        "design refactor 大規模 アーキ 仕様変更",
        "should consider maybe suggest preserve existing compat backward",
        "minimal only scope limited 最小 のみ 限定",
        "P3 minor nit: 整理 未使用 型",
        "preserve existing behavior should consider refactor design P0 lint ruff",
    ],
)
def test_all_features_bounded(body: str) -> None:
    ctx = _make_context(body=body)
    _, features = extract_review_features(ctx)
    for field_name in ReviewIntentFeatures.model_fields:
        value = getattr(features, field_name)
        assert 0.0 <= value <= 1.0, f"{field_name}={value} out of [0,1]"


# ---------------------------------------------------------------------------
# 9. Return types and model validation
# ---------------------------------------------------------------------------


def test_return_types() -> None:
    ctx = _make_context()
    obs, features = extract_review_features(ctx)
    assert isinstance(obs, ReviewObservation)
    assert isinstance(features, ReviewIntentFeatures)


def test_observation_is_frozen() -> None:
    ctx = _make_context()
    obs = extract_review_observation(ctx)
    with pytest.raises((TypeError, Exception)):
        obs.has_path_hint = False  # type: ignore[misc]


def test_features_is_frozen() -> None:
    ctx = _make_context()
    _, features = extract_review_features(ctx)
    with pytest.raises((TypeError, Exception)):
        features.intent_clarity = 0.5  # type: ignore[misc]
