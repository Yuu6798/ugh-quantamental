"""Run FX daily protocol workflow with schema migration bootstrap."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_target_db_url() -> str:
    """Resolve the SQLite URL used by the data branch daily job."""
    explicit_path = os.getenv("FX_SQLITE_PATH")
    if explicit_path:
        return f"sqlite:///{Path(explicit_path).expanduser().resolve()}"

    data_dir = Path(os.getenv("FX_DATA_DIR", "data")).expanduser().resolve()
    return f"sqlite:///{data_dir / 'fx_daily.sqlite3'}"


def run_migrations(db_url: str) -> None:
    """Apply Alembic migrations against the provided database URL."""
    from alembic import command
    from alembic.config import Config

    repo_root = Path(__file__).resolve().parents[1]
    config = Config(str(repo_root / "alembic.ini"))
    config.set_main_option("script_location", str(repo_root / "alembic"))
    config.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(config, "head")


def main() -> int:
    db_url = resolve_target_db_url()
    run_migrations(db_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
