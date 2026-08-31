"""Regression tests for e_star replay snapshot discovery across history batches."""

from __future__ import annotations

import importlib.util
import pathlib
import sys

_SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "analyze_estar_lag.py"
)
_spec = importlib.util.spec_from_file_location("analyze_estar_lag_snapshot_lookup", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
analyze_estar_lag = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = analyze_estar_lag
_spec.loader.exec_module(analyze_estar_lag)


def test_find_snapshot_searches_all_batch_dirs_when_catchup_dir_sorts_first(
    tmp_path: pathlib.Path,
) -> None:
    day = analyze_estar_lag.date(2026, 8, 31)
    date_dir = tmp_path / "history" / "20260831"

    # A recovered prior batch can sort before the day's own batch and has no
    # input snapshot.  The replay must keep searching rather than returning
    # None from the first directory.
    (date_dir / "forecast_20260827_recovered").mkdir(parents=True)
    own_batch = date_dir / "forecast_20260831_current"
    own_batch.mkdir()
    snapshot = own_batch / "input_snapshot.json"
    snapshot.write_text("{}", encoding="utf-8")

    found = analyze_estar_lag.find_snapshot_path(str(tmp_path), day)

    assert found == str(snapshot)
