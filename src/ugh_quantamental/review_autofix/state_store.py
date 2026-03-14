from __future__ import annotations

import json
from pathlib import Path


class StateStore:
    def seen(self, key: str) -> bool:
        raise NotImplementedError

    def mark(self, key: str) -> None:
        raise NotImplementedError


class FileStateStore(StateStore):
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")

    def _load(self) -> set[str]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {str(item) for item in raw}

    def seen(self, key: str) -> bool:
        return key in self._load()

    def mark(self, key: str) -> None:
        data = self._load()
        data.add(key)
        self._path.write_text(json.dumps(sorted(data)), encoding="utf-8")
