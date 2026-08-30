"""Regression test for forecast-time input snapshot preservation."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from tests.fx_protocol.test_automation_csv_exports import _make_snapshot
from ugh_quantamental.fx_protocol.automation_models import FxDailyAutomationConfig
from ugh_quantamental.fx_protocol.data_sources import FxMarketDataProvider


def _make_session():
    from ugh_quantamental.persistence.db import (
        create_all_tables,
        create_db_engine,
        create_session_factory,
    )

    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    create_all_tables(engine)
    return create_session_factory(engine)()


def test_idempotent_retry_preserves_forecast_time_input_snapshot() -> None:
    from ugh_quantamental.fx_protocol.automation import run_fx_daily_protocol_once

    first_snapshot = _make_snapshot()
    retry_snapshot = first_snapshot.model_copy(update={"current_spot": 151.25})
    provider = MagicMock(spec=FxMarketDataProvider)
    provider.fetch_snapshot.side_effect = [first_snapshot, retry_snapshot]
    session = _make_session()

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = FxDailyAutomationConfig(
            run_outcome_evaluation=False,
            run_forecast_generation=True,
            write_csv_exports=True,
            csv_output_dir=tmpdir,
        )
        with patch(
            "ugh_quantamental.fx_protocol.automation.current_as_of_jst",
            return_value=first_snapshot.as_of_jst,
        ), patch(
            "ugh_quantamental.fx_protocol.automation.is_protocol_business_day",
            return_value=True,
        ):
            first = run_fx_daily_protocol_once(cfg, provider, session)
            session.commit()
            retry = run_fx_daily_protocol_once(cfg, provider, session)

        assert first.forecast_created is True
        assert retry.forecast_created is False
        assert first.forecast_batch_id == retry.forecast_batch_id
        assert first.forecast_batch_id is not None

        date_str = first_snapshot.as_of_jst.strftime("%Y%m%d")
        history_path = os.path.join(
            tmpdir, "history", date_str, first.forecast_batch_id, "input_snapshot.json"
        )
        latest_path = os.path.join(tmpdir, "latest", "input_snapshot.json")
        with open(history_path, encoding="utf-8") as fh:
            history_snapshot = json.load(fh)
        with open(latest_path, encoding="utf-8") as fh:
            latest_snapshot = json.load(fh)

        assert history_snapshot["current_spot"] == first_snapshot.current_spot
        assert latest_snapshot["current_spot"] == first_snapshot.current_spot
        assert history_snapshot["current_spot"] != retry_snapshot.current_spot

    session.close()
