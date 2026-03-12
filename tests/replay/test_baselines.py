"""Integration tests for replay/baselines.py — create / get / compare flows."""

from __future__ import annotations

import importlib.util

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


# ---------------------------------------------------------------------------
# Import isolation — make_baseline_id must not require SQLAlchemy
# ---------------------------------------------------------------------------


def test_make_baseline_id_importable_without_sqlalchemy(monkeypatch) -> None:
    """baselines.make_baseline_id must be importable even when sqlalchemy is absent.

    Simulates a SQLAlchemy-free environment by hiding the module from sys.modules
    and the finder, then reimporting baselines to verify no transitive SQLAlchemy
    import occurs at module load time.
    """
    import sys
    import types

    # Remove cached baselines module so it reimports fresh
    mods_to_remove = [k for k in sys.modules if "baselines" in k or "suites" in k]
    saved = {k: sys.modules.pop(k) for k in mods_to_remove}

    # Inject a dummy sqlalchemy that raises on real attribute access
    fake_sa = types.ModuleType("sqlalchemy")
    fake_orm = types.ModuleType("sqlalchemy.orm")
    monkeypatch.setitem(sys.modules, "sqlalchemy", fake_sa)
    monkeypatch.setitem(sys.modules, "sqlalchemy.orm", fake_orm)

    try:
        # This must not raise even though sqlalchemy is "broken"
        from ugh_quantamental.replay.baselines import make_baseline_id  # noqa: PLC0415

        bid = make_baseline_id()
        assert bid.startswith("base_")
    finally:
        # Restore original modules
        for k, v in saved.items():
            sys.modules[k] = v


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_suite_request_with_run(session, question_features, signal_features, alignment_inputs):
    """Persist one projection run and return a RegressionSuiteRequest over it."""
    from ugh_quantamental.engine.projection import run_projection_engine
    from ugh_quantamental.engine.projection_models import ProjectionConfig
    from ugh_quantamental.persistence.repositories import ProjectionRunRepository
    from ugh_quantamental.replay.suite_models import ProjectionSuiteCase, RegressionSuiteRequest
    from ugh_quantamental.workflows.models import make_run_id

    run_id = make_run_id("proj_bl_")
    cfg = ProjectionConfig()
    result = run_projection_engine("q-bl-1", 30, question_features, signal_features,
                                   alignment_inputs, cfg)
    ProjectionRunRepository.save_run(
        session,
        run_id=run_id,
        projection_id="q-bl-1",
        question_features=question_features,
        signal_features=signal_features,
        alignment_inputs=alignment_inputs,
        config=cfg,
        result=result,
    )
    session.flush()
    return (
        run_id,
        RegressionSuiteRequest(
            projection_cases=(ProjectionSuiteCase(name="smoke", run_ids=(run_id,)),)
        ),
    )


# ---------------------------------------------------------------------------
# make_baseline_id
# ---------------------------------------------------------------------------


def test_make_baseline_id_default_prefix() -> None:
    from ugh_quantamental.replay.baselines import make_baseline_id

    bid = make_baseline_id()
    assert bid.startswith("base_")
    assert len(bid) == len("base_") + 12


def test_make_baseline_id_custom_prefix() -> None:
    from ugh_quantamental.replay.baselines import make_baseline_id

    bid = make_baseline_id(prefix="golden_")
    assert bid.startswith("golden_")


def test_make_baseline_id_unique() -> None:
    from ugh_quantamental.replay.baselines import make_baseline_id

    ids = {make_baseline_id() for _ in range(20)}
    assert len(ids) == 20


# ---------------------------------------------------------------------------
# create_regression_baseline
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_create_baseline_returns_bundle(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from ugh_quantamental.replay.baseline_models import CreateRegressionBaselineRequest
    from ugh_quantamental.replay.baselines import create_regression_baseline

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    req = CreateRegressionBaselineRequest(
        baseline_name="test-v1",
        suite_request=suite_req,
        description="first golden snapshot",
    )
    bundle = create_regression_baseline(db_session, req)

    assert bundle.baseline.baseline_name == "test-v1"
    assert bundle.baseline.description == "first golden snapshot"
    assert bundle.persisted_run_id == bundle.baseline.baseline_id
    assert bundle.baseline.suite_result_json["aggregate"]["total_case_count"] == 1
    assert len(bundle.baseline.suite_result_json["projection_cases"]) == 1


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_create_baseline_explicit_id(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from ugh_quantamental.replay.baseline_models import CreateRegressionBaselineRequest
    from ugh_quantamental.replay.baselines import create_regression_baseline

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    req = CreateRegressionBaselineRequest(
        baseline_name="explicit-id-test",
        suite_request=suite_req,
        baseline_id="base_manual001",
    )
    bundle = create_regression_baseline(db_session, req)
    assert bundle.baseline.baseline_id == "base_manual001"
    assert bundle.persisted_run_id == "base_manual001"


# ---------------------------------------------------------------------------
# get_regression_baseline
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_baseline_by_id(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from ugh_quantamental.replay.baseline_models import CreateRegressionBaselineRequest
    from ugh_quantamental.replay.baselines import (
        create_regression_baseline,
        get_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    created = create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(baseline_name="get-by-id", suite_request=suite_req),
    )
    loaded = get_regression_baseline(db_session, baseline_id=created.baseline.baseline_id)

    assert loaded is not None
    assert loaded.baseline.baseline_id == created.baseline.baseline_id
    assert loaded.baseline.baseline_name == "get-by-id"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_baseline_by_name(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from ugh_quantamental.replay.baseline_models import CreateRegressionBaselineRequest
    from ugh_quantamental.replay.baselines import (
        create_regression_baseline,
        get_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(baseline_name="get-by-name", suite_request=suite_req),
    )
    loaded = get_regression_baseline(db_session, baseline_name="get-by-name")

    assert loaded is not None
    assert loaded.baseline.baseline_name == "get-by-name"


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_baseline_missing_returns_none(db_session) -> None:
    from ugh_quantamental.replay.baselines import get_regression_baseline

    result = get_regression_baseline(db_session, baseline_id="base_nonexistent")
    assert result is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_baseline_by_name_missing_returns_none(db_session) -> None:
    from ugh_quantamental.replay.baselines import get_regression_baseline

    result = get_regression_baseline(db_session, baseline_name="does-not-exist")
    assert result is None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_get_baseline_both_args_raises(db_session) -> None:
    from ugh_quantamental.replay.baselines import get_regression_baseline

    with pytest.raises(ValueError, match="exactly one"):
        get_regression_baseline(db_session, baseline_id="x", baseline_name="y")


# ---------------------------------------------------------------------------
# compare_regression_baseline — exact match
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_compare_baseline_exact_match(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from ugh_quantamental.replay.baseline_models import (
        CompareRegressionBaselineRequest,
        CreateRegressionBaselineRequest,
    )
    from ugh_quantamental.replay.baselines import (
        compare_regression_baseline,
        create_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    bundle = create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(baseline_name="compare-exact", suite_request=suite_req),
    )
    result = compare_regression_baseline(
        db_session,
        CompareRegressionBaselineRequest(baseline_id=bundle.baseline.baseline_id),
    )

    assert result is not None
    assert result.comparison.exact_match is True
    assert result.comparison.case_count_match is True
    assert result.comparison.passed_case_count_diff == 0
    assert result.comparison.total_mismatch_count_diff == 0
    assert all(d.passed_match is True for d in result.comparison.case_deltas)


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_compare_baseline_by_name(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from ugh_quantamental.replay.baseline_models import (
        CompareRegressionBaselineRequest,
        CreateRegressionBaselineRequest,
    )
    from ugh_quantamental.replay.baselines import (
        compare_regression_baseline,
        create_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(baseline_name="compare-by-name", suite_request=suite_req),
    )
    result = compare_regression_baseline(
        db_session,
        CompareRegressionBaselineRequest(baseline_name="compare-by-name"),
    )
    assert result is not None
    assert result.comparison.exact_match is True


# ---------------------------------------------------------------------------
# compare_regression_baseline — missing baseline
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_compare_missing_baseline_returns_none(db_session) -> None:
    from ugh_quantamental.replay.baseline_models import CompareRegressionBaselineRequest
    from ugh_quantamental.replay.baselines import compare_regression_baseline

    result = compare_regression_baseline(
        db_session,
        CompareRegressionBaselineRequest(baseline_id="base_nonexistent"),
    )
    assert result is None


# ---------------------------------------------------------------------------
# compare_regression_baseline — mismatch detection
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_compare_baseline_detects_mismatch(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    """Alter stored suite_result_json after creation; compare must detect non-match."""
    from ugh_quantamental.persistence.models import RegressionSuiteBaselineRecord
    from ugh_quantamental.replay.baseline_models import (
        CompareRegressionBaselineRequest,
        CreateRegressionBaselineRequest,
    )
    from ugh_quantamental.replay.baselines import (
        compare_regression_baseline,
        create_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    bundle = create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(baseline_name="mismatch-test", suite_request=suite_req),
    )

    # Corrupt the stored result by overwriting passed_case_count in aggregate
    record = db_session.get(RegressionSuiteBaselineRecord, bundle.baseline.baseline_id)
    assert record is not None
    corrupted = dict(record.suite_result_json)
    corrupted["aggregate"] = dict(corrupted["aggregate"])
    corrupted["aggregate"]["passed_case_count"] = 99  # fabricated value
    corrupted["projection_cases"] = [
        {**c, "passed": False} for c in corrupted["projection_cases"]
    ]
    record.suite_result_json = corrupted
    db_session.flush()

    result = compare_regression_baseline(
        db_session,
        CompareRegressionBaselineRequest(baseline_id=bundle.baseline.baseline_id),
    )

    assert result is not None
    assert result.comparison.exact_match is False
    # passed_case_count_diff = current (1 passing) - stored (99) = negative
    assert result.comparison.passed_case_count_diff < 0
    # at least one case has mismatched passed flag
    assert any(d.passed_match is False for d in result.comparison.case_deltas)


# ---------------------------------------------------------------------------
# compare does not write
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_compare_does_not_write(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    """compare_regression_baseline must not modify the session state."""
    from ugh_quantamental.replay.baseline_models import (
        CompareRegressionBaselineRequest,
        CreateRegressionBaselineRequest,
    )
    from ugh_quantamental.replay.baselines import (
        compare_regression_baseline,
        create_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    bundle = create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(
            baseline_name="no-write-compare", suite_request=suite_req
        ),
    )
    db_session.commit()  # clean state before compare

    compare_regression_baseline(
        db_session,
        CompareRegressionBaselineRequest(baseline_id=bundle.baseline.baseline_id),
    )

    # Session must have no pending dirty or new objects after compare
    assert not db_session.dirty
    assert not db_session.new


# ---------------------------------------------------------------------------
# created_at naive-UTC round-trip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_baseline_created_at_naive_utc(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    from datetime import timezone

    from ugh_quantamental.replay.baseline_models import CreateRegressionBaselineRequest
    from ugh_quantamental.replay.baselines import create_regression_baseline

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    aware_ts = __import__("datetime").datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    bundle = create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(
            baseline_name="utc-test",
            suite_request=suite_req,
            created_at=aware_ts,
        ),
    )
    stored = bundle.baseline.created_at
    # Must be naive (no tzinfo)
    assert stored.tzinfo is None
    # Must preserve the UTC time value
    assert stored.year == 2026
    assert stored.month == 6
    assert stored.hour == 12


# ---------------------------------------------------------------------------
# case_deltas group separation — same name in projection and state groups
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_compare_case_deltas_have_group_field(
    db_session, question_features, signal_features, alignment_inputs,
) -> None:
    """Each RegressionSuiteCaseDelta must carry a group field ('projection'/'state')."""
    from ugh_quantamental.replay.baseline_models import (
        CompareRegressionBaselineRequest,
        CreateRegressionBaselineRequest,
    )
    from ugh_quantamental.replay.baselines import (
        compare_regression_baseline,
        create_regression_baseline,
    )

    _, suite_req = _make_suite_request_with_run(
        db_session, question_features, signal_features, alignment_inputs
    )
    bundle = create_regression_baseline(
        db_session,
        CreateRegressionBaselineRequest(baseline_name="group-field-test", suite_request=suite_req),
    )
    result = compare_regression_baseline(
        db_session,
        CompareRegressionBaselineRequest(baseline_id=bundle.baseline.baseline_id),
    )

    assert result is not None
    for delta in result.comparison.case_deltas:
        assert delta.group in ("projection", "state"), (
            f"unexpected group {delta.group!r} on delta {delta.name!r}"
        )
    # The fixture creates a projection-only suite, so all deltas must be projection
    assert all(d.group == "projection" for d in result.comparison.case_deltas)
