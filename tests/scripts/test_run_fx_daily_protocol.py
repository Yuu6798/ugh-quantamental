from __future__ import annotations

from types import SimpleNamespace

import scripts.run_fx_daily_protocol as daily_script


def test_run_migrations_passes_target_db_url_to_alembic(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyConfig:
        def __init__(self, path: str) -> None:
            captured["config_path"] = path
            self.options: dict[str, str] = {}

        def set_main_option(self, key: str, value: str) -> None:
            self.options[key] = value

    def fake_upgrade(config, revision: str) -> None:
        captured["upgrade_revision"] = revision
        captured["sqlalchemy_url"] = config.options["sqlalchemy.url"]

    monkeypatch.setattr(daily_script, "run_migrations", daily_script.run_migrations)
    monkeypatch.setitem(__import__("sys").modules, "alembic", SimpleNamespace(command=SimpleNamespace(upgrade=fake_upgrade)))
    monkeypatch.setitem(__import__("sys").modules, "alembic.command", SimpleNamespace(upgrade=fake_upgrade))
    monkeypatch.setitem(__import__("sys").modules, "alembic.config", SimpleNamespace(Config=DummyConfig))

    db_url = "sqlite:////tmp/data-branch.sqlite3"
    daily_script.run_migrations(db_url)

    assert captured["upgrade_revision"] == "head"
    assert captured["sqlalchemy_url"] == db_url
