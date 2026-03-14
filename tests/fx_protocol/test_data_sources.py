from __future__ import annotations

from datetime import datetime

from ugh_quantamental.fx_protocol.data_sources import ProviderSnapshotDataSource


class _DummyProvider:
    def __init__(self, returned_as_of_jst: datetime) -> None:
        self.returned_as_of_jst = returned_as_of_jst

    def fetch_snapshot(self, *, as_of_jst: datetime) -> dict[str, object]:
        return {
            "as_of_jst": self.returned_as_of_jst,
            "price": 150.2,
            "request_passthrough": as_of_jst,
        }


def test_fetch_snapshot_keeps_requested_as_of_jst_as_canonical_anchor() -> None:
    requested = datetime(2026, 4, 2, 8, 0, 0)
    stale_metadata = datetime(2026, 4, 1, 8, 0, 0)
    source = ProviderSnapshotDataSource(provider=_DummyProvider(returned_as_of_jst=stale_metadata))

    snapshot = source.fetch_snapshot(requested)

    assert snapshot["as_of_jst"] == requested
    assert snapshot["provider_as_of_jst"] == stale_metadata
    assert snapshot["request_passthrough"] == requested
