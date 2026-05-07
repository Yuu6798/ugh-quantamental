"""Unit tests for v2 ``StrategyKind`` helpers (spec §8.1).

Covers ``is_ugh_kind`` (legacy + v2 variants, enum + string forms) and the
``EXPECTED_DAILY_BATCH_SIZE`` / ``_ACTIVE_STRATEGY_KINDS`` source-of-truth
introduced for the v2 cut-over.
"""

from __future__ import annotations

import pytest

from ugh_quantamental.fx_protocol.models import (
    EXPECTED_DAILY_BATCH_SIZE,
    StrategyKind,
    _ACTIVE_STRATEGY_KINDS,
    is_ugh_kind,
)


def test_is_ugh_kind_legacy_enum() -> None:
    assert is_ugh_kind(StrategyKind.ugh) is True


def test_is_ugh_kind_legacy_string() -> None:
    assert is_ugh_kind("ugh") is True


@pytest.mark.parametrize(
    "kind",
    [
        StrategyKind.ugh_v2_alpha,
        StrategyKind.ugh_v2_beta,
        StrategyKind.ugh_v2_gamma,
        StrategyKind.ugh_v2_delta,
    ],
)
def test_is_ugh_kind_v2_variants_enum(kind: StrategyKind) -> None:
    assert is_ugh_kind(kind) is True


@pytest.mark.parametrize(
    "kind",
    ["ugh_v2_alpha", "ugh_v2_beta", "ugh_v2_gamma", "ugh_v2_delta"],
)
def test_is_ugh_kind_v2_variants_string(kind: str) -> None:
    assert is_ugh_kind(kind) is True


@pytest.mark.parametrize(
    "kind",
    [
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    ],
)
def test_is_ugh_kind_baselines_false(kind: StrategyKind) -> None:
    assert is_ugh_kind(kind) is False


def test_is_ugh_kind_baseline_strings_false() -> None:
    assert is_ugh_kind("baseline_random_walk") is False
    assert is_ugh_kind("baseline_prev_day_direction") is False
    assert is_ugh_kind("baseline_simple_technical") is False


def test_is_ugh_kind_unknown_string_false() -> None:
    """Unknown / forward-compatible kind strings return False rather than raising.

    This keeps analytics paths that read raw CSV rows (e.g. legacy fixtures
    or future variants) tolerant.
    """
    assert is_ugh_kind("not_a_kind") is False
    assert is_ugh_kind("") is False


def test_is_ugh_kind_non_string_returns_false() -> None:
    """Defensive: non-StrategyKind / non-string inputs return False."""
    assert is_ugh_kind(None) is False  # type: ignore[arg-type]
    assert is_ugh_kind(0) is False  # type: ignore[arg-type]


def test_expected_daily_batch_size_matches_active_kinds() -> None:
    """Spec §7 step 4c: single source of truth for daily batch size."""
    assert EXPECTED_DAILY_BATCH_SIZE == len(_ACTIVE_STRATEGY_KINDS)
    assert EXPECTED_DAILY_BATCH_SIZE == 7  # 4 v2 UGH variants + 3 baselines


def test_active_strategy_kinds_excludes_legacy_ugh() -> None:
    """Legacy ``ugh`` is retired from new daily emission (spec §5.2)."""
    assert StrategyKind.ugh not in _ACTIVE_STRATEGY_KINDS


def test_active_strategy_kinds_includes_all_v2_variants() -> None:
    for variant in (
        StrategyKind.ugh_v2_alpha,
        StrategyKind.ugh_v2_beta,
        StrategyKind.ugh_v2_gamma,
        StrategyKind.ugh_v2_delta,
    ):
        assert variant in _ACTIVE_STRATEGY_KINDS
