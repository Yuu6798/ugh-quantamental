"""Shared fixture for the script tests that read the execution archive (spec §8).

The archive under ``tmp_path`` is written with the real execution exporters
through the module-level helpers of
``tests/fx_protocol/test_execution_reporting.py``: two Mon-Fri weeks
(2026-03-02 .. 2026-03-13) of complete six-book live batches in which
``ugh_x1`` and ``bench_long`` go long every day and every window closes
+100 bp.  No network, no clock: ``generated_at_utc`` is pinned one hour after
the last window closed, and the activation marker is patched to the first day
so the calendar cohort is exactly these ten days (nothing blocks the gate).

``latest/execution_summary.json`` is pre-seeded with ``{"stale": true}`` so a
test can tell a refreshed summary from a leftover one.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from tests.fx_protocol.test_execution_reporting import (
    _activate,
    _after_close,
    _business_days,
    _trade,
    _write_day,
)
from ugh_quantamental.fx_protocol.execution_models import BookId

EXECUTION_ARCHIVE_FIRST_DAY = date(2026, 3, 2)  # Monday
EXECUTION_ARCHIVE_LAST_DAY = date(2026, 3, 13)  # Friday of the second week
EXECUTION_ARCHIVE_DAYS = tuple(
    _business_days(EXECUTION_ARCHIVE_FIRST_DAY, EXECUTION_ARCHIVE_LAST_DAY)
)


@pytest.fixture
def execution_archive(tmp_path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, datetime]:
    """``(csv_output_dir, generated_at_utc)`` of the ten-day archive with a stale latest summary."""
    root = str(tmp_path / "csv")
    _activate(monkeypatch, EXECUTION_ARCHIVE_FIRST_DAY)
    for day in EXECUTION_ARCHIVE_DAYS:
        _write_day(
            root,
            day,
            {BookId.ugh_x1: _trade(1), BookId.bench_long: _trade(1)},
            realized_close=101.0,
        )
    latest_dir = tmp_path / "csv" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "execution_summary.json").write_text('{"stale": true}\n', encoding="utf-8")
    return root, _after_close(EXECUTION_ARCHIVE_LAST_DAY)
