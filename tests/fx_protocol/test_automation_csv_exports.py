"""Tests for automation CSV export integration (automation_models + automation.py)."""

from __future__ import annotations

import importlib.util
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from ugh_quantamental.fx_protocol.automation_models import (
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
# FxDailyAutomationConfig — new fields
# ---------------------------------------------------------------------------


class TestAutomationConfigCsvFields:
    def test_defaults(self) -> None:
        cfg = FxDailyAutomationConfig()
        assert cfg.write_csv_exports is True
        assert cfg.csv_output_dir == "./data/csv"

    def test_disable_csv(self) -> None:
        cfg = FxDailyAutomationConfig(write_csv_exports=False)
        assert cfg.write_csv_exports is False

    def test_custom_csv_dir(self) -> None:
        cfg = FxDailyAutomationConfig(csv_output_dir="/tmp/mycsv")
        assert cfg.csv_output_dir == "/tmp/mycsv"

    def test_frozen(self) -> None:
        cfg = FxDailyAutomationConfig()
        with pytest.raises(Exception):
            cfg.write_csv_exports = False  # type: ignore[misc]

    def test_empty_csv_output_dir_rejected(self) -> None:
        with pytest.raises(Exception):
            FxDailyAutomationConfig(csv_output_dir="")


# ---------------------------------------------------------------------------
# FxDailyAutomationResult — new fields
# ---------------------------------------------------------------------------


class TestAutomationResultCsvFields:
    def test_defaults_are_none(self) -> None:
        r = FxDailyAutomationResult(
            as_of_jst=datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
        )
        assert r.forecast_csv_path is None
        assert r.outcome_csv_path is None
        assert r.evaluation_csv_path is None
        assert r.manifest_path is None

    def test_with_csv_paths(self) -> None:
        r = FxDailyAutomationResult(
            as_of_jst=datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST),
            forecast_csv_path="/tmp/csv/forecasts/USDJPY_20260314_forecast.csv",
            outcome_csv_path="/tmp/csv/outcomes/USDJPY_20260314_outcome.csv",
            evaluation_csv_path="/tmp/csv/evaluations/USDJPY_20260314_evaluation.csv",
        )
        assert r.forecast_csv_path is not None
        assert r.outcome_csv_path is not None
        assert r.evaluation_csv_path is not None

    def test_frozen(self) -> None:
        r = FxDailyAutomationResult(
            as_of_jst=datetime(2026, 3, 14, 8, 0, 0, tzinfo=_JST)
        )
        with pytest.raises(Exception):
            r.forecast_csv_path = "/tmp/x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Helpers for full automation tests
# ---------------------------------------------------------------------------


def _build_windows(n: int) -> tuple[FxCompletedWindow, ...]:
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
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


def _make_snapshot() -> FxProtocolMarketSnapshot:
    wins = _build_windows(20)
    as_of = wins[-1].window_end_jst
    return FxProtocolMarketSnapshot(
        pair=CurrencyPair.USDJPY,
        as_of_jst=as_of,
        current_spot=150.0,
        completed_windows=wins,
        market_data_provenance=MarketDataProvenance(
            vendor="test",
            feed_name="feed",
            price_type="mid",
            resolution="1d",
            timezone="Asia/Tokyo",
            retrieved_at_utc=datetime(2026, 3, 14, 0, 0, 0, tzinfo=_UTC),
        ),
    )


# ---------------------------------------------------------------------------
# Full automation run — CSV integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestAutomationCsvIntegration:
    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def test_forecast_csv_written_when_enabled(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            assert result.forecast_csv_path is not None
            assert os.path.isfile(result.forecast_csv_path)
            assert result.outcome_csv_path is None
            assert result.evaluation_csv_path is None
        session.close()

    def test_no_csv_written_when_disabled(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=False,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            assert result.forecast_csv_path is None
            assert result.outcome_csv_path is None
            assert result.evaluation_csv_path is None
        session.close()

    def test_forecast_csv_has_four_rows(self) -> None:
        import csv

        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            assert result.forecast_csv_path is not None
            with open(result.forecast_csv_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
            assert len(rows) == 4
        session.close()

    def test_idempotent_rerun_overwrites_csv(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                r1 = run_fx_daily_protocol_once(cfg, provider, session)
                session.commit()
                r2 = run_fx_daily_protocol_once(cfg, provider, session)

            assert r1.forecast_csv_path == r2.forecast_csv_path
        session.close()

    def test_result_includes_csv_paths(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            # forecast_csv_path must be set; outcome/evaluation remain None
            # because run_outcome_evaluation=False
            assert isinstance(result.forecast_csv_path, str)
        session.close()

    def test_no_csv_when_forecast_batch_id_is_none(self) -> None:
        """If forecast generation is disabled, no CSV should be written."""
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=False,  # no forecast → no batch id
                write_csv_exports=True,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)

            assert result.forecast_csv_path is None
        session.close()


# ---------------------------------------------------------------------------
# Manifest integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestAutomationManifestIntegration:
    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def _run_forecast_only(self, tmpdir: str):
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
            write_csv_exports=True,
            csv_output_dir=tmpdir,
        )
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)
        session.close()
        return result

    def test_manifest_path_returned(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_forecast_only(tmpdir)
            assert result.manifest_path is not None
            assert os.path.isfile(result.manifest_path)

    def test_manifest_json_in_latest_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_forecast_only(tmpdir)
            assert result.manifest_path == os.path.join(
                os.path.abspath(tmpdir), "latest", "manifest.json"
            )

    def test_manifest_has_required_keys(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_forecast_only(tmpdir)
            assert result.manifest_path is not None
            with open(result.manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            for key in (
                "as_of_jst", "generated_at_utc", "forecast_batch_id",
                "outcome_id", "evaluation_count", "forecast_csv_path",
                "outcome_csv_path", "evaluation_csv_path",
                "protocol_version", "theory_version", "engine_version", "schema_version",
            ):
                assert key in manifest, f"manifest missing key: {key}"

    def test_manifest_outcome_null_when_absent(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_forecast_only(tmpdir)
            assert result.manifest_path is not None
            with open(result.manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            assert manifest["outcome_csv_path"] is None
            assert manifest["evaluation_csv_path"] is None

    def test_manifest_path_none_when_csv_disabled(self) -> None:
        from unittest.mock import MagicMock

        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once
        from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider

        snap = _make_snapshot()
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        session = self._make_session()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = FxDailyAutomationConfig(
                run_outcome_evaluation=False,
                run_forecast_generation=True,
                write_csv_exports=False,
                csv_output_dir=tmpdir,
            )
            with patch(
                "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
                return_value=snap.as_of_jst,
            ), patch(
                "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
                return_value=True,
            ):
                result = run_fx_daily_protocol_once(cfg, provider, session)
            assert result.manifest_path is None
        session.close()

    def test_latest_forecast_csv_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_forecast_only(tmpdir)
            assert os.path.isfile(os.path.join(tmpdir, "latest", "forecast.csv"))

    def test_latest_outcome_absent_no_stale_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_forecast_only(tmpdir)
            assert not os.path.exists(os.path.join(tmpdir, "latest", "outcome.csv"))
