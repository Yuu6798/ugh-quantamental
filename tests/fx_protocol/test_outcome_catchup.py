"""Tests for the outcome catch-up feature (FX-OUTCOME-CATCHUP).

Covers:
- FxDailyAutomationConfig.outcome_catchup_days (typed field)
- CatchupWindowResult (new per-window result type)
- FxDailyAutomationResult.catchup_windows (new tuple field)
- request_builders.catchup_window_candidates / build_outcome_request_for_window
- csv_exports.publish_csv_to_history_only
- run_fx_daily_protocol_once end-to-end catch-up recovery, idempotency, and
  lookback-bound exclusion, modeling "D1 forecast issued -> D2 run missing ->
  D3/D4 run recovers D1" per docs/briefs/2026-08_FX-OUTCOME-CATCHUP.md.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.automation_models import (
    CatchupWindowResult,
    FxDailyAutomationConfig,
    FxDailyAutomationResult,
)
from ugh_quantamental.fx_protocol.data_models import (
    FxCompletedWindow,
    FxProtocolMarketSnapshot,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_JST = ZoneInfo("Asia/Tokyo")
_UTC = timezone.utc


# ---------------------------------------------------------------------------
# Shared window-building helpers
# ---------------------------------------------------------------------------


def _build_windows(n: int) -> tuple[FxCompletedWindow, ...]:
    """Build n consecutive business-day FxCompletedWindow objects."""
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)  # Monday
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        windows.append(
            FxCompletedWindow(
                window_start_jst=start,
                window_end_jst=end,
                open_price=149.5,
                high_price=151.5,
                low_price=148.5,
                close_price=150.5,
            )
        )
        start = end
        count += 1
    return tuple(windows)


def _provenance() -> MarketDataProvenance:
    return MarketDataProvenance(
        vendor="test",
        feed_name="feed",
        price_type="mid",
        resolution="1d",
        timezone="Asia/Tokyo",
        retrieved_at_utc=datetime(2026, 3, 14, 0, 0, 0, tzinfo=_UTC),
    )


def _snapshot_with_n_windows(n: int) -> FxProtocolMarketSnapshot:
    """Snapshot whose as_of_jst equals the end of its newest completed window."""
    wins = _build_windows(n)
    as_of = wins[-1].window_end_jst
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of,
        current_spot=150.0,
        completed_windows=wins,
        market_data_provenance=_provenance(),
    )


# ---------------------------------------------------------------------------
# FxDailyAutomationConfig.outcome_catchup_days
# ---------------------------------------------------------------------------


class TestOutcomeCatchupDaysConfig:
    def test_default_is_five(self) -> None:
        cfg = FxDailyAutomationConfig()
        assert cfg.outcome_catchup_days == 5

    def test_custom_value(self) -> None:
        cfg = FxDailyAutomationConfig(outcome_catchup_days=10)
        assert cfg.outcome_catchup_days == 10

    def test_zero_allowed(self) -> None:
        cfg = FxDailyAutomationConfig(outcome_catchup_days=0)
        assert cfg.outcome_catchup_days == 0

    def test_negative_rejected(self) -> None:
        with pytest.raises(Exception):
            FxDailyAutomationConfig(outcome_catchup_days=-1)

    def test_frozen(self) -> None:
        cfg = FxDailyAutomationConfig()
        with pytest.raises(Exception):
            cfg.outcome_catchup_days = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CatchupWindowResult
# ---------------------------------------------------------------------------


class TestCatchupWindowResult:
    def _make(self, **overrides) -> CatchupWindowResult:
        base = dict(
            window_start_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            window_end_jst=datetime(2026, 3, 11, 8, 0, 0, tzinfo=_JST),
            forecast_batch_id="fb_test",
            outcome_id="oc_test",
            evaluation_count=7,
        )
        base.update(overrides)
        return CatchupWindowResult(**base)

    def test_construction(self) -> None:
        cu = self._make()
        assert cu.forecast_batch_id == "fb_test"
        assert cu.evaluation_count == 7
        assert cu.outcome_csv_path is None
        assert cu.evaluation_csv_path is None

    def test_frozen(self) -> None:
        cu = self._make()
        with pytest.raises(Exception):
            cu.evaluation_count = 0  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(Exception):
            CatchupWindowResult(
                window_start_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
                window_end_jst=datetime(2026, 3, 11, 8, 0, 0, tzinfo=_JST),
                forecast_batch_id="fb_test",
                outcome_id="oc_test",
                evaluation_count=7,
                unexpected_field="nope",  # type: ignore[call-arg]
            )


# ---------------------------------------------------------------------------
# FxDailyAutomationResult.catchup_windows
# ---------------------------------------------------------------------------


class TestResultCatchupWindowsField:
    def test_default_is_empty_tuple(self) -> None:
        r = FxDailyAutomationResult(as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))
        assert r.catchup_windows == ()
        assert isinstance(r.catchup_windows, tuple)

    def test_construction_and_order_preserved(self) -> None:
        cu1 = CatchupWindowResult(
            window_start_jst=datetime(2026, 3, 8, 8, 0, 0, tzinfo=_JST),
            window_end_jst=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
            forecast_batch_id="fb_1",
            outcome_id="oc_1",
            evaluation_count=7,
        )
        cu2 = CatchupWindowResult(
            window_start_jst=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
            window_end_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            forecast_batch_id="fb_2",
            outcome_id="oc_2",
            evaluation_count=7,
        )
        r = FxDailyAutomationResult(
            as_of_jst=datetime(2026, 3, 11, 8, 0, 0, tzinfo=_JST),
            catchup_windows=(cu1, cu2),
        )
        assert r.catchup_windows == (cu1, cu2)
        assert r.catchup_windows[0].forecast_batch_id == "fb_1"
        assert r.catchup_windows[1].forecast_batch_id == "fb_2"

    def test_frozen_no_append(self) -> None:
        """A frozen tuple field cannot be mutated by append/remove/reorder."""
        r = FxDailyAutomationResult(as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))
        with pytest.raises(AttributeError):
            r.catchup_windows.append(  # type: ignore[attr-defined]
                CatchupWindowResult(
                    window_start_jst=datetime(2026, 3, 8, 8, 0, 0, tzinfo=_JST),
                    window_end_jst=datetime(2026, 3, 9, 8, 0, 0, tzinfo=_JST),
                    forecast_batch_id="fb_1",
                    outcome_id="oc_1",
                    evaluation_count=7,
                )
            )
        with pytest.raises(Exception):
            r.catchup_windows = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# request_builders.catchup_window_candidates / build_outcome_request_for_window
# ---------------------------------------------------------------------------


class TestCatchupWindowCandidates:
    def test_zero_max_days_returns_empty(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import catchup_window_candidates

        snap = _snapshot_with_n_windows(20)
        assert catchup_window_candidates(snap, max_business_days=0) == ()

    def test_excludes_the_immediately_preceding_window(self) -> None:
        """Distance-0 window (handled by previous_window_matches) is never a candidate."""
        from ugh_quantamental.fx_protocol.request_builders import catchup_window_candidates

        snap = _snapshot_with_n_windows(20)
        newest = snap.completed_windows[-1]
        candidates = catchup_window_candidates(snap, max_business_days=5)
        assert newest not in candidates

    def test_returns_bounded_lookback_oldest_first(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import catchup_window_candidates

        snap = _snapshot_with_n_windows(20)
        candidates = catchup_window_candidates(snap, max_business_days=5)
        # windows[14..18] (5 windows, distances 5..1) — oldest (largest distance) first.
        expected = snap.completed_windows[14:19]
        assert candidates == expected

    def test_lookback_excludes_windows_beyond_bound(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import catchup_window_candidates

        snap = _snapshot_with_n_windows(20)
        candidates = catchup_window_candidates(snap, max_business_days=1)
        assert len(candidates) == 1
        assert candidates[0] == snap.completed_windows[-2]

    def test_larger_max_than_available_history_is_safe(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import catchup_window_candidates

        snap = _snapshot_with_n_windows(20)
        candidates = catchup_window_candidates(snap, max_business_days=100)
        # Only 19 windows are older than the newest (distance 0) one.
        assert len(candidates) == 19
        assert candidates[0] == snap.completed_windows[0]
        assert candidates[-1] == snap.completed_windows[-2]

    def test_misaligned_as_of_jst_rejects_windows_rather_than_misreport_distance(
        self,
    ) -> None:
        """FIX 7: FxProtocolMarketSnapshot.as_of_jst carries no business-day/
        08:00 alignment validator (unlike FxCompletedWindow's own endpoints),
        so a caller can hand catchup_window_candidates a snapshot whose
        as_of_jst is off the canonical grid (e.g. mid-afternoon rather than
        08:00 JST). prev_as_of_jst only ever looks at the *date* part, so the
        very first step from such an as_of_jst jumps clean past the newest
        window's end without ever landing on it exactly. The old code
        returned whatever lag the walk happened to overshoot to; the fixed
        guard must reject the window instead."""
        from ugh_quantamental.fx_protocol.request_builders import catchup_window_candidates

        snap = _snapshot_with_n_windows(20)
        # Same calendar date as the newest window's end, but not on the 08:00
        # JST grid at all. prev_as_of_jst ignores time-of-day, so the very
        # first step lands one full business day further back (Friday),
        # skipping clean past the newest window's (Monday) end.
        misaligned_as_of = snap.as_of_jst.replace(hour=14, minute=0, second=0)
        snap_misaligned = snap.model_copy(update={"as_of_jst": misaligned_as_of})
        newest = snap.completed_windows[-1]

        candidates = catchup_window_candidates(snap_misaligned, max_business_days=100)

        # The newest window's end is unreachable by any exact prev_as_of_jst
        # step from this as_of_jst — it must be rejected, not (as the old,
        # unguarded code did) reported as a spurious distance-1 candidate
        # merely because the walk happened to overshoot past it after one
        # step. Every older, genuinely-aligned window is still found normally.
        assert newest not in candidates
        assert len(candidates) == len(snap.completed_windows) - 1

    def test_business_day_lag_returns_none_for_misaligned_end(self) -> None:
        """Direct unit coverage of the one-line guard on _business_day_lag."""
        from ugh_quantamental.fx_protocol.request_builders import _business_day_lag

        as_of = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)  # Monday
        # Saturday 08:00 JST is never reachable via prev_as_of_jst steps from
        # a Monday as_of (Monday -> Friday, skipping the weekend entirely).
        misaligned_end = datetime(2026, 1, 3, 8, 0, 0, tzinfo=_JST)
        assert _business_day_lag(misaligned_end, as_of, max_lag=10) is None

    def test_business_day_lag_returns_lag_for_aligned_end(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import _business_day_lag

        as_of = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)  # Monday
        aligned_end = datetime(2026, 1, 2, 8, 0, 0, tzinfo=_JST)  # Friday, distance 1
        assert _business_day_lag(aligned_end, as_of, max_lag=10) == 1


class TestBuildOutcomeRequestForWindow:
    def test_matches_window_fields(self) -> None:
        from ugh_quantamental.fx_protocol.request_builders import (
            build_outcome_request_for_window,
        )

        snap = _snapshot_with_n_windows(20)
        window = snap.completed_windows[10]
        req = build_outcome_request_for_window(
            window,
            pair=snap.pair,
            market_data_provenance=snap.market_data_provenance,
            schema_version="v1",
            protocol_version="v1",
        )
        assert req.window_start_jst == window.window_start_jst
        assert req.window_end_jst == window.window_end_jst
        assert req.realized_open == window.open_price
        assert req.realized_high == window.high_price
        assert req.realized_low == window.low_price
        assert req.realized_close == window.close_price
        assert req.pair == snap.pair

    def test_build_daily_outcome_request_still_matches_newest(self) -> None:
        """Refactor regression: build_daily_outcome_request output is unchanged."""
        from ugh_quantamental.fx_protocol.request_builders import build_daily_outcome_request

        snap = _snapshot_with_n_windows(20)
        req = build_daily_outcome_request(snap, schema_version="v1", protocol_version="v1")
        newest = snap.completed_windows[-1]
        assert req.window_start_jst == newest.window_start_jst
        assert req.window_end_jst == newest.window_end_jst
        assert req.realized_close == newest.close_price


# ---------------------------------------------------------------------------
# csv_exports.publish_csv_to_history_only
# ---------------------------------------------------------------------------


class TestPublishCsvToHistoryOnly:
    def test_writes_history_only_not_latest(self) -> None:
        from ugh_quantamental.fx_protocol.csv_exports import publish_csv_to_history_only

        with tempfile.TemporaryDirectory() as tmpdir:
            outcome_src = os.path.join(tmpdir, "src_outcome.csv")
            eval_src = os.path.join(tmpdir, "src_eval.csv")
            with open(outcome_src, "w", encoding="utf-8") as fh:
                fh.write("outcome_id\nfoo\n")
            with open(eval_src, "w", encoding="utf-8") as fh:
                fh.write("evaluation_id\nbar\n")

            result = publish_csv_to_history_only(
                tmpdir, "20260310", "fb_hist_test", outcome_src, eval_src
            )

            history_outcome = os.path.join(tmpdir, "history", "20260310", "fb_hist_test", "outcome.csv")
            history_eval = os.path.join(
                tmpdir, "history", "20260310", "fb_hist_test", "evaluation.csv"
            )
            assert os.path.isfile(history_outcome)
            assert os.path.isfile(history_eval)
            assert result["history_outcome"] == "history/20260310/fb_hist_test/outcome.csv"
            assert result["history_evaluation"] == "history/20260310/fb_hist_test/evaluation.csv"

            # latest/ must not exist at all — this function never touches it.
            assert not os.path.exists(os.path.join(tmpdir, "latest"))

    def test_none_paths_produce_none_results(self) -> None:
        from ugh_quantamental.fx_protocol.csv_exports import publish_csv_to_history_only

        with tempfile.TemporaryDirectory() as tmpdir:
            result = publish_csv_to_history_only(tmpdir, "20260310", "fb_hist_test", None, None)
            assert result["history_outcome"] is None
            assert result["history_evaluation"] is None

    def test_does_not_write_forecast_csv_when_omitted(self) -> None:
        from ugh_quantamental.fx_protocol.csv_exports import publish_csv_to_history_only

        with tempfile.TemporaryDirectory() as tmpdir:
            publish_csv_to_history_only(tmpdir, "20260310", "fb_hist_test", None, None)
            forecast_path = os.path.join(
                tmpdir, "history", "20260310", "fb_hist_test", "forecast.csv"
            )
            assert not os.path.exists(forecast_path)

    def test_writes_forecast_csv_when_given(self) -> None:
        """FIX 1 amendment: an optional forecast_path republishes that batch's
        forecast rows alongside outcome/evaluation, so the recovered window's
        end-date directory is self-contained for
        labeled_observations.collect_evaluated_forecast_rows."""
        from ugh_quantamental.fx_protocol.csv_exports import publish_csv_to_history_only

        with tempfile.TemporaryDirectory() as tmpdir:
            forecast_src = os.path.join(tmpdir, "src_forecast.csv")
            with open(forecast_src, "w", encoding="utf-8") as fh:
                fh.write("forecast_id\nbaz\n")

            result = publish_csv_to_history_only(
                tmpdir, "20260310", "fb_hist_test", None, None, forecast_path=forecast_src
            )

            forecast_path = os.path.join(
                tmpdir, "history", "20260310", "fb_hist_test", "forecast.csv"
            )
            assert os.path.isfile(forecast_path)
            assert result["history_forecast"] == "history/20260310/fb_hist_test/forecast.csv"


# ---------------------------------------------------------------------------
# End-to-end: run_fx_daily_protocol_once outcome catch-up
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestOutcomeCatchupEndToEnd:
    """D1 forecast issued -> D2 run missing -> D3 run recovers D1 (per the brief's fixture).

    Window indexing (business days bd[0], bd[1], ... starting Monday 2026-01-05):
    - Day1 = bd[20]: forecast issued for window bd[20]->bd[21] ("D1's window" —
      the one that later needs recovering; mirrors the real 2026-08-27 batch).
    - Day2 = bd[21]: run MISSING entirely (no automation call at all — mirrors
      the real 2026-08-28 business-day-guard refusal).
    - Day3 = bd[22]: forecast issued for window bd[22]->bd[23]. Its own Step 4
      (current window bd[21]->bd[22]) is skipped because Day2's run never
      created a forecast batch for that window (existing _prior_batch_ready
      behaviour, unchanged by this brief). Step 4b (catch-up) recovers window
      bd[20]->bd[21] (distance 1 business day from bd[22]).

    A deeper 2-business-day gap (Day2 AND Day3 both missing, recovered on
    Day4) is used separately to exercise the lookback bound.
    """

    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def _run(self, session, n_windows: int, cfg: FxDailyAutomationConfig):
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _snapshot_with_n_windows(n_windows)
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)
        return snap, result

    def test_catchup_recovers_gap_window(self) -> None:
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )

                # Day1: forecast issued for window bd[20]->bd[21].
                snap1, r1 = self._run(session, 20, cfg)
                session.commit()
                d1_forecast_batch_id = r1.forecast_batch_id
                assert r1.forecast_created is True

                # Day2: run missing entirely — no call.

                # Day3: forecast for bd[22]->bd[23]; current window (bd21->bd22)
                # skipped (no batch for Day2's window — existing behaviour,
                # back-compat singular fields unchanged). Catch-up recovers D1.
                snap3, r3 = self._run(session, 22, cfg)
                session.commit()

                # Singular fields describe ONLY the immediately-preceding window
                # (bd21->bd22), which has no forecast batch — back-compat unchanged.
                assert r3.forecast_created is True
                assert r3.outcome_recorded is False
                assert r3.outcome_id is None
                assert r3.evaluation_count == 0

                # Catch-up recovered exactly one window: D1's. D1's *forecast*
                # window is (snap1.as_of_jst -> next business day) — the window
                # the forecast workflow created, not snap1's own newest
                # completed_windows entry (that's one business day earlier,
                # part of D1's trailing baseline history).
                from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

                assert len(r3.catchup_windows) == 1
                cu = r3.catchup_windows[0]
                assert cu.window_start_jst == snap1.as_of_jst
                assert cu.window_end_jst == next_as_of_jst(snap1.as_of_jst)
                assert cu.forecast_batch_id == d1_forecast_batch_id
                assert cu.evaluation_count == 7
                assert cu.outcome_csv_path is not None
                assert cu.evaluation_csv_path is not None

                # History-only export landed under the recovered window's END
                # date — never its start date, which is the SAME directory
                # the originating batch already owns for its own forecast.csv
                # (and, if that start day was itself a normal eval day, the
                # previous window's outcome/evaluation) and must not collide
                # with.
                date_str = cu.window_end_jst.strftime("%Y%m%d")
                hist_eval = os.path.join(
                    tmpdir, "history", date_str, d1_forecast_batch_id, "evaluation.csv"
                )
                hist_outcome = os.path.join(
                    tmpdir, "history", date_str, d1_forecast_batch_id, "outcome.csv"
                )
                assert os.path.isfile(hist_eval)
                assert os.path.isfile(hist_outcome)

                # latest/ must still reflect Day3's own (current) batch, not D1's,
                # and must NOT gain an outcome/evaluation file from the catch-up
                # (Day3's own outcome_id is None; history-only export never
                # touches latest/).
                assert os.path.isfile(os.path.join(tmpdir, "latest", "forecast.csv"))
                assert not os.path.exists(os.path.join(tmpdir, "latest", "outcome.csv"))
                assert not os.path.exists(os.path.join(tmpdir, "latest", "evaluation.csv"))

                import json

                with open(
                    os.path.join(tmpdir, "latest", "manifest.json"), encoding="utf-8"
                ) as fh:
                    manifest = json.load(fh)
                assert manifest["forecast_batch_id"] == r3.forecast_batch_id
                assert manifest["forecast_batch_id"] != d1_forecast_batch_id
        finally:
            session.close()

    def test_catchup_idempotent_on_rerun(self) -> None:
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                self._run(session, 20, cfg)
                session.commit()

                # Day3, run #1: recovers D1's window.
                _, r3a = self._run(session, 22, cfg)
                session.commit()
                assert len(r3a.catchup_windows) == 1
                d1_outcome_id = r3a.catchup_windows[0].outcome_id

                # Day3, run #2 (same session, same as_of): must not duplicate.
                _, r3b = self._run(session, 22, cfg)
                session.commit()
                assert r3b.catchup_windows == ()

                from ugh_quantamental.persistence.repositories import (
                    FxOutcomeEvaluationRepository,
                )

                evals = FxOutcomeEvaluationRepository.load_fx_evaluation_batch(
                    session, d1_outcome_id
                )
                assert evals is not None
                assert len(evals) == 7
        finally:
            session.close()

    def test_catchup_recovers_two_day_gap_with_default_bound(self) -> None:
        """Two consecutive missing days (D2, D3): D4 recovers D1 at distance 2."""
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                snap1, r1 = self._run(session, 20, cfg)
                session.commit()
                d1_forecast_batch_id = r1.forecast_batch_id

                # Day2 and Day3: both missing entirely.

                # Day4 (n=23): recovers D1's window at distance 2.
                _, r4 = self._run(session, 23, cfg)
                session.commit()

                assert len(r4.catchup_windows) == 1
                cu = r4.catchup_windows[0]
                assert cu.forecast_batch_id == d1_forecast_batch_id
                assert cu.window_start_jst == snap1.as_of_jst
                # The current (distance-0) window's own batch is also missing
                # (Day3 never ran), so today's singular outcome fields stay empty.
                assert r4.outcome_recorded is False
        finally:
            session.close()

    def test_lookback_bound_excludes_window_beyond_catchup_days(self) -> None:
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                    outcome_catchup_days=1,  # D1's window is at distance 2 from Day4.
                )
                self._run(session, 20, cfg)
                session.commit()
                # Day2 and Day3: both missing entirely.
                _, r4 = self._run(session, 23, cfg)
                session.commit()

                # Excluded: distance 2 > outcome_catchup_days=1.
                assert r4.catchup_windows == ()
        finally:
            session.close()

    def test_catchup_disabled_when_outcome_catchup_days_zero(self) -> None:
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                    outcome_catchup_days=0,
                )
                self._run(session, 20, cfg)
                session.commit()
                # Day2: missing entirely.
                _, r3 = self._run(session, 22, cfg)
                session.commit()
                assert r3.catchup_windows == ()
        finally:
            session.close()

    def test_no_gap_day_backcompat_empty_catchup_and_unchanged_singular_fields(self) -> None:
        """No missed run in between: catch-up finds nothing; singular fields as before."""
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                # Day1: forecast for bd20->bd21.
                self._run(session, 20, cfg)
                session.commit()
                # Day2 (bd21): normal consecutive run — no gap.
                _, r2 = self._run(session, 21, cfg)
                session.commit()

                assert r2.outcome_recorded is True
                assert r2.evaluation_count == 7
                assert r2.catchup_windows == ()
        finally:
            session.close()

    def test_failed_catchup_flush_isolated_from_outer_transaction(self) -> None:
        """A flush failure inside catch-up must not poison today's outer transaction."""
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                self._run(session, 20, cfg)
                session.commit()

                from sqlalchemy import event
                from ugh_quantamental.fx_protocol import outcomes as outcomes_module

                real_workflow = outcomes_module.run_daily_outcome_evaluation_workflow

                def fail_during_flush(active_session, request):
                    @event.listens_for(active_session, "before_flush", once=True)
                    def _raise_once(*_args, **_kwargs):
                        raise RuntimeError("synthetic catch-up flush failure")

                    return real_workflow(active_session, request)

                with patch.object(
                    outcomes_module,
                    "run_daily_outcome_evaluation_workflow",
                    side_effect=fail_during_flush,
                ):
                    _, r3 = self._run(session, 22, cfg)

                assert r3.forecast_created is True
                assert r3.catchup_windows == ()
                session.commit()

                from ugh_quantamental.persistence.repositories import FxForecastRepository

                current = FxForecastRepository.load_fx_forecast_batch(
                    session, r3.forecast_batch_id
                )
                assert current is not None
                assert len(current.forecasts) == 7
        finally:
            session.close()

    def test_rerun_repairs_missing_history_after_db_recovery(self) -> None:
        """Persisted DB evaluations must not suppress retry of missing history CSVs."""
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                self._run(session, 20, cfg)
                session.commit()
                _, first = self._run(session, 22, cfg)
                session.commit()
                assert len(first.catchup_windows) == 1
                cu = first.catchup_windows[0]

                history_dir = os.path.join(
                    tmpdir,
                    "history",
                    cu.window_end_jst.strftime("%Y%m%d"),
                    cu.forecast_batch_id,
                )
                eval_path = os.path.join(history_dir, "evaluation.csv")
                assert os.path.isfile(eval_path)
                os.remove(eval_path)

                _, retry = self._run(session, 22, cfg)
                session.commit()
                assert len(retry.catchup_windows) == 1
                assert retry.catchup_windows[0].outcome_id == cu.outcome_id
                assert os.path.isfile(eval_path)

                from ugh_quantamental.persistence.repositories import (
                    FxOutcomeEvaluationRepository,
                )

                evals = FxOutcomeEvaluationRepository.load_fx_evaluation_batch(
                    session, cu.outcome_id
                )
                assert evals is not None
                assert len(evals) == 7
        finally:
            session.close()

    def test_missing_forecast_batch_skipped_not_raised(self) -> None:
        """A catch-up candidate whose forecast batch was never created is skipped,
        not raised, and today's own forecast/outcome proceed normally."""
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                )
                # Day1: forecast for bd20->bd21.
                self._run(session, 20, cfg)
                session.commit()
                # Day2: missing entirely (no batch ever created for bd21->bd22).
                # Day3: forecast for bd22->bd23; current window (bd21->bd22) has
                # no batch so is skipped; must not raise.
                _, r3 = self._run(session, 22, cfg)
                session.commit()
                assert r3.forecast_created is True
                assert r3.outcome_recorded is False
        finally:
            session.close()

    def test_catchup_does_not_overwrite_normal_days_own_history_dir(self) -> None:
        """FIX 1: catch-up must publish under the recovered window's END date,
        never its START date. The start-date directory is already owned by
        that window's own originating batch — which used it, on ITS OWN day,
        to file the *previous* window's evaluation under the exact batch id
        catch-up recomputes as cu_batch_id for this window. Publishing there
        would silently overwrite that already-archived outcome.csv /
        evaluation.csv.
        """
        session = self._make_session()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cfg = FxDailyAutomationConfig(
                    run_outcome_evaluation=True,
                    run_forecast_generation=True,
                    write_csv_exports=True,
                    csv_output_dir=tmpdir,
                    # Bound to distance 1 so Day4's catch-up only considers
                    # window bd21->bd22 (this test's target). At the default
                    # bound, bd20->bd21 (Day1's window, distance 2, already
                    # evaluated normally by Day2's Step 4) would ALSO surface
                    # as a candidate — a separate, pre-existing history-key
                    # mismatch between Step 4's own publish location and
                    # catch-up's completeness check that is out of scope for
                    # this fix; isolate this test from it.
                    outcome_catchup_days=1,
                )
                # Day1 (n=20): forecast for window bd20->bd21.
                self._run(session, 20, cfg)
                session.commit()

                # Day2 (n=21, "Day S"): normal run, no gap. Evaluates window
                # bd20->bd21 (Day1's window) and publishes it under
                # history/{S}/{batch predicting bd21->bd22}/ — the SAME batch
                # id catch-up will later compute as cu_batch_id for window
                # bd21->bd22 (make_forecast_batch_id is keyed by a window's
                # START, and bd21 is both "Day2's own as_of" and "window
                # bd21->bd22's start").
                snap2, r2 = self._run(session, 21, cfg)
                session.commit()
                assert r2.outcome_recorded is True
                day2_batch_id = r2.forecast_batch_id
                date_s = snap2.as_of_jst.strftime("%Y%m%d")

                original_outcome_path = os.path.join(
                    tmpdir, "history", date_s, day2_batch_id, "outcome.csv"
                )
                original_evaluation_path = os.path.join(
                    tmpdir, "history", date_s, day2_batch_id, "evaluation.csv"
                )
                assert os.path.isfile(original_outcome_path)
                assert os.path.isfile(original_evaluation_path)
                with open(original_outcome_path, encoding="utf-8") as fh:
                    original_outcome_content = fh.read()
                with open(original_evaluation_path, encoding="utf-8") as fh:
                    original_evaluation_content = fh.read()

                # Day3: missing entirely (gap).

                # Day4 (n=23): recovers window bd21->bd22 -- predicted by
                # day2_batch_id, the SAME batch id keying Day2's own history
                # dir above.
                from ugh_quantamental.fx_protocol.calendar import next_as_of_jst

                _, r4 = self._run(session, 23, cfg)
                session.commit()
                assert len(r4.catchup_windows) == 1
                cu = r4.catchup_windows[0]
                assert cu.forecast_batch_id == day2_batch_id
                assert cu.window_start_jst == snap2.as_of_jst
                assert cu.window_end_jst == next_as_of_jst(snap2.as_of_jst)

                # Day2's own history dir (evaluation of window bd20->bd21)
                # is byte-for-byte untouched by the later recovery.
                with open(original_outcome_path, encoding="utf-8") as fh:
                    assert fh.read() == original_outcome_content
                with open(original_evaluation_path, encoding="utf-8") as fh:
                    assert fh.read() == original_evaluation_content

                # The recovered window (bd21->bd22) landed under ITS OWN end
                # date -- a directory distinct from Day2's own (date_s).
                recovered_date_s = cu.window_end_jst.strftime("%Y%m%d")
                assert recovered_date_s != date_s
                recovered_outcome_path = os.path.join(
                    tmpdir, "history", recovered_date_s, day2_batch_id, "outcome.csv"
                )
                recovered_evaluation_path = os.path.join(
                    tmpdir, "history", recovered_date_s, day2_batch_id, "evaluation.csv"
                )
                assert os.path.isfile(recovered_outcome_path)
                assert os.path.isfile(recovered_evaluation_path)
                # Recovered content differs from Day2's own (a different window).
                with open(recovered_evaluation_path, encoding="utf-8") as fh:
                    assert fh.read() != original_evaluation_content
        finally:
            session.close()
