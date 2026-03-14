"""Data-source adapters for FX protocol snapshots."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Protocol


class SnapshotProvider(Protocol):
    """Provider protocol used by the daily FX data source adapter."""

    def fetch_snapshot(self, *, as_of_jst: datetime) -> dict[str, Any]:
        ...


class ProviderSnapshotDataSource:
    """Adapter that anchors canonical snapshot day to the caller request."""

    def __init__(self, provider: SnapshotProvider) -> None:
        self._provider = provider

    def fetch_snapshot(self, as_of_jst: datetime) -> dict[str, Any]:
        """Fetch provider data while preserving requested canonical as_of_jst."""
        payload = deepcopy(self._provider.fetch_snapshot(as_of_jst=as_of_jst))
        provider_as_of_jst = payload.get("as_of_jst")

        payload["as_of_jst"] = as_of_jst
        if provider_as_of_jst is not None:
            payload["provider_as_of_jst"] = provider_as_of_jst

        return payload
