"""Tests for minimal persistence DB and migration scaffolding."""

import importlib.util
from pathlib import Path

import pytest

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None
HAS_ALEMBIC = importlib.util.find_spec("alembic") is not None


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy not installed")
def test_create_all_tables_sqlite() -> None:
    from sqlalchemy import inspect

    from ugh_quantamental.persistence.db import create_all_tables, create_db_engine

    engine = create_db_engine()
    create_all_tables(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {"projection_runs", "state_runs"}.issubset(table_names)


@pytest.mark.skipif(not (HAS_SQLALCHEMY and HAS_ALEMBIC), reason="persistence deps not installed")
def test_alembic_upgrade_applies_initial_migration(tmp_path: Path) -> None:
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    from ugh_quantamental.persistence.db import create_db_engine

    db_path = tmp_path / "alembic.db"
    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(config, "head")

    engine = create_db_engine(f"sqlite:///{db_path}")
    table_names = set(inspect(engine).get_table_names())
    assert {"alembic_version", "projection_runs", "state_runs"}.issubset(table_names)
