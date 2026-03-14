"""Alembic environment for minimal persistence migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ugh_quantamental.persistence.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Allow the database URL to be overridden via:
#   1. -x sqlalchemy.url=... on the alembic CLI (takes highest precedence), or
#   2. SQLALCHEMY_URL environment variable.
# This is required by scripts/run_fx_daily_protocol.py so that Alembic
# migrates the data-branch SQLite file rather than alembic.ini's default.
_url_override = context.get_x_argument(as_dictionary=True).get("sqlalchemy.url") or os.environ.get(
    "SQLALCHEMY_URL"
)
if _url_override:
    config.set_main_option("sqlalchemy.url", _url_override)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
