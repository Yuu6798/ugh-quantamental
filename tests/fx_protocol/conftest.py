"""Shared fixtures for ``tests/fx_protocol``.

The FX execution layer (automation Step 3b, ``docs/specs/fx_execution_layer_v1.md`` §6)
fetches a live USDJPY spot on every run that records decisions, and
``FxDailyAutomationConfig.run_execution_layer`` defaults to ``True``.  Tests never
touch the network, so the fetch is refused for every test in this package: the
automation then records ``entry_status = "live_unavailable"`` rows, exactly as a
real run would after a failed fetch.  A test that needs a quote replaces the same
attribute with its own stub (``monkeypatch.setattr`` on
``ugh_quantamental.fx_protocol.automation.fetch_live_spot_yahoo``), which wins
because autouse fixtures are set up first.
"""

from __future__ import annotations

import pytest

from ugh_quantamental.fx_protocol.data_sources import FxDataFetchError


def _refuse_live_spot(*args: object, **kwargs: object) -> tuple[float, object]:
    raise FxDataFetchError("live spot network access is disabled in tests")


@pytest.fixture(autouse=True)
def _no_live_spot_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse the execution layer's live-spot fetch so no test reaches the network."""
    monkeypatch.setattr(
        "ugh_quantamental.fx_protocol.automation.fetch_live_spot_yahoo", _refuse_live_spot
    )
