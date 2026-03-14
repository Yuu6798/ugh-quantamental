import pytest

from ugh_quantamental.review_autofix.config import load_config


@pytest.mark.parametrize("token", ["1", "true", "TRUE", "yes", "on"])
def test_load_config_accepts_true_tokens_for_dry_run(monkeypatch, token: str) -> None:
    monkeypatch.setenv("DRY_RUN", token)
    config = load_config()
    assert config.dry_run is True


@pytest.mark.parametrize("token", ["0", "false", "FALSE", "no", "off"])
def test_load_config_accepts_false_tokens_for_dry_run(monkeypatch, token: str) -> None:
    monkeypatch.setenv("DRY_RUN", token)
    config = load_config()
    assert config.dry_run is False


def test_load_config_rejects_invalid_boolean_for_dry_run(monkeypatch) -> None:
    monkeypatch.setenv("DRY_RUN", "maybe")
    with pytest.raises(ValueError, match=r"invalid boolean env DRY_RUN"):
        load_config()
