"""Tests for fx_protocol.ids — deterministic ID generation helpers."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.ids import (
    make_evaluation_id,
    make_forecast_batch_id,
    make_forecast_id,
    make_outcome_id,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, StrategyKind

JST = ZoneInfo("Asia/Tokyo")

_PAIR = CurrencyPair.USDJPY
_AS_OF = datetime(2026, 3, 10, 8, 0, 0, tzinfo=JST)
_WINDOW_START = datetime(2026, 3, 10, 8, 0, 0, tzinfo=JST)
_WINDOW_END = datetime(2026, 3, 11, 8, 0, 0, tzinfo=JST)
_PROTO_VER = "v1"
_SCHEMA_VER = "v1"


# ---------------------------------------------------------------------------
# make_forecast_batch_id
# ---------------------------------------------------------------------------


def test_forecast_batch_id_is_stable() -> None:
    id1 = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    id2 = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    assert id1 == id2


def test_forecast_batch_id_starts_with_prefix() -> None:
    fid = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    assert fid.startswith("fb_")


def test_forecast_batch_id_contains_pair() -> None:
    fid = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    assert "USDJPY" in fid


def test_forecast_batch_id_contains_as_of_date() -> None:
    fid = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    assert "20260310" in fid


def test_forecast_batch_id_changes_with_different_date() -> None:
    other_as_of = datetime(2026, 3, 11, 8, 0, 0, tzinfo=JST)
    id1 = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    id2 = make_forecast_batch_id(_PAIR, other_as_of, _PROTO_VER)
    assert id1 != id2


def test_forecast_batch_id_changes_with_different_protocol_version() -> None:
    id1 = make_forecast_batch_id(_PAIR, _AS_OF, "v1")
    id2 = make_forecast_batch_id(_PAIR, _AS_OF, "v2")
    assert id1 != id2


# ---------------------------------------------------------------------------
# make_forecast_id
# ---------------------------------------------------------------------------


def test_forecast_id_is_stable() -> None:
    id1 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    id2 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    assert id1 == id2


def test_forecast_id_starts_with_prefix() -> None:
    fid = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    assert fid.startswith("fc_")


def test_forecast_id_contains_pair() -> None:
    fid = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    assert "USDJPY" in fid


def test_forecast_id_contains_strategy() -> None:
    fid = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    assert "ugh" in fid


def test_forecast_id_differs_by_strategy_kind() -> None:
    id_ugh = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    id_rw = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.baseline_random_walk)
    assert id_ugh != id_rw


def test_forecast_id_differs_by_date() -> None:
    other = datetime(2026, 3, 12, 8, 0, 0, tzinfo=JST)
    id1 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    id2 = make_forecast_id(_PAIR, other, _PROTO_VER, StrategyKind.ugh)
    assert id1 != id2


@pytest.mark.parametrize(
    "strategy_kind",
    [
        StrategyKind.ugh,
        StrategyKind.baseline_random_walk,
        StrategyKind.baseline_prev_day_direction,
        StrategyKind.baseline_simple_technical,
    ],
)
def test_forecast_id_stable_for_all_strategy_kinds(strategy_kind: StrategyKind) -> None:
    id1 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, strategy_kind)
    id2 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, strategy_kind)
    assert id1 == id2


def test_forecast_id_all_four_strategies_are_unique() -> None:
    ids = [
        make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, sk)
        for sk in StrategyKind
    ]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# make_outcome_id
# ---------------------------------------------------------------------------


def test_outcome_id_is_stable() -> None:
    id1 = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    id2 = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    assert id1 == id2


def test_outcome_id_starts_with_prefix() -> None:
    oid = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    assert oid.startswith("oc_")


def test_outcome_id_contains_pair() -> None:
    oid = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    assert "USDJPY" in oid


def test_outcome_id_differs_by_window_start() -> None:
    other_start = datetime(2026, 3, 11, 8, 0, 0, tzinfo=JST)
    other_end = datetime(2026, 3, 12, 8, 0, 0, tzinfo=JST)
    id1 = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    id2 = make_outcome_id(_PAIR, other_start, other_end, _SCHEMA_VER)
    assert id1 != id2


def test_outcome_id_differs_by_schema_version() -> None:
    id1 = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, "v1")
    id2 = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, "v2")
    assert id1 != id2


# ---------------------------------------------------------------------------
# make_evaluation_id
# ---------------------------------------------------------------------------


def test_evaluation_id_is_stable() -> None:
    fc_id = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    ev1 = make_evaluation_id(fc_id, _SCHEMA_VER)
    ev2 = make_evaluation_id(fc_id, _SCHEMA_VER)
    assert ev1 == ev2


def test_evaluation_id_starts_with_prefix() -> None:
    fc_id = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    ev = make_evaluation_id(fc_id, _SCHEMA_VER)
    assert ev.startswith("ev_")


def test_evaluation_id_contains_forecast_id() -> None:
    fc_id = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    ev = make_evaluation_id(fc_id, _SCHEMA_VER)
    assert fc_id in ev


def test_evaluation_id_differs_by_schema_version() -> None:
    fc_id = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    ev1 = make_evaluation_id(fc_id, "v1")
    ev2 = make_evaluation_id(fc_id, "v2")
    assert ev1 != ev2


def test_evaluation_id_differs_by_forecast_id() -> None:
    fc1 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    fc2 = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.baseline_random_walk)
    ev1 = make_evaluation_id(fc1, _SCHEMA_VER)
    ev2 = make_evaluation_id(fc2, _SCHEMA_VER)
    assert ev1 != ev2


# ---------------------------------------------------------------------------
# No duplicate-format ambiguity
# ---------------------------------------------------------------------------


def test_forecast_batch_and_forecast_ids_are_distinct() -> None:
    """forecast_batch_id and forecast_id must never collide in format."""
    fb = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    fc = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    assert fb != fc
    assert fb.startswith("fb_")
    assert fc.startswith("fc_")


def test_outcome_and_evaluation_ids_are_distinct() -> None:
    oc = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    fc_id = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    ev = make_evaluation_id(fc_id, _SCHEMA_VER)
    assert oc != ev
    assert oc.startswith("oc_")
    assert ev.startswith("ev_")


def test_all_four_id_types_have_distinct_prefixes() -> None:
    fb = make_forecast_batch_id(_PAIR, _AS_OF, _PROTO_VER)
    fc = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    oc = make_outcome_id(_PAIR, _WINDOW_START, _WINDOW_END, _SCHEMA_VER)
    fc_id = make_forecast_id(_PAIR, _AS_OF, _PROTO_VER, StrategyKind.ugh)
    ev = make_evaluation_id(fc_id, _SCHEMA_VER)

    prefixes = {fb[:3], fc[:3], oc[:3], ev[:3]}
    assert len(prefixes) == 4
