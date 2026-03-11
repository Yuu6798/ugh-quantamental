"""Minimal sync SQLAlchemy bootstrap helpers for persistence v1."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ugh_quantamental.persistence.models import Base


def create_db_engine(url: str = "sqlite+pysqlite:///:memory:", echo: bool = False) -> Engine:
    """Create a sync SQLAlchemy engine."""
    return create_engine(url, echo=echo, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def create_all_tables(engine: Engine) -> None:
    """Create all persistence tables from ORM metadata."""
    Base.metadata.create_all(bind=engine)
