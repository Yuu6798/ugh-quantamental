"""Tests for automation_models.py, data_sources.py, and automation.py."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
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
from ugh_quantamental.fx_protocol.data_sources import (
    FxDataFetchError,
    FxMarketDataProvider,
    HttpJsonFxMarketDataProvider,
    _parse_snapshot,
)
from ugh_quantamental.fx_protocol.models import CurrencyPair, MarketDataProvenance

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

_JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _provenance_dict() -> dict:
    return {
        "vendor": "test",
        "feed_name": "feed",
        "price_type": "mid",
        "resolution": "1d",
        "timezone": "Asia/Tokyo",
        "retrieved_at_utc": "2026-03-10T00:00:00+00:00",
    }


def _build_windows_dicts(n: int = 20) -> list[dict]:
    """Build n consecutive window dicts."""
    wins = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        wins.append({
            "window_start_jst": start.isoformat(),
            "window_end_jst": end.isoformat(),
            "open_price": 149.5,
            "high_price": 151.5,
            "low_price": 148.5,
            "close_price": 150.5,
            "event_tags": [],
        })
        start = end
        count += 1
    return wins


def _snapshot_payload(n: int = 20, as_of_jst: str | None = None) -> dict:
    wins = _build_windows_dicts(n)
    # as_of_jst defaults to the end of the last window.
    if as_of_jst is None:
        as_of_jst = wins[-1]["window_end_jst"]
    return {
        "pair": "USDJPY",
        "as_of_jst": as_of_jst,
        "current_spot": 150.0,
        "completed_windows": wins,
        "market_data_provenance": _provenance_dict(),
    }


def _build_fxprotocol_snapshot(n: int = 20) -> FxProtocolMarketSnapshot:
    """Build a typed FxProtocolMarketSnapshot for automation tests."""
    from ugh_quantamental.fx_protocol.data_sources import _parse_snapshot as _ps

    payload = _snapshot_payload(n)
    as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
    # Override as_of_jst to match a real business day.
    payload["as_of_jst"] = as_of.isoformat()
    return _ps(payload, as_of)


# ---------------------------------------------------------------------------
# FxDailyAutomationConfig
# ---------------------------------------------------------------------------


class TestFxDailyAutomationConfig:
    def test_defaults(self) -> None:
        cfg = FxDailyAutomationConfig()
        assert cfg.pair == CurrencyPair.USDJPY
        assert cfg.theory_version == "v1"
        assert cfg.protocol_version == "v1"
        assert cfg.run_forecast_generation is True
        assert cfg.run_outcome_evaluation is True
        assert cfg.data_branch == "fx-daily-data"

    def test_custom_values(self) -> None:
        cfg = FxDailyAutomationConfig(
            theory_version="v2",
            engine_version="v3",
            run_outcome_evaluation=False,
        )
        assert cfg.theory_version == "v2"
        assert cfg.run_outcome_evaluation is False

    def test_frozen(self) -> None:
        cfg = FxDailyAutomationConfig()
        with pytest.raises(Exception):
            cfg.theory_version = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FxDailyAutomationResult
# ---------------------------------------------------------------------------


class TestFxDailyAutomationResult:
    def test_defaults(self) -> None:
        r = FxDailyAutomationResult(as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))
        assert r.forecast_created is False
        assert r.outcome_recorded is False
        assert r.evaluation_count == 0
        assert r.data_commit_created is False

    def test_with_values(self) -> None:
        r = FxDailyAutomationResult(
            as_of_jst=datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST),
            forecast_batch_id="fb_123",
            forecast_created=True,
            evaluation_count=4,
        )
        assert r.forecast_batch_id == "fb_123"
        assert r.forecast_created is True
        assert r.evaluation_count == 4


# ---------------------------------------------------------------------------
# HttpJsonFxMarketDataProvider (no real network; stub urllib)
# ---------------------------------------------------------------------------


class TestHttpJsonFxMarketDataProvider:
    def _make_provider(self, url: str = "http://example.com/fx") -> HttpJsonFxMarketDataProvider:
        return HttpJsonFxMarketDataProvider(url=url)

    def _mock_urlopen(self, payload: dict):
        """Return a context-manager mock for urllib.request.urlopen."""
        body = json.dumps(payload).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = body
        return mock_resp

    def test_successful_fetch(self) -> None:
        provider = self._make_provider()
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(20, as_of_jst=as_of.isoformat())
        mock_resp = self._mock_urlopen(payload)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            snap = provider.fetch_snapshot(as_of)

        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) == 20

    def test_missing_url_raises(self) -> None:
        provider = HttpJsonFxMarketDataProvider(url="")
        with pytest.raises(FxDataFetchError, match="FX_DATA_URL"):
            provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))

    def test_non_200_status_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 503
        mock_resp.read.return_value = b'{"error": "service unavailable"}'

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="503"):
                provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))

    def test_invalid_json_raises(self) -> None:
        provider = self._make_provider()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = b"NOT JSON"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(FxDataFetchError, match="JSON"):
                provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))

    def test_provider_satisfies_protocol(self) -> None:
        provider = self._make_provider()
        assert isinstance(provider, FxMarketDataProvider)

    def test_no_network_access_in_tests(self) -> None:
        """Ensure provider uses its URL without touching the network."""
        provider = HttpJsonFxMarketDataProvider(url="http://should-not-be-called.invalid/")
        # We patch urllib so no actual network call happens.
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("no network in tests"),
        ):
            with pytest.raises(FxDataFetchError, match="Network error"):
                provider.fetch_snapshot(datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST))


# ---------------------------------------------------------------------------
# _parse_snapshot helper
# ---------------------------------------------------------------------------


class TestParseSnapshot:
    def test_parses_valid_payload(self) -> None:
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(20, as_of_jst=as_of.isoformat())
        snap = _parse_snapshot(payload, as_of)
        assert snap.current_spot == 150.0
        assert snap.pair == CurrencyPair.USDJPY
        assert len(snap.completed_windows) == 20

    def test_missing_current_spot_raises(self) -> None:
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(20, as_of_jst=as_of.isoformat())
        del payload["current_spot"]
        with pytest.raises(FxDataFetchError, match="current_spot"):
            _parse_snapshot(payload, as_of)

    def test_fewer_than_20_windows_raises(self) -> None:
        as_of = datetime(2026, 3, 10, 8, 0, 0, tzinfo=_JST)
        payload = _snapshot_payload(19, as_of_jst=as_of.isoformat())
        with pytest.raises((FxDataFetchError, ValueError)):
            _parse_snapshot(payload, as_of)


# ---------------------------------------------------------------------------
# run_fx_daily_protocol_once (happy path + idempotency)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="SQLAlchemy not installed")
class TestRunFxDailyProtocolOnce:
    def _make_session(self):
        from ugh_quantamental.persistence.db import (
            create_all_tables,
            create_db_engine,
            create_session_factory,
        )

        engine = create_db_engine("sqlite+pysqlite:///:memory:")
        create_all_tables(engine)
        return create_session_factory(engine)()

    def _make_provider(self, snap: FxProtocolMarketSnapshot):
        """Build a stub provider that returns the given snapshot."""
        provider = MagicMock(spec=FxMarketDataProvider)
        provider.fetch_snapshot.return_value = snap
        return provider

    def _make_snapshot_no_previous_window(self) -> FxProtocolMarketSnapshot:
        """Snapshot where as_of_jst does NOT match newest window end (no outcome)."""
        wins = _build_windows_raw(20)
        # Force as_of to be 7 days after newest window end (no match).
        future_as_of = wins[-1].window_end_jst + timedelta(days=7)
        return FxProtocolMarketSnapshot(
            pair=CurrencyPair.USDJPY,
            as_of_jst=future_as_of,
            current_spot=150.0,
            completed_windows=wins,
            market_data_provenance=MarketDataProvenance(
                vendor="test",
                feed_name="feed",
                price_type="mid",
                resolution="1d",
                timezone="Asia/Tokyo",
                retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )

    def _make_snapshot_with_previous_window(self) -> FxProtocolMarketSnapshot:
        """Snapshot where as_of_jst matches newest window end (outcome eligible)."""
        wins = _build_windows_raw(20)
        as_of = wins[-1].window_end_jst  # matches newest window end
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
                retrieved_at_utc=datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc),
            ),
        )

    def test_forecast_only_no_previous_window(self) -> None:
        """Happy path: forecast created, no outcome (no prior window match)."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,  # disable outcome for simplicity
            run_forecast_generation=True,
        )

        # Patch current_as_of_jst to return the snapshot's as_of_jst.
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)

        assert result.forecast_batch_id is not None
        assert result.forecast_created is True
        assert result.outcome_recorded is False
        session.close()

    def test_idempotent_rerun_does_not_duplicate(self) -> None:
        """Second run with the same as_of_jst must not create new forecast records."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
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
            # Second run — same session, same as_of.
            r2 = run_fx_daily_protocol_once(cfg, provider, session)

        # Both runs return the same batch_id; only the first creates it.
        assert r1.forecast_batch_id == r2.forecast_batch_id
        assert r1.forecast_created is True
        assert r2.forecast_created is False
        session.close()

    def test_no_outcome_when_no_prior_window(self) -> None:
        """Outcome must not be run when previous_window_matches returns False."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=True,
            run_forecast_generation=True,
        )

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.previous_window_matches",
            return_value=False,
        ):
            result = run_fx_daily_protocol_once(cfg, provider, session)

        assert result.outcome_recorded is False
        assert result.outcome_id is None
        session.close()

    def test_non_business_day_raises(self) -> None:
        """Running on a non-business day must raise ValueError."""
        from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

        snap = self._make_snapshot_no_previous_window()
        provider = self._make_provider(snap)
        session = self._make_session()
        cfg = FxDailyAutomationConfig()

        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=snap.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=False,
        ):
            with pytest.raises(ValueError, match="business day"):
                run_fx_daily_protocol_once(cfg, provider, session)
        session.close()


# ---------------------------------------------------------------------------
# _build_windows_raw helper for test_automation
# ---------------------------------------------------------------------------


def _build_windows_raw(n: int) -> tuple[FxCompletedWindow, ...]:
    """Build n consecutive FxCompletedWindow objects (Mon→next-biz-day)."""
    windows: list[FxCompletedWindow] = []
    start = datetime(2026, 1, 5, 8, 0, 0, tzinfo=_JST)
    count = 0
    while count < n:
        end = start + timedelta(days=1)
        while end.isoweekday() in (6, 7):
            end += timedelta(days=1)
        end = end.replace(hour=8, minute=0, second=0, microsecond=0)
        windows.append(FxCompletedWindow(
            window_start_jst=start,
            window_end_jst=end,
            open_price=149.5,
            high_price=151.5,
            low_price=148.5,
            close_price=150.5,
        ))
        start = end
        count += 1
    return tuple(windows)
